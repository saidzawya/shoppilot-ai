#!/usr/bin/env python3
"""Full falsification battery: execution realism, independent filters,
walk-forward, and Monte Carlo. Imports the research engine so every number
is reproducible from data/ + context.json. Writes out/analysis.json.
"""
import json, math, random, statistics
import research as R
import stats as S

random.seed(7)

def summ(trades):
    Rs = [t["R"] for t in trades]
    if not Rs:
        return {"n": 0, "sumR": 0.0, "expR": 0.0, "win": 0.0, "pf": 0.0}
    wins = [r for r in Rs if r > 0]; losses = [-r for r in Rs if r <= 0]
    pf = sum(wins) / sum(losses) if losses and sum(losses) > 0 else float("inf")
    return {"n": len(Rs), "sumR": round(sum(Rs), 2),
            "expR": round(sum(Rs) / len(Rs), 3),
            "win": round(100 * len(wins) / len(Rs)), "pf": round(pf, 2)}

out = {}

# ---------- 1. Execution realism grid (base = liquidity target) ----------
print("="*64, "\n1. EXECUTION REALISM  (base strategy, liquidity target)\n", "="*64)
grid = []
for cost, slip, delay in [(0,0,False),(0.15,0,False),(0.30,0,False),(0.50,0,False),
                          (0.30,0.20,False),(0.30,0.20,True),(0.50,0.30,True)]:
    t = R.run(cost=cost, slip=slip, delay=delay)
    s = summ(t)
    lbl = f"cost={cost} slip={slip} delay={delay}"
    grid.append({"cfg": lbl, **s})
    print(f"  {lbl:34s} N={s['n']} win%={s['win']} PF={s['pf']} sumR={s['sumR']:+.2f} expR={s['expR']:+.3f}")
out["execution_grid"] = grid

# ---------- 2. Independent enhancement filters (never combined) ----------
print("\n"+"="*64, "\n2. FILTERS — each applied ALONE (base = no filter)\n", "="*64)
filters = {
    "base (no filter)":        dict(),
    "overnight-trend (with)":  dict(filt="onight_trend"),
    "overnight-counter (fade)":dict(filt="onight_counter"),
    "min box >= 8":            dict(filt=("min_box", 8.0)),
    "min box >= 12":           dict(filt=("min_box", 12.0)),
    "ATR/onight-range >= 60":  dict(filt=("atr", 60.0)),
    "breakout cutoff 30min":   dict(breakout_cutoff_min=30),
    "breakout cutoff 60min":   dict(breakout_cutoff_min=60),
    "break-even @ +1R":        dict(be_R=1.0),
    "trailing stop @ +1R":     dict(trail_R=1.0),
    "partial TP half @ +1R":   dict(partial_R=1.0),
}
frows = []
for name, kw in filters.items():
    t = R.run(**kw)
    s = summ(t)
    frows.append({"filter": name, **s})
    print(f"  {name:26s} N={s['n']:2d} win%={s['win']:2d} PF={s['pf']:4} sumR={s['sumR']:+6.2f} expR={s['expR']:+.3f}")
out["filters"] = frows

# ---------- 3. Fixed RR targets (sensitivity of the exit choice) ----------
print("\n"+"="*64, "\n3. FIXED RR TARGETS\n", "="*64)
rr_rows = []
for rr in (1, 2, 3):
    t = R.run(tp_mode="rr", rr=rr)
    s = summ(t); rr_rows.append({"rr": rr, **s})
    print(f"  RR 1:{rr}   N={s['n']} win%={s['win']} PF={s['pf']} sumR={s['sumR']:+.2f} expR={s['expR']:+.3f}")
out["rr_targets"] = rr_rows

# ---------- 4. Walk-forward (temporal split, no re-fit — pure OOS) ----------
print("\n"+"="*64, "\n4. WALK-FORWARD (temporal, out-of-sample)\n", "="*64)
base = R.run()
base.sort(key=lambda x: x["date"])
half = len(base) // 2
seg = {"first-half": base[:half], "second-half": base[half:]}
# rolling 3 windows
n = len(base); w = n // 3
seg["window-1"] = base[:w]; seg["window-2"] = base[w:2*w]; seg["window-3"] = base[2*w:]
wf = {}
for k, t in seg.items():
    s = summ(t); wf[k] = s
    d0 = t[0]["date"] if t else "-"; d1 = t[-1]["date"] if t else "-"
    print(f"  {k:12s} {d0}..{d1}  N={s['n']} win%={s['win']} PF={s['pf']} expR={s['expR']:+.3f} sumR={s['sumR']:+.2f}")
out["walk_forward"] = wf

# ---------- 5. Monte Carlo on the R-sequence ----------
print("\n"+"="*64, "\n5. MONTE CARLO  (bootstrap of R-sequence, 10k runs)\n", "="*64)
Rs = [t["R"] for t in base]
def mc(risk_frac, horizon=100, iters=10000, ruin=0.5):
    ruins = 0; finals = []; maxdd = []
    for _ in range(iters):
        eq = 1.0; peak = 1.0; dd = 0.0; hit = False
        for _ in range(horizon):
            r = Rs[random.randrange(len(Rs))]
            eq *= (1 + risk_frac * r)
            if eq <= 0:
                eq = 1e-9
            peak = max(peak, eq); dd = min(dd, eq/peak - 1)
            if eq <= ruin:
                hit = True
        ruins += hit; finals.append(eq); maxdd.append(dd)
    finals.sort(); maxdd.sort()
    return {"risk_frac": risk_frac, "horizon": horizon,
            "P_ruin_50pct": round(ruins/iters, 4),
            "median_final_mult": round(finals[iters//2], 3),
            "p05_final": round(finals[int(0.05*iters)], 3),
            "p95_final": round(finals[int(0.95*iters)], 3),
            "median_maxDD": round(statistics.median(maxdd), 3),
            "worst5pct_maxDD": round(maxdd[int(0.05*iters)], 3)}
mcs = []
for rf in (0.01, 0.02, 0.03):
    m = mc(rf); mcs.append(m)
    print(f"  risk {int(rf*100)}%/trade, 100 trades:  P(ruin>50%)={m['P_ruin_50pct']}  "
          f"median x{m['median_final_mult']}  5-95%: x{m['p05_final']}..x{m['p95_final']}  "
          f"medDD={m['median_maxDD']}  worstDD={m['worst5pct_maxDD']}")
out["monte_carlo"] = mcs

# core stats on base for the record
out["base_core"] = {k: (round(v, 4) if isinstance(v, float) else v)
                    for k, v in S.core_stats(Rs).items() if k != "equity"}
p, lo, hi = S.bootstrap_pvalue(Rs)
out["base_core"]["p_expectancy_le0"] = round(p, 4)
out["base_core"]["ci95_expectancy"] = [round(lo, 3), round(hi, 3)]

json.dump(out, open("out/analysis.json", "w"), indent=1)
print("\n-> out/analysis.json written")
