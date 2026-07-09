# THE GOLD MARKET ATLAS
### A statistical atlas of XAU behavior — Phase 2 of the Edge Discovery program

**Build:** 2026-07-09 · **Primary design target: MT5 broker feed** (`mt5_ingest.py` → every module reruns identically at 1m). MT5 M1 export **not yet delivered** to the research environment, so this edition is the **reference build**: 2y hourly GC=F (11,441 bars / 492 trading days / 1,921 six-hour windows), 60d 5m, 10y daily (2,512 days). Every table states its source; every number regenerates from `events.py, states.py, liquidity.py, precursors.py`.

---

## I · THE EVENT CENSUS (16,357 market events, 2y hourly)
| Event | Count | First-order fact |
|---|---|---|
| Breakouts (close beyond 24-bar extreme) | 1,163 | **55% of resolved breakouts are FALSE** (645 false / 518 true). The base state of a gold breakout is failure. |
| Breakout direction | 796 up / 367 dn | 2:1 upside skew = the 2024-26 bull regime, not a law. |
| FVG imbalances | 2,134 created | **88% filled within 96h.** Imbalance-fill is near-inevitable — an FVG is not a special magnet, it is a description of where price oscillates anyway. |
| Swing-failure patterns (SFP) | 677 | SFP-at-highs outnumber SFP-at-lows 2.2:1 in an uptrend — stop-runs cluster against the trend side. |
| Retests after true breaks | 351 | **57% hold, 43% fail.** A retest is a coin-flip with a small edge, not a confirmation ritual. |
| Displacement candles | 286 | ~1 per 1.7 trading days; see §IV — they cluster in two states only. |

## II · THE SIX MARKET STATES (discovered, not named — k chosen by silhouette)
k-means over 1,921 six-hour windows; the data selected **k=6**:

| State | Share | Signature (data-derived) | E[range] | P(up) | E[duration] |
|---|---|---|---|---|---|
| **S1 balance/rotation** | 41% | efficiency 0.22, no displacement | $30 | 0.50 | ~10h |
| **S2 up-impulse** | 20% | efficiency 0.71, 76% up-bars | $39 | 1.00* | ~8h |
| **S3 down-impulse** | 14% | efficiency 0.71, 24% up-bars | $47 | 0.00* | ~7h |
| **S4 choppy expansion** | 11% | high vol, 1 displacement/window, low efficiency | $57 | 0.54 | ~7h |
| **S5 compression** | 10% | 2.6 compression events/window | $22 | 0.56 | ~8h |
| **S6 panic** | 3% | $86 ranges, 2 vol-explosions/window, 71% down | $86 | 0.29 | ~7h |

\* P(up)≈1/0 is definitional (impulse windows are classified partly by their net), not predictive.

**Transition engine — what the states actually tell you about the NEXT 6 hours:**
- Rows S1–S4 of the transition matrix are ~identical to the base distribution → **knowing today's state barely predicts the next window's type, and direction continuation is 0.44–0.54 everywhere ≈ coin-flip.** Gold's direction is close to memoryless at the 6h horizon.
- Two real exceptions: **compression persists** (S5→S5 = 28% vs 10% base) and resolves with the *lowest* next-window range ($31.6) — *compression does NOT imminently explode*; and **panic mean-reverts** (S6→S2 up-impulse = 29% vs 20% base; next-window range collapses $86→$39). Caveat: N(S6)=56.

