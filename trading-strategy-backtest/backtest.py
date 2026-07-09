#!/usr/bin/env python3
"""Backtest of the US-open 5m box breakout + 1m hammer strategy on GC=F.

Rules implemented (as described by the strategy author):
 1. Box = high/low (wick to wick) of the 9:30-9:35 ET 5-minute candle.
 2. First subsequent 5m candle whose BODY closes outside the box
    (close beyond the edge) arms the setup: above -> LONG, below -> SHORT.
    Breakout search capped at 10:30 ET.
 3. After the breakout candle closes, wait on the 1-minute chart for a
    hammer (long: lower wick >= 2x body, small upper wick; short: mirror).
    Must appear within 30 minutes of the breakout close. Enter at hammer close.
 4. SL below the nearest low = min(low of last 5 one-minute bars) - $0.5
    (short: above nearest high + $0.5).
 5. TP = "the liquidity above in full" = pre-open session extreme
    (fetched separately per trade day). R-multiple outcomes also tracked.
 6. If neither TP nor SL hit by 16:00 ET -> exit at 16:00 close.
"""
import csv, glob, json, os, sys
from datetime import datetime, timezone

def load_csv(path):
    out = []
    with open(path) as f:
        next(f)
        for row in csv.reader(f):
            out.append((int(row[0]), float(row[1]), float(row[2]),
                        float(row[3]), float(row[4])))
    return out

def resample(bars, secs):
    out = {}
    for t, o, h, l, c in bars:
        k = t - (t % secs)
        if k not in out:
            out[k] = [o, h, l, c]
        else:
            b = out[k]
            b[1] = max(b[1], h)
            b[2] = min(b[2], l)
            b[3] = c
    return [(k, *v) for k, v in sorted(out.items())]

def is_hammer(o, h, l, c, direction):
    rng = h - l
    body = abs(c - o)
    if rng < 0.3:
        return False
    if direction == "LONG":
        lower = min(o, c) - l
        upper = h - max(o, c)
        return lower >= 2 * body and lower >= 0.5 * rng and upper <= 0.3 * rng
    else:
        upper = h - max(o, c)
        lower = min(o, c) - l
        return upper >= 2 * body and upper >= 0.5 * rng and lower <= 0.3 * rng

def detect_entry(bars1m, open_epoch):
    """Exactly as the strategy author states, no time limits:
    1) first 5m candle (2nd, 3rd, ... any) whose body closes outside the
       box arms the direction;
    2) REQUIRED: price must first RETURN to the box (retest) — for a long,
       trade back down to the box top; for a short, back up to the box
       bottom — before moving to the 1m chart;
    3) after the retest, the first 1m hammer triggers the entry."""
    b5 = resample(bars1m, 300)
    box = next((b for b in b5 if b[0] == open_epoch), None)
    if box is None:
        return None
    box_hi, box_lo = box[2], box[3]
    bo = None
    for b in b5:
        t, o, h, l, c = b
        if t <= open_epoch:
            continue
        if c > box_hi:
            bo = ("LONG", t + 300, c)
            break
        if c < box_lo:
            bo = ("SHORT", t + 300, c)
            break
    if bo is None:
        return {"result": "NO_BREAKOUT", "box": (box_hi, box_lo)}
    side, bo_close_t, bo_close = bo
    retest = False
    retest_t = None
    for i, b in enumerate(bars1m):
        t, o, h, l, c = b
        if t < bo_close_t:
            continue
        if not retest:
            if (side == "LONG" and l <= box_hi) or (side == "SHORT" and h >= box_lo):
                retest = True
                retest_t = t
            else:
                continue
        # hammer may be the retest bar itself or any later bar
        if is_hammer(o, h, l, c, side):
            look = bars1m[max(0, i - 4):i + 1]
            if side == "LONG":
                sl = min(x[3] for x in look) - 0.5
            else:
                sl = max(x[2] for x in look) + 0.5
            return {"result": "ENTRY", "side": side, "box": (box_hi, box_lo),
                    "bo_close_t": bo_close_t, "retest_t": retest_t,
                    "entry_t": t + 60, "entry": c, "sl": sl, "hammer_i": i}
    if not retest:
        return {"result": "NO_RETEST", "side": side, "box": (box_hi, box_lo),
                "bo_close_t": bo_close_t}
    return {"result": "NO_HAMMER", "side": side, "box": (box_hi, box_lo),
            "bo_close_t": bo_close_t, "retest_t": retest_t}

def fmt_et(epoch):
    # EDT = UTC-4
    return datetime.fromtimestamp(epoch - 4 * 3600, tz=timezone.utc).strftime("%H:%M")

def simulate(side, entry, sl, tp, path_bars):
    """Walk bars after entry; return (outcome, exit_price, exit_t, ambiguous).
    outcome in TP/SL/OPEN/EOD. Ambiguous = TP and SL inside the same bar."""
    for t, o, h, l, c in path_bars:
        if side == "LONG":
            hit_sl = l <= sl
            hit_tp = tp is not None and h >= tp
        else:
            hit_sl = h >= sl
            hit_tp = tp is not None and l <= tp
        if hit_sl and hit_tp:
            return "SL", sl, t, True   # conservative: loss on ambiguity
        if hit_sl:
            return "SL", sl, t, False
        if hit_tp:
            return "TP", tp, t, False
    if path_bars:
        return "OPEN", path_bars[-1][4], path_bars[-1][0], False
    return "OPEN", entry, None, False

