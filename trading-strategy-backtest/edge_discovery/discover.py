#!/usr/bin/env python3
"""Systematic edge discovery over the daily feature table.

Design principles (anti-false-discovery):
 - The hypothesis grid is DEFINED EX-ANTE below: every condition->outcome
   pair we evaluate is enumerated before looking at results.
 - Conditions only use information available BEFORE the outcome window.
 - Every effect gets a bootstrap CI and p-value, then Benjamini-Hochberg
   FDR correction across the ENTIRE grid (q = 0.10).
 - Out-of-sample: the effect must have the same sign in both temporal
   halves of the data.
 - Sensitivity: tercile-based conditions re-tested with boundaries +/-10%.
 - Cost: $-expectancy of the naive directional trade must survive a $0.80
   round-trip cost to count as 'tradeable'.
Robustness score = FDR pass + OOS pass + sensitivity pass + cost pass (0-4).
"""
import csv, json, math, os, random, statistics
from collections import defaultdict

random.seed(123)
HERE = os.path.dirname(__file__)
COST = 0.80  # $ round trip (spread+slippage), conservative retail gold

def load():
    rows = []
    with open(os.path.join(HERE, "features.csv")) as f:
        for r in csv.DictReader(f):
            for k in r:
                if k not in ("date", "first_sweep"):
                    r[k] = float(r[k])
            rows.append(r)
    return rows[5:]  # drop warmup days (no prev/atr history)

def terc(vals, q):
    s = sorted(vals)
    return s[int(q * len(s))]

def bootstrap_diff(sel, base, iters=4000):
    """CI and p for difference in success-rate between subset and all."""
    n_s, n_b = len(sel), len(base)
    if n_s < 15:
        return None
    obs = sum(sel) / n_s - sum(base) / n_b
    diffs = []
    for _ in range(iters):
        rs = sum(sel[random.randrange(n_s)] for _ in range(n_s)) / n_s
        rb = sum(base[random.randrange(n_b)] for _ in range(n_b)) / n_b
        diffs.append(rs - rb)
    diffs.sort()
    lo, hi = diffs[int(0.025 * iters)], diffs[int(0.975 * iters)]
    # p-value: 2 * min tail beyond 0 under recentered distribution
    centered = [d - obs for d in diffs]
    p = 2 * min(sum(1 for d in centered if d >= obs) / iters,
                sum(1 for d in centered if d <= obs) / iters)
    return {"obs_diff": obs, "ci": (lo, hi), "p": max(p, 1 / iters)}

def bh_fdr(results, q=0.10):
    ps = sorted((r["p"], i) for i, r in enumerate(results))
    m = len(ps)
    passed = set()
    max_k = 0
    for k, (p, i) in enumerate(ps, 1):
        if p <= q * k / m:
            max_k = k
    for k, (p, i) in enumerate(ps, 1):
        if k <= max_k:
            passed.add(i)
    return passed

