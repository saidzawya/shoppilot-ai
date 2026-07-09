#!/usr/bin/env python3
"""Institutional performance + robustness statistics for a trade ledger.

Consumes a CSV with at least an 'R' column (R-multiple per trade) plus
optional date/side/month/reason. Prints a full report and returns a dict.
All inference is done in R-units (risk-normalised) so it is independent of
position size. Includes a bootstrap test of H0: expectancy <= 0.

Usage: python3 stats.py [out/trades_base_5m.csv]
"""
import csv, math, random, sys, statistics
from collections import defaultdict

random.seed(42)

def load_R(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            r["R"] = float(r["R"])
            rows.append(r)
    return rows

def max_drawdown(equity):
    peak = equity[0] if equity else 0.0
    mdd = 0.0
    for v in equity:
        peak = max(peak, v)
        mdd = min(mdd, v - peak)
    return mdd  # negative number, in R

def longest_streak(Rs, win):
    best = cur = 0
    for r in Rs:
        hit = (r > 0) if win else (r <= 0)
        cur = cur + 1 if hit else 0
        best = max(best, cur)
    return best

def core_stats(Rs):
    n = len(Rs)
    wins = [r for r in Rs if r > 0]
    losses = [r for r in Rs if r <= 0]
    gross_win = sum(wins)
    gross_loss = -sum(losses)
    pf = gross_win / gross_loss if gross_loss > 0 else float("inf")
    exp = sum(Rs) / n
    equity = []
    acc = 0.0
    for r in Rs:
        acc += r
        equity.append(acc)
    sd = statistics.pstdev(Rs) if n > 1 else 0.0
    sharpe_trade = exp / sd if sd > 0 else 0.0
    # ~annualise: ~1 trade/day, ~252 trading days
    sharpe_ann = sharpe_trade * math.sqrt(252)
    return {
        "n": n, "win_rate": len(wins) / n, "n_win": len(wins), "n_loss": len(losses),
        "profit_factor": pf, "expectancy_R": exp, "median_R": statistics.median(Rs),
        "std_R": sd, "avg_win_R": (gross_win / len(wins)) if wins else 0.0,
        "avg_loss_R": (sum(losses) / len(losses)) if losses else 0.0,
        "largest_win_R": max(Rs), "largest_loss_R": min(Rs),
        "sum_R": sum(Rs), "max_dd_R": max_drawdown(equity),
        "longest_loss_streak": longest_streak(Rs, False),
        "longest_win_streak": longest_streak(Rs, True),
        "sharpe_trade": sharpe_trade, "sharpe_ann": sharpe_ann,
        "equity": equity,
    }

def bootstrap_pvalue(Rs, iters=20000):
    """Stationary bootstrap of the mean. p = P(resampled mean <= 0 | data).
    Also a 95% CI for expectancy."""
    n = len(Rs)
    means = []
    for _ in range(iters):
        s = sum(Rs[random.randrange(n)] for _ in range(n)) / n
        means.append(s)
    means.sort()
    p_le0 = sum(1 for m in means if m <= 0) / iters
    lo = means[int(0.025 * iters)]
    hi = means[int(0.975 * iters)]
    return p_le0, lo, hi

def outlier_sensitivity(Rs):
    s = sorted(Rs, reverse=True)
    out = {}
    for k in (0, 1, 2, 3):
        rem = s[k:]
        out[k] = {"sum_R": sum(rem), "exp_R": sum(rem) / len(rem) if rem else 0,
                  "n": len(rem)}
    return out

def monthly(rows):
    m = defaultdict(list)
    for r in rows:
        m[r.get("month", "?")].append(r["R"])
    return {k: {"n": len(v), "sum_R": round(sum(v), 2),
                "win%": round(100 * sum(1 for x in v if x > 0) / len(v))}
            for k, v in sorted(m.items())}

def report(path):
    rows = load_R(path)
    Rs = [r["R"] for r in rows]
    st = core_stats(Rs)
    p, lo, hi = bootstrap_pvalue(Rs)
    osens = outlier_sensitivity(Rs)
    mo = monthly(rows)
    print(f"\n{'='*60}\nLEDGER: {path}   (N={st['n']} trades)\n{'='*60}")
    print(f"Win rate           {100*st['win_rate']:.1f}%  ({st['n_win']}W / {st['n_loss']}L)")
    print(f"Profit factor      {st['profit_factor']:.2f}")
    print(f"Expectancy         {st['expectancy_R']:+.3f} R / trade")
    print(f"  95% bootstrap CI  [{lo:+.3f}, {hi:+.3f}] R")
    print(f"  P(expectancy<=0)  {p:.3f}   <- H0: no edge")
    print(f"Median R           {st['median_R']:+.3f}")
    print(f"Avg win / avg loss {st['avg_win_R']:+.2f}R / {st['avg_loss_R']:+.2f}R")
    print(f"Largest win/loss   {st['largest_win_R']:+.2f}R / {st['largest_loss_R']:+.2f}R")
    print(f"Std dev R          {st['std_R']:.2f}")
    print(f"Sharpe (per-trade) {st['sharpe_trade']:.3f}   (~annualised {st['sharpe_ann']:.2f})")
    print(f"Total R            {st['sum_R']:+.2f}")
    print(f"Max drawdown       {st['max_dd_R']:.2f} R")
    print(f"Longest loss streak {st['longest_loss_streak']}   win streak {st['longest_win_streak']}")
    print(f"\nOUTLIER SENSITIVITY (remove top-k winners):")
    for k, v in osens.items():
        print(f"  drop top {k}:  sumR={v['sum_R']:+.2f}  exp={v['exp_R']:+.3f}R  (N={v['n']})")
    print(f"\nMONTHLY:")
    for k, v in mo.items():
        print(f"  {k}:  N={v['n']:2d}  sumR={v['sum_R']:+.2f}  win%={v['win%']}")
    return {"stats": st, "p_value": p, "ci": (lo, hi),
            "outlier": osens, "monthly": mo}

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "out/trades_base_5m.csv"
    report(path)
