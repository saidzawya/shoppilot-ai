# Gold Edge Discovery Engine — Findings Report
**Data:** GC=F (COMEX gold) · 2 years hourly = **492 trading days** (Jul 2024 – Jul 2026) + **10 years daily** (N=2,512) for seasonality.
**Method:** 36-hypothesis ex-ante grid + 17 seasonality tests, bootstrap CIs, **Benjamini-Hochberg FDR (q=0.10)** across each family, temporal out-of-sample split, look-ahead audit, $0.80 round-trip cost test, k-means regime discovery (numpy, 30 restarts).
**Stance:** every pattern assumed false until the data repeatedly said otherwise. ICT/SMC/retail concepts all entered the grid as equals.

> **Note on inputs:** your MacBook's MT5 data is **not reachable from this cloud session** (full filesystem search: nothing mounted). The engine is built to ingest it the moment it arrives — see §5. Everything below uses the largest feed reachable here. MT5-only features (5m box size, retest counts, 1m MFE/MAE, tick volume, spread-at-entry) are computed automatically once `mt5_ingest.py` runs.

---

## 1 · CONFIRMED STATISTICAL BEHAVIORS (passed FDR + out-of-sample)

### ★ Finding 1 — Gold NY days are one-sided: the first liquidity pool taken is almost always the ONLY one taken
| | swept prev-HIGH first | swept prev-LOW first |
|---|---|---|
| P(also sweeps the other side) | **6%** (base 41%) | **9%** (base 56%) |
| N | 259 | 184 |
| p (bootstrap) | 0.0003 | 0.0003 |
| FDR / OOS both halves | PASS / same sign | PASS / same sign |

**This directly contradicts the popular "sweep one side, then run to the opposite pool" narrative.** Once NY takes yesterday's high, the odds of it also taking yesterday's low collapse by ~35–48 points. Corollary (also FDR-PASS, p=0.0065): days that sweep the prev-day **low** first close **lower** 59% of the time — sweeps are **momentum**, not reversal. The "stop-hunt reversal" read of a low-sweep loses **−$8.9/day** as a trade.
*Economic explanation:* taking out an extreme requires a directional impulse; gold intraday flows trend once committed, and re-crossing the whole prior-day range needs range expansion that occurs on <10% of days. *Honest caveat:* partially mechanical (both-side sweeps require today's range > yesterday's), which is itself the point — the market rarely grants it.

### ★ Finding 2 — Volatility regimes are real, strongly persistent, and directionless
k-means (k=4) on 7 structure features finds quiet/normal/loud/extreme days (avg NY range $31 → $63 → $100 → $135). **P(same regime tomorrow) = 0.78 vs 0.45 random**; the regime ordering reproduces in both data halves. But **no regime predicts direction** (P(up) 0.48–0.57, n.s.).
*Use:* position sizing and stop-width calibration — not direction. *Explanation:* classic volatility clustering (ARCH), the most robust stylized fact in finance; your gold data confirms it cleanly.

### ★ Finding 3 (negative, 10-year certainty) — There is NO day-of-week or month edge in gold
All 17 seasonality tests on 2,512 days: **zero pass FDR**; every 95% CI straddles zero (best candidate, July +$1.70/day, p=0.09, fails correction). Any strategy built on "gold rises on X-day" is noise-mining.

**Also confirmed (descriptive):** price discovery is spread across sessions — NY contributes 37.8% of daily variance, Asia 31.9%, London 29.0%. No session dominates; the "real move only happens in NY" belief is wrong for gold.

---

## 2 · INTERESTING HYPOTHESES — need MT5 1m data to resolve

| Hypothesis | Current evidence | Why unresolved |
|---|---|---|
| Post-sweep continuation is tradeable | direction bias +6.6pts (p=0.08, fails FDR); **$net ≈ 0** at hourly entry | hourly entry is up to 59 min late; 1m entry at the sweep tick may capture the move — or prove there's nothing |
| First-hour strong-down → afternoon fade | +$1.11 net, OOS-stable, p=0.19 | N=164 too small; needs 5-10y |
| Asia+London agreement → NY follows | +5.0pts, right sign both halves, p=0.34 | same |
| July / December positive drift | +$1.7/+$1.7 per day, p=0.09/0.12 | 10 more Julys needed |

## 3 · PATTERNS THAT LOOKED PLAUSIBLE AND FAILED VALIDATION
Every one of these was tested and **rejected** (p ≫ 0.05 and/or wrong-sign OOS and/or negative after $0.80 cost): overnight-trend continuation into NY (all variants) · gap momentum **and** gap fade · previous-day trend continuation · London-fades-Asia signal · first-hour momentum (weak form) · high-volatility-day continuation · quiet-pre-open continuation · every day-of-week direction play · "sweep low → reverse up" (fails at −$8.9/day). The graveyard is the deliverable too: **28 of 36 intraday hypotheses and 17 of 17 seasonal ones died.**

---

## 4 · Ranked summary
| # | Behavior | N | p | FDR | OOS | Cost-survives | Robustness |
|---|---|---|---|---|---|---|---|
| 1 | One-sided liquidity days (high-first) | 259 | 0.0003 | ✓ | ✓ | structural | 3/4 |
| 2 | One-sided liquidity days (low-first) | 184 | 0.0003 | ✓ | ✓ | structural | 3/4 |
| 3 | Low-sweep = bearish momentum day | 184 | 0.0065 | ✓ | ✓ | as fade: NO | 3/4 |
| 4 | Volatility regime persistence 0.78 | 492 | <0.01 | ✓ | ✓ | sizing tool | 4/4 |
| 5 | No DOW/month edge (negative result) | 2512 | — | ✓ | ✓ | — | 4/4 |

**Bottom line:** gold *does* contain repeatable statistical behaviors — but they are **structural** (one-sidedness, volatility clustering), not the directional entry signals retail lore expects. The correct foundation for a robust system, per this data: (a) regime-based sizing, (b) never trade for the opposite liquidity pool after a sweep, (c) treat sweeps as momentum context. Direction itself remains ~coin-flip at every horizon tested here.

## 5 · Plugging in your MacBook MT5 data (unlocks the 1m layer)
```
# On the Mac: export XAUUSD M1 from MT5 (View→Symbols→Bars→Export), then EITHER
git clone <repo> && cp XAUUSD_M1.csv trading-strategy-backtest/edge_discovery/
git checkout claude/trading-strategy-analysis-1e2ejm && git add -A && git commit -m "add MT5 data" && git push
# (gzip it first if >100MB: gzip XAUUSD_M1.csv)  ... then tell me, and I rerun everything at 1m;
# OR run locally:
cd trading-strategy-backtest/edge_discovery
python3 mt5_ingest.py XAUUSD_M1.csv <broker_UTC_offset>
python3 features.py && python3 discover.py && python3 regimes.py && python3 seasonal.py
```
Files: `build_h1.py, build_context.py, features.py, discover.py, seasonal.py, regimes.py, mt5_ingest.py` · data: `h1.csv (11,441 bars), d1.csv (2,512), features.csv (497×27)` · results: `findings.json`.
