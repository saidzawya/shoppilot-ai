# Quantitative Research Report — US-Open Box-Breakout Gold Strategy
## Falsification study · GC=F (COMEX gold futures) · 2026

**Prepared:** 2026-07-09  ·  **Approach:** attempt to *falsify*, not to prove.
**Null hypothesis (H₀):** the strategy has no edge (expectancy ≤ 0).
We reject H₀ only if the data forces us to.

---

## VERDICT

> ## ❌ The strategy does NOT demonstrate a reliable trading edge.

This is the middle-strength of the three permitted conclusions is *not* met; the
evidence lands on the weakest. Specifically, on the largest dataset obtainable in
this environment the strategy is **statistically indistinguishable from no edge**,
its entire profit depends on **one trade out of 36**, its **out-of-sample first
half loses money**, and its expectancy **turns negative under realistic trading
costs**. None of these individually would be fatal; together they are decisive.

A genuine edge could still exist and simply be undetectable at this sample size —
which is exactly why the deliverable includes a **local-run kit to repeat this
study on 3–5 years of real 1-minute data** (`fetch_dukascopy.py`). Until that
larger test is run and passes, the honest classification is *no demonstrated edge*.

---

## 1. Data — what was achievable, and the hard ceiling

| Feed | Result in this environment |
|---|---|
| Yahoo **1-minute** GC=F | **Hard 30-day cap** (`"must be within the last 30 days"`). 3–5 yr of 1m is **impossible here.** |
| Yahoo **5-minute** GC=F | Works back ~60 days → **39 RTH trading days** (May 13 – Jul 9 2026). This is the study set. |
| Yahoo spot **XAUUSD=X** | 404 — not served. |
| Dukascopy / OANDA / stooq / Binance | All **proxy-blocked** (403 CONNECT). |

**Consequence, stated plainly:** the objective of "3–5 years of 1-minute data" is
**not attainable inside this environment.** The largest defensible study here is
**39 trading days / 36 trades** at 5-minute resolution. That is ~5–6× below the
~200-trade rule-of-thumb needed to separate skill from luck at this win rate. Every
conclusion below is therefore *provisional on a small sample* — and the kit exists
to remove that limitation off-platform.

**Timeframe note (documented approximation):** the author's entry trigger is a
**1-minute hammer**. Because 1m is capped at 30 days, the 39-day study uses a
**5-minute hammer** (identical geometry). The previously-validated **20-day 1m
study** (`backtest.py`, true 1m hammer, retest rule) is retained as the
high-resolution cross-check. Both agree on the qualitative result (low win rate,
positive-but-outlier-dependent expectancy), which is itself a robustness signal.

**Rules held constant:** 09:30 ET 5m box → first 5m body-close outside box →
mandatory return-to-box (retest) → hammer entry → stop at nearest swing ±$0.5 →
target = pre-open session liquidity → flat by 16:00 ET. No rule was optimized.

---

## 2. Headline statistics (base strategy, liquidity target, zero cost)

| Metric | Value | Read |
|---|---|---|
| Trades (N) | **36** over 39 days | small sample |
| Win rate | **36%** (13W / 23L) | low — needs big winners to pay |
| Profit factor | **1.23** | weak (institutional floor ≈ 1.3–1.5) |
| Expectancy | **+0.144 R** | positive but… |
| **95% bootstrap CI** | **[−0.41, +0.78] R** | **straddles zero** |
| **P(expectancy ≤ 0)** | **0.33** | **cannot reject "no edge"** |
| Median R | **−1.00** | the typical trade is a full loss |
| Avg win / avg loss | +2.17R / −1.00R | payoff carries it, not hit-rate |
| Largest win / loss | +5.59R / −1.00R | one outlier dominates |
| Max drawdown | **−6.9 R** | on 36 trades |
| Longest losing streak | **6** | psychologically heavy |
| Sharpe (annualised, ~1 trade/day) | ~1.2 | flattering; see caveats |

The bootstrap p-value is the single most important number: **there is a 33%
chance the true expectancy is zero or negative** given this data. Institutional
acceptance needs p < 0.05. We are 6× away.

