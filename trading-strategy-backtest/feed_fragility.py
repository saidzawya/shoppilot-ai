#!/usr/bin/env python3
"""Feed-sensitivity proxy. A direct COMEX(GC=F) vs OANDA(spot) comparison
needs OANDA data, which is not reachable in this environment (XAUUSD=X 404s,
broker feeds proxy-blocked). Instead we quantify the *fragility* of each
signal on the data we have: how far the breakout candle's BODY closes beyond
the box edge. If that margin is smaller than a plausible feed offset
(futures/spot basis + spread, ~$0.5-1.5 on gold), the same candle could
close INSIDE the box on another feed -> the signal weakens, vanishes, or
flips direction. This bounds how often feed choice changes the trade.
"""
import csv, glob, os
import research as R

rows = []
for path in sorted(glob.glob("data/5m_2026-*.csv")):
    if "tail" in path:
        continue
    date = os.path.basename(path).split("_")[1].replace(".csv", "")
    bars = R.load(path)
    if len(bars) < 30:
        continue
    box_hi, box_lo = bars[0][2], bars[0][3]
    for b in bars[1:]:
        t, o, h, l, c = b
        if c > box_hi:
            rows.append((date, "LONG", round(c - box_hi, 2), round(box_hi - box_lo, 2))); break
        if c < box_lo:
            rows.append((date, "SHORT", round(box_lo - c, 2), round(box_hi - box_lo, 2))); break

margins = [r[2] for r in rows]
print(f"Breakout-margin distribution over {len(rows)} signalled days (5m COMEX):")
margins_sorted = sorted(margins)
import statistics
print(f"  median margin {statistics.median(margins):.2f}$   mean {statistics.mean(margins):.2f}$")
for off in (0.5, 1.0, 1.5, 2.0):
    frag = sum(1 for m in margins if m < off)
    print(f"  signals clearing box by < ${off:.1f}: {frag}/{len(rows)} = {100*frag/len(rows):.0f}%  (feed-fragile)")
print(f"\nInterpretation: with a ~$0.5-1.5 futures/spot offset, roughly "
      f"{100*sum(1 for m in margins if m<1.0)/len(rows):.0f}% of days could show a different or absent "
      f"signal on OANDA vs COMEX. Documented empirical case: 2026-07-08 "
      f"(COMEX 5m -> SHORT; author's OANDA chart -> LONG).")
