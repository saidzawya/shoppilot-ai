#!/usr/bin/env python3
"""Bridge your broker's MT5 export into this engine.

In MT5: View > Symbols > XAUUSD > Bars -> request M1 for the full history,
then right-click -> Export (or use the included MQL5 one-liner in README).
The export is CSV like:
    2019.01.02 01:00:00,1282.31,1282.55,1282.11,1282.40,532,15,25
    (date time, open, high, low, close, tickvol, vol, spread)

Usage:
    python3 mt5_ingest.py XAUUSD_M1.csv [broker_utc_offset_hours]

Writes:
  h1.csv        - hourly bars resampled from M1 (drives features.py etc.)
  m1_full.csv   - normalized 1m bars (drives the MT5-only features:
                  5m box, retests, MFE/MAE, spread-at-entry, tick volume)
Then simply rerun:  features.py -> discover.py -> regimes.py
"""
import csv, sys
from datetime import datetime, timezone, timedelta

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    off = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0  # broker-server -> UTC
    tz = timezone(timedelta(hours=off))
    m1 = {}
    with open(src) as f:
        for line in f:
            p = line.strip().replace("\t", ",").split(",")
            if len(p) < 5 or not p[0][:2].isdigit():
                continue
            try:
                dt = datetime.strptime(p[0][:19].replace(".", "-"), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                dt = datetime.strptime(p[0][:16].replace(".", "-"), "%Y-%m-%d %H:%M")
            t = int(dt.replace(tzinfo=tz).timestamp())
            o, h, l, c = map(float, p[1:5])
            tv = int(float(p[5])) if len(p) > 5 else 0
            sp = int(float(p[7])) if len(p) > 7 else 0
            m1[t] = (o, h, l, c, tv, sp)
    with open("m1_full.csv", "w") as f:
        f.write("epoch,open,high,low,close,tickvol,spread\n")
        for t in sorted(m1):
            o, h, l, c, tv, sp = m1[t]
            f.write(f"{t},{o},{h},{l},{c},{tv},{sp}\n")
    # resample to H1
    h1 = {}
    for t in sorted(m1):
        k = t - (t % 3600)
        o, h, l, c, tv, sp = m1[t]
        if k not in h1:
            h1[k] = [o, h, l, c, tv]
        else:
            b = h1[k]
            b[1] = max(b[1], h); b[2] = min(b[2], l); b[3] = c; b[4] += tv
    with open("h1.csv", "w") as f:
        f.write("epoch,open,high,low,close,volume\n")
        for k in sorted(h1):
            o, h, l, c, v = h1[k]
            f.write(f"{k},{round(o,2)},{round(h,2)},{round(l,2)},{round(c,2)},{v}\n")
    print(f"m1_full.csv: {len(m1)} bars   h1.csv: {len(h1)} bars")
    print("Now rerun: features.py -> discover.py -> regimes.py")

if __name__ == "__main__":
    main()