---

## 3. Robustness — does the profit survive scrutiny? (mostly no)

**3a. Outlier dependence — FATAL.** Remove the best trades one at a time:

| Removed | Total R | Expectancy |
|---|---|---|
| nothing | +5.19 | +0.144 |
| top 1 | **−0.40** | **−0.012** |
| top 2 | −4.77 | −0.140 |
| top 3 | −8.75 | −0.265 |

**Deleting a single trade (of 36) flips the strategy from profitable to
losing.** A real edge is diffuse across many trades; this one is a lottery ticket.

**3b. Walk-forward (out-of-sample, no re-fit) — FAILS.**

| Segment | Dates | N | Win% | PF | Expectancy |
|---|---|---|---|---|---|
| First half | May 13 – Jun 9 | 18 | 33% | **0.82** | **−0.121 R** |
| Second half | Jun 10 – Jul 9 | 18 | 39% | 1.67 | +0.410 R |
| Window 1 | May 13 – Jun 1 | 12 | 25% | 0.76 | −0.179 R |
| Window 2 | Jun 2 – Jun 17 | 12 | 42% | 1.34 | +0.200 R |
| Window 3 | Jun 22 – Jul 9 | 12 | 42% | 1.71 | +0.411 R |

The **first out-of-sample half loses money.** All profit is concentrated in the
back half of a 2-month window — the definition of period-dependence, not edge.

**3c. Monthly:** May **−3.5 R** (18% win), June +7.4 R, July +1.4 R. One good month.

**3d. Execution realism — edge decays to zero then negative.**

| Assumption (per side) | Total R | Expectancy | PF |
|---|---|---|---|
| $0 cost (ideal) | +5.19 | +0.144 | 1.23 |
| $0.15 | +3.39 | +0.094 | 1.14 |
| **$0.30** | +1.61 | +0.045 | **1.06** |
| **$0.50** | **−0.77** | **−0.022** | 0.97 |
| $0.30 + $0.20 slip | +0.52 | +0.014 | 1.02 |
| $0.50 + $0.30 slip + 1-bar delay | **−1.60** | **−0.044** | 0.94 |

Retail gold spread+commission+slippage is realistically **$0.30–0.60/side**. In
that range expectancy is **≈ 0 or negative.** The paper edge does not survive the
broker.

**3e. Feed sensitivity.** A direct COMEX-vs-OANDA test needs OANDA data (blocked).
As a proxy we measured how far each breakout closes beyond the box: **15% of
signals clear the box by < $1, 23% by < $1.5** — smaller than a plausible
futures/spot basis + spread. Those days can show a **different or absent signal on
another feed.** Empirical confirmation: **2026-07-08 was a SHORT on COMEX but a
LONG on the author's OANDA chart.** Signal direction is partly an artifact of feed.

---

## 4. Enhancement filters — each tested ALONE (never combined)

| Filter (alone) | N | Win% | PF | Expectancy | Note |
|---|---|---|---|---|---|
| base | 36 | 36 | 1.23 | +0.144 | — |
| Overnight-trend (trade with) | 18 | 44 | 1.37 | +0.204 | halves sample; in-sample |
| Overnight-counter (fade) | 18 | 28 | 1.12 | +0.084 | — |
| Min box ≥ $8 | 25 | 36 | 1.53 | +0.338 | best-looking → overfit risk |
| Min box ≥ $12 | 11 | 36 | 1.28 | +0.176 | tiny N |
| Overnight-range (ATR) ≥ $60 | 18 | 39 | 1.33 | +0.200 | — |
| Breakout cutoff 30 min | 35 | 37 | 1.28 | +0.177 | barely changes anything |
| Break-even @ +1R | 36 | 22 | 1.30 | +0.116 | lowers win%, cuts winners |
| Trailing stop @ +1R | 36 | 58 | 1.10 | +0.038 | raises win% but kills payoff |
| Partial TP half @ +1R | 36 | 36 | 1.42 | +0.164 | smoother, marginal |

