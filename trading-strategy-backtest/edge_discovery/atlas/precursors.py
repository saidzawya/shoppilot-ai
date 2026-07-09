#!/usr/bin/env python3
"""Precursor mining: what consistently happens BEFORE big / trend / failed
days? No hypotheses — rank ALL yesterday+overnight features by mutual
information with tomorrow's outcome, with split-half stability. This is
exploratory ranking (flagged as such), not significance testing.
Outcomes (day t, defined ex-ante):
  BIG    : NY range in top decile
  TREND  : NY efficiency |net|/range > 0.55 AND range above median
  FAILED : first-hour move >0.3*atr5 that reverses (rest_net opposite, day
           closes against the first hour)
Predictors: everything knowable BEFORE 09:30 of day t.
"""
import csv, math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ED = os.path.dirname(HERE)

rows = []
with open(os.path.join(ED, "features.csv")) as f:
    for r in csv.DictReader(f):
        rows.append({k: (v if k in ("date", "first_sweep") else float(v)) for k, v in r.items()})
rows = rows[5:]

# outcomes
rng = np.array([r["ny_range"] for r in rows])
net = np.array([r["ny_net"] for r in rows])
fh = np.array([r["fh_net"] for r in rows])
rest = np.array([r["rest_net"] for r in rows])
atr = np.array([r["atr5"] for r in rows])
eff = np.abs(net) / np.maximum(rng, 1e-9)
BIG = (rng >= np.quantile(rng, 0.9)).astype(int)
TREND = ((eff > 0.55) & (rng > np.median(rng))).astype(int)
FAILED = ((np.abs(fh) > 0.3 * atr) & (fh * rest < 0) & (fh * net < 0)).astype(int)

PRED = ["asia_range", "asia_net", "london_range", "london_net", "preNY_range",
        "preNY_net", "preNY_vol", "gap_open", "prev_net", "prev_range", "atr5", "dow"]
X = {p: np.array([r[p] for r in rows]) for p in PRED}

def mi(x, y, bins=3):
    # tercile-bin x; y binary
    q = np.quantile(x, [1/3, 2/3])
    xb = np.digitize(x, q)
    m = 0.0
    n = len(x)
    for xv in range(bins):
        for yv in (0, 1):
            pxy = ((xb == xv) & (y == yv)).sum() / n
            px = (xb == xv).sum() / n
            py = (y == yv).sum() / n
            if pxy > 0:
                m += pxy * math.log2(pxy / (px * py))
    return m

half = len(rows) // 2
print(f"N={len(rows)} days | base rates: BIG={BIG.mean():.2f} TREND={TREND.mean():.2f} FAILED={FAILED.mean():.2f}\n")
for out_name, Y in [("BIG-RANGE day", BIG), ("TREND day", TREND), ("FAILED-MOVE day", FAILED)]:
    scores = []
    for p in PRED:
        m_all = mi(X[p], Y)
        m1 = mi(X[p][:half], Y[:half])
        m2 = mi(X[p][half:], Y[half:])
        stable = (m1 > 0.005) and (m2 > 0.005)
        scores.append((m_all, p, m1, m2, stable))
    scores.sort(reverse=True)
    print(f"== Precursors of {out_name} (MI bits; stability = MI>0.005 in both halves) ==")
    for m_all, p, m1, m2, stable in scores[:5]:
        # direction: rate in top vs bottom tercile
        q = np.quantile(X[p], [1/3, 2/3])
        top = Y[X[p] >= q[1]].mean(); bot = Y[X[p] <= q[0]].mean()
        print(f"  {p:13s} MI={m_all:.4f}  halves=({m1:.4f},{m2:.4f}) {'STABLE' if stable else 'unstable'}"
              f"   P(outcome|top33%)={top:.2f} vs P(|bottom33%)={bot:.2f}")
    print()
