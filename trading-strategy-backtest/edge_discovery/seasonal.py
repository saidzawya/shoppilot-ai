#!/usr/bin/env python3
"""Seasonality on 10 years of daily bars (N~2500): day-of-week and month
effects on daily net change, with bootstrap CIs and BH-FDR across all 17
tests. Long-horizon complement to the 2y session study."""
import csv, os, random, statistics
from datetime import datetime, timezone

random.seed(11)
HERE = os.path.dirname(__file__)

rows = []
with open(os.path.join(HERE, "d1.csv")) as f:
    next(f)
    for r in csv.reader(f):
        t = int(r[0])
        d = datetime.fromtimestamp(t, tz=timezone.utc)
        o, c = float(r[1]), float(r[4])
        rows.append({"dow": d.weekday(), "month": d.month, "net": c - o,
                     "up": 1.0 if c > o else 0.0})

base_up = statistics.mean(r["up"] for r in rows)
print(f"N={len(rows)} days over 10y   base P(up)={base_up:.3f}")

def boot_ci(vals, iters=4000):
    n = len(vals)
    ms = sorted(statistics.mean(random.choice(vals) for _ in range(n)) for _ in range(iters))
    mean = statistics.mean(vals)
    p = 2 * min(sum(1 for m in ms if m <= 0)/iters, sum(1 for m in ms if m >= 0)/iters)
    return mean, ms[int(0.025*iters)], ms[int(0.975*iters)], max(p, 1/iters)

tests = []
for dow, nm in [(0,"Mon"),(1,"Tue"),(2,"Wed"),(3,"Thu"),(4,"Fri")]:
    sel = [r["net"] for r in rows if r["dow"] == dow]
    m, lo, hi, p = boot_ci(sel)
    tests.append((f"DOW {nm}", len(sel), m, lo, hi, p))
for mo in range(1, 13):
    sel = [r["net"] for r in rows if r["month"] == mo]
    m, lo, hi, p = boot_ci(sel)
    tests.append((f"Month {mo:02d}", len(sel), m, lo, hi, p))

# BH-FDR
idx = sorted(range(len(tests)), key=lambda i: tests[i][5])
mtot = len(tests); passed = set(); mk = 0
for k, i in enumerate(idx, 1):
    if tests[i][5] <= 0.10 * k / mtot: mk = k
for k, i in enumerate(idx, 1):
    if k <= mk: passed.add(i)

print(f"\n{'test':10s} {'N':>5s} {'mean$':>8s} {'95% CI':>18s} {'p':>7s}  FDR")
for i, (nm, n, m, lo, hi, p) in enumerate(tests):
    print(f"{nm:10s} {n:5d} {m:+8.2f} [{lo:+7.2f},{hi:+7.2f}] {p:7.4f}  {'PASS' if i in passed else '-'}")