**None of these is a validated improvement.** Every figure is *in-sample* on ≤ 36
trades; the "min box ≥ $8" bump (+0.34 R) is the classic overfit — you are
selecting the periods that happened to work. Per the brief, filters were **not
combined** and **not** used to rescue the base result. They are hypotheses for the
larger study, nothing more. Fixed RR targets: only 1:1 is ~break-even (+0.03 R);
1:2 and 1:3 are net losers.

---

## 5. Monte Carlo (bootstrap of the 36-trade R-sequence, 10k paths)

| Risk / trade | P(ruin >50% DD) | Median ×100 trades | 5–95% band | Median maxDD |
|---|---|---|---|---|
| 1% | 0.0% | ×1.13 | ×0.85 – ×1.55 | −13% |
| 2% | 0.6% | ×1.23 | ×0.69 – ×2.28 | −25% |
| 3% | 6.4% | ×1.31 | ×0.57 – ×3.27 | −36% |

**Read this carefully:** Monte Carlo resamples the *same 36 R's*, so it **inherits
their bias**. It answers "*if* +0.144 R is the true expectancy, what's the risk
profile" — but §2 shows that "if" has a 33% chance of being false. The MC is not
independent evidence of an edge; it is a capital-planning tool *conditional* on an
edge that has not been established. Even taken at face value, a 25% median drawdown
at 2% risk from a system with a 6-trade losing streak is demanding.

---

## 6. Why the sample is the real story

At a 36% win rate with ~2:1 payoff, the standard error on expectancy is large.
The 95% CI [−0.41, +0.78] R means the data is consistent with **anything from a
losing system to a very good one.** You cannot resolve this with 36 trades. To
detect a +0.14 R edge at p<0.05 you need on the order of **250–400 trades**
(≈ 1–1.5 years of daily signals). That test is not runnable in this environment —
hence `fetch_dukascopy.py`.

---

## 7. Deliverables & how to extend (objective #1, done properly off-platform)

```
# On any machine WITHOUT a restrictive proxy:
pip install requests matplotlib
python3 fetch_dukascopy.py 2021-01-01 2025-12-31 XAUUSD   # ~5 yr real 1m data
python3 backtest.py            # true 1-minute rules (hammer on 1m)
python3 research.py            # 5m engine + rich ledger
python3 stats.py out/trades_base_5m.csv
python3 analysis.py            # execution grid, filters, walk-forward, Monte Carlo
python3 make_charts.py         # PNG visual report
```

Run the same battery on 5 years. **Decision rule for a real edge:**
bootstrap P(expectancy ≤ 0) < 0.05 **AND** positive out-of-sample in ≥ 2 of 3
walk-forward windows **AND** expectancy > 0 at $0.40/side cost **AND** result not
dependent on the single best trade. The current 39-day study fails all four.

## Files
- `research.py` — 5m engine (breakout→retest→hammer), rich trade ledger
- `backtest.py` — original 1m engine (20-day high-res cross-check)
- `stats.py` — institutional stats + bootstrap significance test
- `analysis.py` — execution grid, independent filters, walk-forward, Monte Carlo
- `feed_fragility.py` — feed-sensitivity proxy
- `make_charts.py` → `out/report_charts.png`, `out/montecarlo_bootstrap.png`
- `fetch_dukascopy.py` — **5-year local-run kit**
- `build_5m_history.py`, `build_context.py` — data pipeline
- `out/trades_base_5m.csv`, `out/analysis.json` — machine-readable results

---

### One-paragraph summary for a non-quant
We tested the strategy on every trading day we could get (39 days of gold, the
maximum the data feed allows here). It made money on paper — but only because of a
single lucky trade; take that one trade away and it loses. When we split the period
in two and tested the halves separately, the first half lost money. When we added
realistic trading costs, the profit vanished. And there is a one-in-three chance
its "profit" is pure luck. That is not a tradeable edge — it is noise that happened
to be positive. It might have a real edge that is too small to see in 39 days; the
only way to know is to run the included 5-year test on a home computer. Until then:
**do not trade this with real money.**
