#!/usr/bin/env python3
"""Liquidity science — quantifying the six questions with data.
 1 Which side gets swept first?           (by overnight direction)
 2 Which liquidity almost never revisits? (multi-horizon revisit rates, 10y daily)
 3 How long after NY open do sweeps come? (hour-of-day histogram)
 4 Under which volatility regime?         (sweep behavior by ATR tercile)
 5 Continuation or exhaustion?            (post-sweep drift, look-ahead-free)
 6 Does time-of-day change probabilities? (early vs late sweeps)
"""
import csv, os, statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ED = os.path.dirname(HERE)
NY = ZoneInfo("America/New_York")

# ---------- daily features (2y, session-resolved) ----------
rows = []
with open(os.path.join(ED, "features.csv")) as f:
    for r in csv.DictReader(f):
        rows.append(r)
rows = rows[5:]
for r in rows:
    for k in ("preNY_net", "atr5", "post_sweep_net", "ny_net", "prev_range"):
        r[k] = float(r[k])

swept = [r for r in rows if r["first_sweep"] in ("high", "low")]
print(f"=== Q1 WHICH SIDE FIRST (N={len(rows)} days, {len(swept)} with a sweep) ===")
c = Counter(r["first_sweep"] for r in rows)
for k in ("high", "low", "both_same_hour", "none"):
    print(f"  first sweep {k:15s}: {c.get(k,0):4d}  ({100*c.get(k,0)/len(rows):.0f}%)")
for ond, nm in [(1, "overnight UP"), (-1, "overnight DOWN")]:
    sub = [r for r in rows if (r["preNY_net"] > 0) == (ond > 0)]
    cc = Counter(r["first_sweep"] for r in sub)
    n = len(sub)
    print(f"  given {nm:14s}: P(high first)={cc.get('high',0)/n:.2f}  P(low first)={cc.get('low',0)/n:.2f}  P(none)={cc.get('none',0)/n:.2f}")

# ---------- Q4/Q5: by volatility regime ----------
print("\n=== Q4+Q5 SWEEP -> CONTINUATION OR EXHAUSTION, BY VOL REGIME ===")
a_sorted = sorted(r["atr5"] for r in rows)
t1, t2 = a_sorted[len(rows)//3], a_sorted[2*len(rows)//3]
for lo, hi, nm in [(0, t1, "LOW vol"), (t1, t2, "MID vol"), (t2, 1e9, "HIGH vol")]:
    sub = [r for r in swept if lo <= r["atr5"] < hi]
    if not sub:
        continue
    cont = [r for r in sub if (r["post_sweep_net"] > 0) == (r["first_sweep"] == "high")]
    both = [r for r in rows if lo <= r["atr5"] < hi and r["first_sweep"] in ("high", "low")]
    other = [r for r in both if (r["first_sweep"] == "high" and float(r["took_prev_low"]) > 0)
             or (r["first_sweep"] == "low" and float(r["took_prev_high"]) > 0)]
    ps = [abs(r["post_sweep_net"]) for r in sub]
    print(f"  {nm:8s} (N={len(sub):3d}): P(post-sweep continues)={len(cont)/len(sub):.2f}   "
          f"P(other side also swept)={len(other)/len(both):.2f}   E|post-sweep drift|=${statistics.mean(ps):.1f}")

# ---------- Q3/Q6: sweep timing from hourly bars ----------
print("\n=== Q3+Q6 WHEN DO SWEEPS HAPPEN (NY clock) ===")
bars = []
with open(os.path.join(ED, "h1.csv")) as f:
    next(f)
    for r in csv.reader(f):
        t = int(r[0])
        bars.append((datetime.fromtimestamp(t, tz=NY), float(r[1]), float(r[2]), float(r[3]), float(r[4])))
by_day = defaultdict(list)
for b in bars:
    by_day[b[0].date()].append(b)
days_sorted = sorted(by_day)
sweep_hours = Counter()
early_cont, late_cont = [], []
prev_ext = None
for d in days_sorted:
    ny = [b for b in by_day[d] if 9 <= b[0].hour < 16]
    if len(ny) < 5:
        prev_ext = None if not ny else (max(b[2] for b in ny), min(b[3] for b in ny), ny[-1][4])
        continue
    if prev_ext:
        ph, pl, _ = prev_ext
        for b in ny:
            side = "high" if b[2] > ph else ("low" if b[3] < pl else None)
            if side:
                sweep_hours[b[0].hour] += 1
                drift = ny[-1][4] - b[4]
                contv = drift if side == "high" else -drift
                (early_cont if b[0].hour <= 11 else late_cont).append(contv)
                break
    prev_ext = (max(b[2] for b in ny), min(b[3] for b in ny), ny[-1][4])
tot = sum(sweep_hours.values())
for h in range(9, 16):
    n = sweep_hours.get(h, 0)
    print(f"  {h:02d}:00-{h+1:02d}:00 NY: {n:4d} sweeps ({100*n/tot:.0f}%)" + ("  <- opening 2h" if h <= 10 else ""))
print(f"\n  Post-sweep continuation drift (to close): early sweeps (9-12): "
      f"${statistics.mean(early_cont):+.2f} (N={len(early_cont)})   late (12-16): ${statistics.mean(late_cont):+.2f} (N={len(late_cont)})")

# ---------- Q2: revisit horizons on 10y daily ----------
print("\n=== Q2 WHICH LIQUIDITY NEVER GETS REVISITED (10y daily, N=2512) ===")
d1 = []
with open(os.path.join(ED, "d1.csv")) as f:
    next(f)
    for r in csv.reader(f):
        d1.append((int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4])))
for horizon in (1, 5, 20):
    hi_re, lo_re, n = 0, 0, 0
    for i in range(1, len(d1) - horizon):
        ph, pl = d1[i-1][2], d1[i-1][3]
        seg = d1[i:i+horizon]
        if max(s[2] for s in seg) >= ph:
            hi_re += 1
        if min(s[3] for s in seg) <= pl:
            lo_re += 1
        n += 1
    print(f"  prev-day HIGH revisited within {horizon:2d}d: {100*hi_re/n:.0f}%   LOW: {100*lo_re/n:.0f}%")
# weekly extremes
wk = defaultdict(lambda: [0, 1e9, -1e9])
for t, o, h, l, c_ in d1:
    iso = datetime.fromtimestamp(t, tz=timezone.utc).isocalendar()
    key = (iso[0], iso[1])
    wk[key][1] = min(wk[key][1], l)
    wk[key][2] = max(wk[key][2], h)
keys = sorted(wk)
hi_re = lo_re = n = 0
for i in range(1, len(keys) - 4):
    ph, pl = wk[keys[i-1]][2], wk[keys[i-1]][1]
    nxt = keys[i:i+4]
    if max(wk[k][2] for k in nxt) >= ph: hi_re += 1
    if min(wk[k][1] for k in nxt) <= pl: lo_re += 1
    n += 1
print(f"  prev-WEEK high revisited within 4wk: {100*hi_re/n:.0f}%   low: {100*lo_re/n:.0f}%")
