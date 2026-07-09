#!/usr/bin/env python3
"""Extended research engine — native 5-minute backtest of the US-open box
breakout + retest + hammer strategy on GC=F, over the maximum obtainable
history (~39 RTH days, May 13 - Jul 9 2026).

Rules (UNCHANGED from the author's spec, one documented approximation):
  1. Box = high/low of the 09:30 ET 5m candle.
  2. First later 5m candle whose BODY closes outside the box arms direction.
  3. RETEST required: price must return to the box before we look for entry.
  4. Entry trigger = first HAMMER after the retest. **Approximation:** the
     author uses a 1-minute hammer; 1m data is capped at 30 days by the feed,
     so at the 39-day horizon we use a 5-minute hammer (identical geometry).
     The 20-day 1m study (backtest.py) is retained as the high-resolution
     cross-check of this approximation.
  5. SL = nearest 5m swing (min low / max high of last 3 bars) -/+ buffer.
  6. TP = pre-open session liquidity (context.json pre_high / pre_low).
  7. Flat by 16:00 ET.

Emits a trade ledger with R-multiples and per-trade metadata for stats.py.
Everything here is deterministic and reproducible from the CSVs in data/.
"""
import csv, glob, json, os, statistics
from datetime import datetime, timezone

BUFFER = 0.5          # $ beyond swing for the stop
SWING_LOOKBACK = 3    # 5m bars used for "nearest" swing

def load(path):
    out = []
    with open(path) as f:
        next(f)
        for r in csv.reader(f):
            out.append((int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4])))
    return out

def is_hammer(o, h, l, c, side):
    rng = h - l
    body = abs(c - o)
    if rng < 0.3:
        return False
    if side == "LONG":
        lower = min(o, c) - l
        upper = h - max(o, c)
        return lower >= 2 * body and lower >= 0.5 * rng and upper <= 0.3 * rng
    upper = h - max(o, c)
    lower = min(o, c) - l
    return upper >= 2 * body and upper >= 0.5 * rng and lower <= 0.3 * rng

def fmt(t):
    return datetime.fromtimestamp(t - 4 * 3600, tz=timezone.utc).strftime("%H:%M")

def find_signal(bars, require_retest=True, breakout_cutoff_min=None,
                min_box=0.0, min_breakout=0.0):
    box_hi, box_lo = bars[0][2], bars[0][3]
    box_size = box_hi - box_lo
    if box_size < min_box:
        return {"result": "BOX_TOO_SMALL"}
    open_t = bars[0][0]
    bo = None
    for b in bars[1:]:
        t, o, h, l, c = b
        if breakout_cutoff_min is not None and t > open_t + breakout_cutoff_min * 60:
            break
        if c > box_hi:
            bo = ("LONG", t, c); break
        if c < box_lo:
            bo = ("SHORT", t, c); break
    if bo is None:
        return {"result": "NO_BREAKOUT", "box": (box_hi, box_lo)}
    side, bo_t, bo_c = bo
    if abs(bo_c - (box_hi if side == "LONG" else box_lo)) < min_breakout:
        # breakout body-penetration below threshold: still arm, but flag
        pass
    retest = not require_retest
    for i, b in enumerate(bars):
        t, o, h, l, c = b
        if t <= bo_t:
            continue
        if not retest:
            if (side == "LONG" and l <= box_hi) or (side == "SHORT" and h >= box_lo):
                retest = True
            else:
                continue
        if is_hammer(o, h, l, c, side):
            look = bars[max(0, i - SWING_LOOKBACK + 1):i + 1]
            sl = (min(x[3] for x in look) - BUFFER) if side == "LONG" \
                 else (max(x[2] for x in look) + BUFFER)
            return {"result": "ENTRY", "side": side, "box": (box_hi, box_lo),
                    "box_size": round(box_size, 2), "bo_t": bo_t,
                    "entry_i": i, "entry_t": t, "entry": c, "sl": sl}
    return {"result": ("NO_RETEST" if not retest else "NO_HAMMER"),
            "side": side, "box": (box_hi, box_lo)}