COST = 0.0  # one-way cost in $ (spread/2 + slippage); set via --cost

def run(strict_box=True, tp_mode="liquidity", rr=None, quiet=False):
    pre = json.load(open("preopen.json")) if os.path.exists("preopen.json") else {}
    trades = []
    for path in sorted(glob.glob("data/1m_*.csv")):
        date = path.split("_")[1].replace(".csv", "")
        bars = load_csv(path)
        first = bars[0][0]
        open_epoch = first - (first % 86400) + 13 * 3600 + 30 * 60
        r = detect_entry(bars, open_epoch)
        if not r or r["result"] != "ENTRY":
            continue
        side, entry, sl = r["side"], r["entry"], r["sl"]
        box_hi, box_lo = r["box"]
        if strict_box:
            if side == "LONG" and entry <= box_hi:
                trades.append((date, side, "FILTERED_INSIDE_BOX", 0.0))
                continue
            if side == "SHORT" and entry >= box_lo:
                trades.append((date, side, "FILTERED_INSIDE_BOX", 0.0))
                continue
        risk = abs(entry - sl)
        if tp_mode == "liquidity":
            p = pre.get(date)
            if not p:
                continue
            tp = p["pre_high"] if side == "LONG" else p["pre_low"]
            if (side == "LONG" and tp <= entry + 0.5) or (side == "SHORT" and tp >= entry - 0.5):
                trades.append((date, side, "NO_TARGET", 0.0))
                continue
        else:
            tp = entry + rr * risk if side == "LONG" else entry - rr * risk
        # path: rest of 1m bars, then 5m tail if available
        path_bars = [b for b in bars if b[0] >= r["entry_t"]]
        last_1m = path_bars[-1][0] if path_bars else 0
        tail_path = f"data/5m_tail_{date}.csv"
        if os.path.exists(tail_path):
            path_bars += [b for b in load_csv(tail_path)
                          if b[0] >= r["entry_t"] and b[0] > last_1m]
        outcome, exit_p, exit_t, amb = simulate(side, entry, sl, tp, path_bars)
        pnl = (exit_p - entry) if side == "LONG" else (entry - exit_p)
        pnl -= 2 * COST  # round-trip cost
        trades.append((date, side, outcome + ("*" if amb else ""), pnl, risk, entry, sl, tp, exit_t))
    if not quiet:
        closed = [t for t in trades if t[2].startswith(("TP", "SL", "EOD", "OPEN"))]
        wins = [t for t in closed if t[3] > 0]
        losses = [t for t in closed if t[3] <= 0]
        tot_r = sum(t[3] / t[4] for t in closed if len(t) > 4 and t[4] > 0)
        print(f"\n== strict_box={strict_box} tp_mode={tp_mode}{f' rr={rr}' if rr else ''} ==")
        for t in trades:
            if len(t) > 4:
                print(f"  {t[0]} {t[1]:5s} {t[2]:5s} entry {t[5]:.2f} sl {t[6]:.2f} tp {t[7]:.2f}"
                      f" pnl {t[3]:+7.2f} ({t[3]/t[4]:+.2f}R) exit@{fmt_et(t[8]) if t[8] else '-'}")
            else:
                print(f"  {t[0]} {t[1]:5s} {t[2]}")
        n = len(closed)
        print(f"  trades {n}  wins {len(wins)}  losses {len(losses)}"
              f"  winrate {100*len(wins)/n if n else 0:.0f}%  totalR {tot_r:+.2f}"
              f"  total$ {sum(t[3] for t in closed):+.2f}")
    return trades

if __name__ == "__main__":
    if "--cost" in sys.argv:
        COST = float(sys.argv[sys.argv.index("--cost") + 1])
    if len(sys.argv) > 1 and sys.argv[1] == "entries":
        days = sorted(glob.glob("data/1m_*.csv"))
        print(f"{len(days)} days")
        for path in days:
            date = path.split("_")[1].replace(".csv", "")
            bars = load_csv(path)
            first = bars[0][0]
            open_epoch = first - (first % 86400) + 13 * 3600 + 30 * 60
            r = detect_entry(bars, open_epoch)
            if r and r["result"] == "ENTRY":
                risk = abs(r["entry"] - r["sl"])
                print(f"{date}: {r['side']:5s} entry {r['entry']:.2f} @ {fmt_et(r['entry_t'])} ET"
                      f"  SL {r['sl']:.2f} (risk {risk:.2f})  box {r['box'][0]:.1f}/{r['box'][1]:.1f}")
            elif r:
                print(f"{date}: {r['result']} ({r.get('side','-')})")
    else:
        # retest requirement is built into detect_entry; no extra filters
        run(strict_box=False, tp_mode="liquidity")
        for rr in (1, 2, 3):
            run(strict_box=False, tp_mode="rr", rr=rr)