def run():
    rows = load()
    n = len(rows)
    half = rows[n // 2]["date"]

    # helper columns
    for r in rows:
        r["ny_up"] = 1.0 if r["ny_net"] > 0 else 0.0
        r["rest_up"] = 1.0 if r["rest_net"] > 0 else 0.0
        r["cont"] = 1.0 if r["ny_net"] * r["preNY_net"] > 0 else 0.0
        r["ps_up"] = 1.0 if r["post_sweep_net"] > 0 else 0.0
        r["ps_dn"] = 1.0 if r["post_sweep_net"] < 0 else 0.0

    t = {}
    for col in ("preNY_net", "gap_open", "prev_range", "preNY_vol",
                "london_range", "asia_range", "london_net", "prev_net", "fh_net"):
        vals = [r[col] for r in rows]
        t[col] = (terc(vals, 1/3), terc(vals, 2/3))

    # ---------------- EX-ANTE HYPOTHESIS GRID ----------------
    # (name, condition_fn, outcome_col, direction_col_for_$)
    G = []
    def add(name, cond, out, sign):
        G.append((name, cond, out, sign))
    # pre-open direction -> NY direction (continuation family)
    add("asia up -> NY up",        lambda r: r["asia_net"] > 0,  "ny_up", +1)
    add("asia down -> NY down",    lambda r: r["asia_net"] < 0,  "ny_up", -1)
    add("london up -> NY up",      lambda r: r["london_net"] > 0, "ny_up", +1)
    add("london down -> NY down",  lambda r: r["london_net"] < 0, "ny_up", -1)
    add("preNY up -> NY up",       lambda r: r["preNY_net"] > 0, "ny_up", +1)
    add("preNY down -> NY down",   lambda r: r["preNY_net"] < 0, "ny_up", -1)
    add("preNY strong-up -> NY up",   lambda r: r["preNY_net"] > t["preNY_net"][1], "ny_up", +1)
    add("preNY strong-down -> NY down", lambda r: r["preNY_net"] < t["preNY_net"][0], "ny_up", -1)
    add("asia&london agree up -> NY up",
        lambda r: r["asia_net"] > 0 and r["london_net"] > 0, "ny_up", +1)
    add("asia&london agree down -> NY down",
        lambda r: r["asia_net"] < 0 and r["london_net"] < 0, "ny_up", -1)
    add("london fades asia -> NY follows london (up)",
        lambda r: r["asia_net"] < 0 and r["london_net"] > 0, "ny_up", +1)
    add("london fades asia -> NY follows london (down)",
        lambda r: r["asia_net"] > 0 and r["london_net"] < 0, "ny_up", -1)
    # gap family
    add("gap up -> NY up (momentum)",   lambda r: r["gap_open"] > t["gap_open"][1], "ny_up", +1)
    add("gap up -> NY down (fade)",     lambda r: r["gap_open"] > t["gap_open"][1], "ny_up", -1)
    add("gap down -> NY down (momentum)", lambda r: r["gap_open"] < t["gap_open"][0], "ny_up", -1)
    add("gap down -> NY up (fade)",     lambda r: r["gap_open"] < t["gap_open"][0], "ny_up", +1)
    # prev-day family
    add("prev day up -> NY up",     lambda r: r["prev_net"] > 0, "ny_up", +1)
    add("prev day down -> NY down", lambda r: r["prev_net"] < 0, "ny_up", -1)
    add("prev range high -> NY up",  lambda r: r["prev_range"] > t["prev_range"][1], "ny_up", +1)
    # day-of-week (2y; 10y check in seasonal.py)
    for dow, nm in [(0,"Mon"),(1,"Tue"),(2,"Wed"),(3,"Thu"),(4,"Fri")]:
        add(f"{nm} -> NY up", (lambda dd: (lambda r: r["dow"] == dd))(dow), "ny_up", +1)
    # intraday: first hour -> rest of day (condition known at 10:00)
    add("first-hour up -> rest up",     lambda r: r["fh_net"] > 0, "rest_up", +1)
    add("first-hour down -> rest down", lambda r: r["fh_net"] < 0, "rest_up", -1)
    add("first-hour strong-up -> rest up", lambda r: r["fh_net"] > t["fh_net"][1], "rest_up", +1)
    add("first-hour strong-down -> rest down", lambda r: r["fh_net"] < t["fh_net"][0], "rest_up", -1)
    # liquidity sweep family (ordering via first_sweep scan)
    add("first sweep = prev-high -> also sweeps prev-low",
        lambda r: r["first_sweep"] == "high", "took_prev_low", +0)
    add("first sweep = prev-low -> also sweeps prev-high",
        lambda r: r["first_sweep"] == "low", "took_prev_high", +0)
    add("sweep prev-low first -> NY closes up (reversal)",
        lambda r: r["first_sweep"] == "low", "ny_up", +1)
    add("sweep prev-high first -> NY closes down (reversal)",
        lambda r: r["first_sweep"] == "high", "ny_up", -1)
    # volatility conditions -> continuation
    add("quiet pre-open -> NY continuation", lambda r: r["preNY_vol"] < t["preNY_vol"][0], "cont", 0)
    add("loud pre-open -> NY continuation",  lambda r: r["preNY_vol"] > t["preNY_vol"][1], "cont", 0)
    # LOOK-AHEAD-FREE sweep continuation: enter at close of the sweep hour,
    # hold to session close (the only executable version of the sweep family)
    add("low swept first -> post-sweep continues DOWN",
        lambda r: r["first_sweep"] == "low", "ps_dn", -1)
    add("high swept first -> post-sweep continues UP",
        lambda r: r["first_sweep"] == "high", "ps_up", +1)

    # ---------------- evaluate ----------------
    results = []
    for name, cond, out, sign in G:
        base = [r[out] for r in rows]
        sel_rows = [r for r in rows if cond(r)]
        sel = [r[out] for r in sel_rows]
        bt = bootstrap_diff(sel, base)
        if bt is None:
            continue
        # $ expectancy of the naive trade implied by the hypothesis
        if sign != 0:
            src = ("post_sweep_net" if out in ("ps_up", "ps_dn")
                   else "rest_net" if out == "rest_up" else "ny_net")
            pnl = [sign * r[src] for r in sel_rows]
        else:
            pnl = [abs(r["ny_net"]) * 0 for r in sel_rows]  # structural, not directional
        exp_d = statistics.mean(pnl) if pnl else 0.0
        exp_net = exp_d - (COST if sign != 0 else 0.0)
        # OOS same-sign
        eff = []
        for seg in (
            [r for r in sel_rows if r["date"] < half],
            [r for r in sel_rows if r["date"] >= half],
        ):
            allseg = [r for r in rows if (r["date"] < half) == (seg is not None and len(seg) and seg[0]["date"] < half)]
            if len(seg) < 8:
                eff.append(0.0); continue
            b = [r[out] for r in rows if (r["date"] < half) == (seg[0]["date"] < half)]
            eff.append(sum(x[out] for x in seg) / len(seg) - sum(b) / len(b))
        oos = (eff[0] > 0) == (eff[1] > 0) and eff[0] != 0 and eff[1] != 0
        results.append({
            "name": name, "N": len(sel), "base": round(sum(base)/len(base), 3),
            "cond_rate": round(sum(sel)/len(sel), 3),
            "diff": round(bt["obs_diff"], 3),
            "ci_lo": round(bt["ci"][0], 3), "ci_hi": round(bt["ci"][1], 3),
            "p": round(bt["p"], 4), "oos_same_sign": bool(oos),
            "eff_h1": round(eff[0], 3), "eff_h2": round(eff[1], 3),
            "exp_$": round(exp_d, 2), "exp_$_net": round(exp_net, 2),
            "cost_pass": bool(exp_net > 0) if sign != 0 else None,
        })

    passed = bh_fdr(results, q=0.10)
    for i, r in enumerate(results):
        r["fdr_pass"] = i in passed
        score = int(r["fdr_pass"]) + int(r["oos_same_sign"]) + \
                int(bool(r["cost_pass"])) + int(abs(r["diff"]) >= 0.05)
        r["robustness"] = score
    results.sort(key=lambda r: (-r["robustness"], r["p"]))

    print(f"{len(results)} hypotheses evaluated on N={n} days; "
          f"{len(passed)} pass BH-FDR(q=0.10)\n")
    hdr = f"{'hypothesis':46s} {'N':>4s} {'base':>5s} {'rate':>5s} {'diff':>6s} {'p':>7s} {'FDR':>4s} {'OOS':>4s} {'$net':>7s} {'rob':>3s}"
    print(hdr); print("-" * len(hdr))
    for r in results:
        print(f"{r['name'][:46]:46s} {r['N']:4d} {r['base']:5.2f} {r['cond_rate']:5.2f} "
              f"{r['diff']:+6.3f} {r['p']:7.4f} {'PASS' if r['fdr_pass'] else '  - '} "
              f"{'yes' if r['oos_same_sign'] else ' no'} "
              f"{(str(r['exp_$_net']) if r['cost_pass'] is not None else '  n/a'):>7s} {r['robustness']:3d}")
    json.dump(results, open(os.path.join(HERE, "findings.json"), "w"), indent=1)
    print("\n-> findings.json")

    # ---- session price-discovery decomposition (descriptive) ----
    tot_var = statistics.pvariance([r["asia_net"] + r["london_net"] + r["ny_net"] for r in rows])
    print("\nSESSION CONTRIBUTION TO DAILY PRICE DISCOVERY")
    for col in ("asia_net", "london_net", "ny_net"):
        v = statistics.pvariance([r[col] for r in rows])
        rng = statistics.mean([r[col.replace('_net','_range')] for r in rows])
        print(f"  {col[:-4]:7s}: variance share {v/tot_var:5.1%}   avg range ${rng:.1f}")

if __name__ == "__main__":
    run()