def simulate(side, entry, sl, tp, path_bars, be_R=None, trail_R=None,
             risk=None, partial_R=None):
    """Return (exit_price, exit_reason). Optional management overlays.
    be_R: move stop to entry once +be_R reached. trail_R: trail stop by
    `risk` once +trail_R reached. partial_R: bank half at +partial_R (the
    remaining half then rides to TP/BE/EOD)."""
    cur_sl = sl
    banked = 0.0
    half = False
    peak = entry
    for (t, o, h, l, c) in path_bars:
        fav = (h - entry) if side == "LONG" else (entry - l)
        # break-even
        if be_R is not None and risk and fav >= be_R * risk:
            cur_sl = entry if side == "LONG" else entry
            if side == "LONG":
                cur_sl = max(cur_sl, entry)
        # trailing
        if trail_R is not None and risk and fav >= trail_R * risk:
            if side == "LONG":
                cur_sl = max(cur_sl, h - risk)
            else:
                cur_sl = min(cur_sl, l + risk)
        # partial
        if partial_R is not None and not half and risk and fav >= partial_R * risk:
            banked = 0.5 * partial_R * risk
            half = True
        hit_sl = (l <= cur_sl) if side == "LONG" else (h >= cur_sl)
        hit_tp = tp is not None and ((h >= tp) if side == "LONG" else (l <= tp))
        if hit_sl and hit_tp:
            px = cur_sl
            base = (px - entry) if side == "LONG" else (entry - px)
            return base * (0.5 if half else 1.0) + banked, "SL*"
        if hit_sl:
            px = cur_sl
            base = (px - entry) if side == "LONG" else (entry - px)
            return base * (0.5 if half else 1.0) + banked, "SL"
        if hit_tp:
            base = (tp - entry) if side == "LONG" else (entry - tp)
            return base * (0.5 if half else 1.0) + banked, "TP"
    last = path_bars[-1][4] if path_bars else entry
    base = (last - entry) if side == "LONG" else (entry - last)
    return base * (0.5 if half else 1.0) + banked, "EOD"

def run(tp_mode="liquidity", rr=None, cost=0.0, filt=None,
        be_R=None, trail_R=None, partial_R=None, require_retest=True,
        breakout_cutoff_min=None, min_box=0.0, min_breakout=0.0,
        slip=0.0, delay=False, dataset="5m", verbose=False):
    ctx = json.load(open("context.json"))
    files = sorted(glob.glob(f"data/{dataset}_2026-*.csv"))
    files = [f for f in files if "tail" not in f]
    trades = []
    for path in files:
        date = os.path.basename(path).split("_")[1].replace(".csv", "")
        bars = load(path)
        if len(bars) < 30:
            continue
        sig = find_signal(bars, require_retest, breakout_cutoff_min, min_box, min_breakout)
        if sig.get("result") != "ENTRY":
            continue
        side, entry, sl = sig["side"], sig["entry"], sig["sl"]
        # delayed execution: fill at the OPEN of the bar after the hammer
        if delay and sig["entry_i"] + 1 < len(bars):
            entry = bars[sig["entry_i"] + 1][1]
        # slippage: adverse entry fill
        if slip:
            entry = entry + slip if side == "LONG" else entry - slip
        c = ctx.get(date, {})
        # ---- independent filters (each applied alone) ----
        if filt == "onight_trend":
            if (side == "LONG" and c.get("onight_trend", 0) < 0) or \
               (side == "SHORT" and c.get("onight_trend", 0) > 0):
                continue
        if filt == "onight_counter":  # trade only AGAINST overnight (mean-revert)
            if (side == "LONG" and c.get("onight_trend", 0) > 0) or \
               (side == "SHORT" and c.get("onight_trend", 0) < 0):
                continue
        if isinstance(filt, tuple) and filt[0] == "min_box":
            if sig["box_size"] < filt[1]:
                continue
        if isinstance(filt, tuple) and filt[0] == "atr":
            if c.get("onight_range", 0) < filt[1]:
                continue
        risk = abs(entry - sl)
        if risk <= 0:
            continue
        if tp_mode == "liquidity":
            p = ctx.get(date)
            tp = p["pre_high"] if side == "LONG" else p["pre_low"]
            if (side == "LONG" and tp <= entry + 0.5) or \
               (side == "SHORT" and tp >= entry - 0.5):
                continue  # no target (price already beyond liquidity)
        else:
            tp = entry + rr * risk if side == "LONG" else entry - rr * risk
        path_bars = [b for b in bars if b[0] > sig["entry_t"]]
        pnl, reason = simulate(side, entry, sl, tp, path_bars, be_R, trail_R,
                               risk, partial_R)
        pnl -= 2 * cost
        trades.append({
            "date": date, "side": side, "entry": round(entry, 2),
            "sl": round(sl, 2), "tp": round(tp, 2), "risk": round(risk, 2),
            "pnl": round(pnl, 2), "R": round(pnl / risk, 3), "reason": reason,
            "box_size": sig["box_size"], "onight_trend": c.get("onight_trend", 0),
            "onight_range": c.get("onight_range", 0), "month": date[:7],
        })
    if verbose:
        for t in trades:
            print(f"  {t['date']} {t['side']:5s} {t['reason']:4s} "
                  f"R={t['R']:+.2f} risk={t['risk']:.2f} box={t['box_size']:.2f}")
    return trades

if __name__ == "__main__":
    import sys
    base = run(verbose="-v" in sys.argv)
    os.makedirs("out", exist_ok=True)
    with open("out/trades_base_5m.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(base[0].keys()))
        w.writeheader(); w.writerows(base)
    n = len(base)
    rs = [t["R"] for t in base]
    wins = [r for r in rs if r > 0]
    print(f"\nBASE 5m liquidity-target: {n} trades over 39 days")
    print(f"  win%={100*len(wins)/n:.0f}  sumR={sum(rs):+.2f}  avgR={sum(rs)/n:+.3f}")