## III · LIQUIDITY, MEASURED (the six questions)
1. **Which side first?** 90% of days sweep a prior-day extreme. The side is *inherited, not engineered*: overnight up ⇒ 76% high-first; overnight down ⇒ 71% low-first. Sweeps are momentum bookkeeping.
2. **What never gets revisited?** (10y) Prior-day highs revisit 53%/77%/90% within 1/5/20 days; **lows only 45%/69%/83%** — in a secular uptrend, *sold-off lows are the liquidity that dies unvisited* (17% of daily lows never touched again in a month). Weekly: 76% highs vs 63% lows within 4 weeks.
3. **When?** Brutally front-loaded: **82% of first sweeps occur 09:00–10:00 NY**, 93% by 11:00. After noon a first-sweep is a 3%-of-days rarity.
4. **Vol regime?** P(post-sweep continuation): **LOW vol 0.56 → MID 0.54 → HIGH 0.46** — a clean monotone: calm sweeps continue, violent sweeps tilt to exhaustion. P(both sides swept) stays 5–9% in every regime.
5. **Continuation or exhaustion?** Structure: continuation (Phase-1 finding, p=0.0003 FDR-pass — the other pool is taken on only 6–9% of days). Tradeability: post-sweep drift nets ≈$0 at hourly entry; unresolved at 1m (needs MT5).
6. **Time-of-day effect?** Late sweeps (after 12:00) show negative continuation (−$3.7 avg) vs ≈0 for early — but N=15: recorded as a hypothesis, not a finding.

## IV · WHAT PRECEDES BIG MOVES (mutual-information ranking, exploratory)
| Outcome (base rate) | Top stable precursors | Effect |
|---|---|---|
| **BIG-range day** (10%) | atr5, preNY_range, asia_range (MI≈0.11) | P(big)=**27% after loud overnights vs 0% after quiet ones — 0/164.** |
| **TREND day** (20%) | preNY_vol, preNY_range (MI≈0.05) | 33–34% after loud overnights vs 8–10% after quiet. |
| **FAILED-move day** (5%) | none stable | Failed moves are unpredictable noise in this sample. |

**"What almost never happens":** a top-decile NY range emerging from a bottom-tercile overnight — zero occurrences in 492 days. **"Quiet before the storm" is backwards in gold: storms follow noise.** Expansion begets expansion (vol clustering), at odds with the compression-breakout folklore (§II confirms: compression windows resolve *quietly*).

## V · MYTH LEDGER — retail beliefs vs. this data
| Belief | Verdict | Evidence |
|---|---|---|
| "Sweep one side, then run to the other pool" | **FALSE** | other pool taken 6–9% of days (base 41–56%); FDR-pass, OOS-stable |
| "Low-sweep = bullish stop-hunt reversal" | **FALSE** | those days close *lower* 59%; the reversal trade loses $8.9/day |
| "Compression precedes explosion" | **FALSE (6h–1d horizon)** | S5→lowest next range; big days never follow quiet overnights |
| "Breakouts work" | **MOSTLY FALSE** | 55% of hourly breakouts fail; retest holds only 57% |
| "FVGs get filled" | **TRUE but trivial** | 88% fill — so common it carries almost no information |
| "Gold trends on specific weekdays/months" | **FALSE** | 0/17 seasonal tests pass FDR on 10y |
| "The NY session is where the move happens" | **FALSE** | variance shares: NY 38%, Asia 32%, London 29% |
| "Volatility comes in regimes you can ride" | **TRUE** | 6 states, persistence 0.78 (daily), panic mean-reverts |
| "Direction is predictable from structure" | **UNSUPPORTED** | continuation ≈0.44–0.54 in every state; 28/36 directional hypotheses dead |

## VI · WHAT THE ATLAS IMPLIES FOR ANY FUTURE STRATEGY
The market's exploitable regularities in this data are **about volatility, timing and one-sidedness — not direction**: (1) size and stop-width should be regime-conditional (states are persistent); (2) the first hour owns the liquidity event of the day — after 11:00 the map is mostly settled; (3) never pay for the opposite-pool target; (4) directional alpha, if it exists, lives below the hourly resolution — which is precisely the MT5 1m question.

## VII · UPGRADE PATH (makes this Atlas 5–10y deep and 60× finer)
```
python3 mt5_ingest.py XAUUSD_M1.csv <broker_utc_offset>   # on the Mac or after pushing the CSV to this branch
python3 atlas/events.py && python3 atlas/states.py && python3 atlas/liquidity.py && python3 atlas/precursors.py
```
Auto-unlocks: true 1m event timing, spread-at-event, tick-volume features, 5m box statistics, and enough N to settle every "hypothesis" row above.
