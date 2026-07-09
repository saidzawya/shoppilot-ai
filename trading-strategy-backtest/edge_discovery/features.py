#!/usr/bin/env python3
"""Per-trading-day feature table from hourly gold bars (h1.csv).

Sessions are anchored on the America/New_York clock (DST-safe):
  Asia   : 19:00 (prev day) -> 03:00 NY
  London : 03:00 -> 09:00 NY   (approximates the London morning)
  NY     : 09:00 -> 16:00 NY   (hourly grid; the 09:00 bar contains the
                                09:30 open -- documented approximation)
Features marked in FEATURES_REQUIRING_MT5 cannot be computed at hourly
resolution and await the broker's 1m export.
"""
import csv, os, statistics
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
HERE = os.path.dirname(__file__)

FEATURES_REQUIRING_MT5 = [
    "us_open_5m_box_size", "n_box_retests", "distance_before_retest",
    "MFE/MAE at 1m", "tick_volume", "spread_at_entry", "time_to_first_breakout(1m)",
]

def load_h1():
    bars = []
    with open(os.path.join(HERE, "h1.csv")) as f:
        next(f)
        for r in csv.reader(f):
            t = int(r[0])
            dt = datetime.fromtimestamp(t, tz=NY)
            bars.append((dt, float(r[1]), float(r[2]), float(r[3]), float(r[4]), int(r[5])))
    bars.sort()
    return bars

def agg(bs):
    """OHLC aggregate of a bar list; None if empty."""
    if not bs:
        return None
    return {"o": bs[0][1], "h": max(b[2] for b in bs), "l": min(b[3] for b in bs),
            "c": bs[-1][4], "vol": sum(b[5] for b in bs), "n": len(bs)}

def hour_ret_std(bs):
    rets = [(b[4] - b[1]) for b in bs]
    return statistics.pstdev(rets) if len(rets) > 1 else 0.0

def build():
    bars = load_h1()
    # bucket bars by NY trading day: a bar belongs to day D if its NY time is
    # within [D-1 19:00, D 16:00]. We iterate calendar days present.
    by_day = {}
    for b in bars:
        d = b[0].date()
        by_day.setdefault(d, []).append(b)

    days = sorted(by_day)
    rows = []
    prev = None  # previous day's NY session aggregate
    prev_date = None
    atr_hist = []
    for d in days:
        if d.weekday() >= 5:
            continue
        day_bars = by_day.get(d, [])
        prev_cal = d - timedelta(days=1)
        # sessions (NY clock)
        asia = [b for b in by_day.get(prev_cal, []) if b[0].hour >= 19] + \
               [b for b in day_bars if b[0].hour < 3]
        london = [b for b in day_bars if 3 <= b[0].hour < 9]
        ny = [b for b in day_bars if 9 <= b[0].hour < 16]
        A, L, N = agg(asia), agg(london), agg(ny)
        if not (A and L and N) or N["n"] < 5:
            prev = N or prev
            prev_date = d
            continue
        pre = agg(asia + london)
        first_hour = agg([b for b in ny if b[0].hour == 9])
        rest = agg([b for b in ny if b[0].hour >= 10])
        row = {
            "date": str(d), "dow": d.weekday(), "month": d.month,
            "asia_range": round(A["h"] - A["l"], 2), "asia_net": round(A["c"] - A["o"], 2),
            "london_range": round(L["h"] - L["l"], 2), "london_net": round(L["c"] - L["o"], 2),
            "preNY_range": round(pre["h"] - pre["l"], 2), "preNY_net": round(pre["c"] - pre["o"], 2),
            "preNY_vol": round(hour_ret_std(asia + london), 3),
            "ny_open": N["o"], "ny_close": N["c"],
            "ny_net": round(N["c"] - N["o"], 2), "ny_range": round(N["h"] - N["l"], 2),
            "ny_close_pos": round((N["c"] - N["l"]) / (N["h"] - N["l"]), 3) if N["h"] > N["l"] else 0.5,
            "fh_net": round((first_hour["c"] - first_hour["o"]), 2) if first_hour else 0.0,
            "rest_net": round((rest["c"] - rest["o"]), 2) if rest else 0.0,
            "vol_ny": N["vol"],
        }
        if prev:
            row["gap_open"] = round(N["o"] - prev["c"], 2)
            row["prev_net"] = round(prev["c"] - prev["o"], 2)
            row["prev_range"] = round(prev["h"] - prev["l"], 2)
            # liquidity sweeps of the previous NY session extremes
            ph, pl = prev["h"], prev["l"]
            took_hi = N["h"] > ph
            took_lo = N["l"] < pl
            first_side = "none"
            sweep_bar = None
            for b in ny:
                hit_h = b[2] > ph
                hit_l = b[3] < pl
                if hit_h and hit_l:
                    first_side = "both_same_hour"; sweep_bar = b; break
                if hit_h:
                    first_side = "high"; sweep_bar = b; break
                if hit_l:
                    first_side = "low"; sweep_bar = b; break
            # look-ahead-free outcome: return from the CLOSE of the sweep
            # hour to the session close (what a trader entering on the sweep
            # confirmation could actually capture)
            post_sweep = round(N["c"] - sweep_bar[4], 2) if sweep_bar else 0.0
            row.update(took_prev_high=int(took_hi), took_prev_low=int(took_lo),
                       both_swept=int(took_hi and took_lo), first_sweep=first_side,
                       post_sweep_net=post_sweep)
        else:
            row.update(gap_open=0.0, prev_net=0.0, prev_range=0.0,
                       took_prev_high=0, took_prev_low=0, both_swept=0,
                       first_sweep="none", post_sweep_net=0.0)
        # ATR(5) of NY-session ranges
        row["atr5"] = round(sum(atr_hist[-5:]) / len(atr_hist[-5:]), 2) if atr_hist else row["ny_range"]
        atr_hist.append(row["ny_range"])
        rows.append(row)
        prev = N
        prev_date = d

    with open(os.path.join(HERE, "features.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"features.csv: {len(rows)} trading days x {len(rows[0])} features")
    print("MT5-only features (awaiting broker 1m export):", ", ".join(FEATURES_REQUIRING_MT5))
    return rows

if __name__ == "__main__":
    build()
