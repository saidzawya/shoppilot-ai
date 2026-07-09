#!/usr/bin/env python3
"""Generate the visual report PNGs from the base ledger + analysis.json."""
import csv, json, random, statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

random.seed(7)
INK = "#1f2933"; ACC = "#3b6ea5"; POS = "#2e8b57"; NEG = "#c0392b"; GRID = "#d7dde3"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK, "axes.grid": True,
                     "grid.color": GRID, "figure.facecolor": "white",
                     "axes.facecolor": "white"})

rows = list(csv.DictReader(open("out/trades_base_5m.csv")))
Rs = [float(r["R"]) for r in rows]
dates = [r["date"] for r in rows]
an = json.load(open("out/analysis.json"))

eq = []; acc = 0
for r in Rs:
    acc += r; eq.append(acc)
peak = []; p = -1e9
for v in eq:
    p = max(p, v); peak.append(p)
dd = [v - pk for v, pk in zip(eq, peak)]

fig, ax = plt.subplots(2, 3, figsize=(15, 8.5))

# 1 equity
ax[0,0].plot(range(1, len(eq)+1), eq, color=ACC, lw=2)
ax[0,0].axhline(0, color=INK, lw=0.8, ls="--")
ax[0,0].fill_between(range(1, len(eq)+1), eq, 0, where=[v>=0 for v in eq], color=POS, alpha=0.12)
ax[0,0].fill_between(range(1, len(eq)+1), eq, 0, where=[v<0 for v in eq], color=NEG, alpha=0.12)
ax[0,0].set_title("Equity curve (cumulative R)"); ax[0,0].set_xlabel("trade #"); ax[0,0].set_ylabel("R")

# 2 drawdown
ax[0,1].fill_between(range(1, len(dd)+1), dd, 0, color=NEG, alpha=0.5)
ax[0,1].set_title(f"Drawdown (max {min(dd):.1f}R)"); ax[0,1].set_xlabel("trade #"); ax[0,1].set_ylabel("R")

# 3 R histogram
ax[0,2].hist(Rs, bins=[-1.5,-1,-.5,0,.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6],
             color=ACC, edgecolor=INK, alpha=0.8)
ax[0,2].axvline(0, color=INK, lw=0.8, ls="--")
ax[0,2].axvline(statistics.mean(Rs), color=NEG, lw=1.5, label=f"mean {statistics.mean(Rs):+.2f}R")
ax[0,2].set_title("R-multiple distribution"); ax[0,2].set_xlabel("R"); ax[0,2].legend()

# 4 monthly (computed from ledger)
from collections import defaultdict
_mo = defaultdict(float)
for r in rows: _mo[r["month"]] += float(r["R"])
mk = sorted(_mo); mv = [round(_mo[k],2) for k in mk]
ax[1,0].bar(mk, mv, color=[POS if v>=0 else NEG for v in mv], edgecolor=INK, alpha=0.85)
ax[1,0].axhline(0, color=INK, lw=0.8)
ax[1,0].set_title("Monthly P&L (R)"); ax[1,0].set_ylabel("sum R")
for i,v in enumerate(mv): ax[1,0].text(i, v, f"{v:+.1f}", ha="center", va="bottom" if v>=0 else "top")

# 5 walk-forward
wf = an["walk_forward"]
wk = ["first-half","second-half"]; wv=[wf[k]["expR"] for k in wk]
ax[1,1].bar(wk, wv, color=[POS if v>=0 else NEG for v in wv], edgecolor=INK, alpha=0.85)
ax[1,1].axhline(0, color=INK, lw=0.8)
ax[1,1].set_title("Walk-forward expectancy (out-of-sample)"); ax[1,1].set_ylabel("R / trade")
for i,v in enumerate(wv): ax[1,1].text(i, v, f"{v:+.2f}", ha="center", va="bottom" if v>=0 else "top")

# 6 outlier sensitivity
osens = an["base_core"]
osd = an.get("outlier") or {}
# rebuild from ledger to be safe
srt = sorted(Rs, reverse=True)
ks=[0,1,2,3]; sv=[sum(srt[k:]) for k in ks]
ax[1,2].bar([f"drop {k}" for k in ks], sv, color=[POS if v>=0 else NEG for v in sv], edgecolor=INK, alpha=0.85)
ax[1,2].axhline(0, color=INK, lw=0.8)
ax[1,2].set_title("Total R after removing top-k winners"); ax[1,2].set_ylabel("sum R")
for i,v in enumerate(sv): ax[1,2].text(i, v, f"{v:+.1f}", ha="center", va="bottom" if v>=0 else "top")

fig.suptitle("US-Open Box-Breakout Gold Strategy — Falsification Report (5m, 39 days, N=36 trades)",
             fontsize=13, fontweight="bold")
fig.tight_layout(rect=[0,0,1,0.97])
fig.savefig("out/report_charts.png", dpi=110)
print("-> out/report_charts.png")

# Monte-Carlo distribution (separate)
fig2, ax2 = plt.subplots(1, 2, figsize=(12, 4.2))
finals = []
for _ in range(5000):
    e = 1.0
    for _ in range(100):
        e *= (1 + 0.02 * Rs[random.randrange(len(Rs))])
    finals.append(e)
ax2[0].hist(finals, bins=50, color=ACC, edgecolor=INK, alpha=0.8)
ax2[0].axvline(1.0, color=INK, ls="--", label="start")
ax2[0].axvline(statistics.median(finals), color=NEG, label=f"median x{statistics.median(finals):.2f}")
ax2[0].set_title("Monte Carlo: equity multiple after 100 trades @ 2% risk\n(resamples the SAME 36 R's — inherits sample bias)")
ax2[0].set_xlabel("final equity multiple"); ax2[0].legend()

# bootstrap expectancy distribution
means = []
for _ in range(10000):
    means.append(sum(Rs[random.randrange(len(Rs))] for _ in range(len(Rs)))/len(Rs))
ax2[1].hist(means, bins=50, color=ACC, edgecolor=INK, alpha=0.8)
ax2[1].axvline(0, color=NEG, lw=1.5, label="H0: no edge")
ax2[1].axvline(statistics.mean(means), color=INK, ls="--", label=f"mean {statistics.mean(means):+.3f}R")
p_le0 = sum(1 for m in means if m<=0)/len(means)
ax2[1].set_title(f"Bootstrap of expectancy — P(<=0) = {p_le0:.2f}\n(cannot reject 'no edge')")
ax2[1].set_xlabel("expectancy R"); ax2[1].legend()
fig2.tight_layout()
fig2.savefig("out/montecarlo_bootstrap.png", dpi=110)
print("-> out/montecarlo_bootstrap.png")
