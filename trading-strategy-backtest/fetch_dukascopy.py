#!/usr/bin/env python3
"""LOCAL-RUN KIT — download real multi-year 1-minute gold data from Dukascopy
and write CSVs in this project's schema (data/1m_<YYYY-MM-DD>.csv), so the
exact same engine (research.py / backtest.py / stats.py) can be run on 3-5
years of history on an unconstrained machine.

WHY THIS EXISTS: in the cloud research environment the price feed is capped
at 30 days of 1-minute data (Yahoo), and Dukascopy/OANDA/broker feeds are
proxy-blocked. So the largest in-environment study is ~39 trading days.
Run THIS on your own computer (no proxy) to extend to years.

USAGE:
    pip install requests
    python3 fetch_dukascopy.py 2021-01-01 2025-12-31 XAUUSD
Then:
    python3 research.py         # or backtest.py for the 1m rules
    python3 stats.py out/trades_base_5m.csv

Dukascopy serves one LZMA-compressed .bi5 tick file per hour at:
  https://datafeed.dukascopy.com/datafeed/{SYM}/{YYYY}/{MM0:02d}/{DD:02d}/{HH:02d}h_ticks.bi5
where MM0 is the MONTH MINUS ONE (Dukascopy months are 0-indexed).
Each tick = 20 bytes big-endian:
  uint32 ms-since-hour, uint32 ask(points), uint32 bid(points),
  float32 askVol, float32 bidVol.  For XAUUSD, price = points / 1000.
This script resamples ticks -> 1-minute OHLC (mid price) and writes RTH+full
day CSVs. It is deliberately dependency-light (requests + stdlib lzma).
"""
import lzma, os, struct, sys
from datetime import datetime, timedelta, timezone

try:
    import requests
except ImportError:
    sys.exit("pip install requests")

POINT = {"XAUUSD": 1000.0, "EURUSD": 100000.0}  # points-per-unit divisor

def fetch_hour(sym, dt):
    url = (f"https://datafeed.dukascopy.com/datafeed/{sym}/{dt.year}/"
           f"{dt.month-1:02d}/{dt.day:02d}/{dt.hour:02d}h_ticks.bi5")
    r = requests.get(url, timeout=30, headers={"User-Agent": "research"})
    if r.status_code != 200 or not r.content:
        return []
    try:
        raw = lzma.decompress(r.content)
    except lzma.LZMAError:
        return []
    div = POINT.get(sym, 1000.0)
    ticks = []
    for i in range(0, len(raw), 20):
        ms, ask, bid, _, _ = struct.unpack(">IIIff", raw[i:i+20])
        mid = (ask + bid) / 2.0 / div
        ticks.append((dt.timestamp() + ms / 1000.0, mid))
    return ticks

def resample_1m(ticks):
    bars = {}
    for t, px in ticks:
        k = int(t) - (int(t) % 60)
        if k not in bars:
            bars[k] = [px, px, px, px]
        else:
            b = bars[k]; b[1] = max(b[1], px); b[2] = min(b[2], px); b[3] = px
    return bars

def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    d0 = datetime.strptime(sys.argv[1], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    d1 = datetime.strptime(sys.argv[2], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    sym = sys.argv[3] if len(sys.argv) > 3 else "XAUUSD"
    os.makedirs("data", exist_ok=True)
    day = d0
    while day <= d1:
        if day.weekday() >= 5:  # skip weekends (market closed)
            day += timedelta(days=1); continue
        ticks = []
        for h in range(24):
            ticks += fetch_hour(sym, day.replace(hour=h))
        if len(ticks) < 100:
            print(f"{day.date()}: no data (holiday?)"); day += timedelta(days=1); continue
        bars = resample_1m(ticks)
        path = f"data/1m_{day.date()}.csv"
        with open(path, "w") as f:
            f.write("epoch,open,high,low,close\n")
            for k in sorted(bars):
                o, h, l, c = bars[k]
                f.write(f"{k},{o:.2f},{h:.2f},{l:.2f},{c:.2f}\n")
        print(f"{day.date()}: {len(bars)} 1m bars -> {path}")
        day += timedelta(days=1)

if __name__ == "__main__":
    main()
