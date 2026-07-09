#!/usr/bin/env python3
"""Event-based market database: converts bars into MARKET EVENTS.

MT5-FIRST: if edge_discovery/m1_full.csv exists (from mt5_ingest.py) it is
used automatically at 1-minute resolution. Otherwise falls back to the
reference feed (h1.csv, 2y hourly) with provenance recorded in every row.

Event vocabulary (resolution-agnostic, thresholds in ATR units, ex-ante):
  COMPRESSION       rolling 12-bar range < 40% of its median
  VOL_EXPLOSION     bar range > 3x ATR(48)
  DISPLACEMENT      |body| > 1.5x ATR(48) and body/range > 0.7
  BREAKOUT_UP/DN    close beyond prior 24-bar extreme
  FALSE_BREAK       breakout that closes back inside within 6 bars
  TRUE_BREAK        breakout that holds 6 bars
  RETURN_TO_RANGE   first re-touch of the broken level after TRUE_BREAK
  RETEST_HOLD/FAIL  did the re-touch hold (close back in breakout direction)?
  FVG_UP/DN         3-bar imbalance (gap between bar[i-2].high & bar[i].low)
  FVG_FILL          price trades back through the gap midpoint
  SFP_HIGH/LOW      swing-failure: takes a 24-bar extreme by <0.25 ATR then
                    closes back inside (the classic stop-run pattern)
  TREND_ACCEL       3 consecutive same-direction closes with expanding ranges
Writes events.csv: epoch,dt_utc,event,dir,magnitude_atr,price,src
"""
import csv, os, statistics, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ED = os.path.dirname(HERE)

def pick_source():
    m1 = os.path.join(ED, "m1_full.csv")
    if os.path.exists(m1):
        return m1, "MT5_M1"
    return os.path.join(ED, "h1.csv"), "REF_H1_YAHOO"

def load(path):
    out = []
    with open(path) as f:
        head = f.readline()
        for r in csv.reader(f):
            out.append((int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4])))
    return out

def run():
    path, src = pick_source()
    bars = load(path)
    n = len(bars)
    events = []
    atr = [0.0] * n
    win = []
    for i, b in enumerate(bars):
        win.append(b[2] - b[3])
        if len(win) > 48:
            win.pop(0)
        atr[i] = statistics.mean(win)

    # rolling extremes
    pending_breaks = []  # (idx, dir, level)
    awaiting_retest = []  # (idx, dir, level)
    fvgs = []  # (idx, dir, top, bot, filled)
    def emit(i, ev, d, mag, px):
        events.append((bars[i][0], ev, d, round(mag, 2), px))

    for i in range(50, n):
        t, o, h, l, c = bars[i]
        A = atr[i] or 1e-9
        hh = max(b[2] for b in bars[i-24:i])
        ll = min(b[3] for b in bars[i-24:i])
        rng12 = max(b[2] for b in bars[i-12:i+1]) - min(b[3] for b in bars[i-12:i+1])
        med12 = statistics.median(bars[j][2] - bars[j][3] for j in range(i-12, i+1)) * 12
        body = c - o
        # compression / explosion / displacement
        if med12 > 0 and rng12 < 0.4 * med12:
            emit(i, "COMPRESSION", 0, rng12 / A, c)
        if (h - l) > 3 * A:
            emit(i, "VOL_EXPLOSION", 1 if body > 0 else -1, (h - l) / A, c)
        if abs(body) > 1.5 * A and (h - l) > 0 and abs(body) / (h - l) > 0.7:
            emit(i, "DISPLACEMENT", 1 if body > 0 else -1, abs(body) / A, c)
        # SFP (checked before breakout since it's the failure case)
        if h > hh and (h - hh) < 0.25 * A and c < hh:
            emit(i, "SFP_HIGH", -1, (h - hh) / A, c)
        elif l < ll and (ll - l) < 0.25 * A and c > ll:
            emit(i, "SFP_LOW", +1, (ll - l) / A, c)
        # breakout by CLOSE
        if c > hh:
            emit(i, "BREAKOUT_UP", +1, (c - hh) / A, c)
            pending_breaks.append([i, +1, hh])
        elif c < ll:
            emit(i, "BREAKOUT_DN", -1, (ll - c) / A, c)
            pending_breaks.append([i, -1, ll])
        # resolve pending breaks (true/false after 6 bars)
        for pb in pending_breaks[:]:
            j, d, lvl = pb
            if i - j > 6:
                pending_breaks.remove(pb)
                closes = [bars[x][4] for x in range(j + 1, min(j + 7, n))]
                back = any((cc - lvl) * d < 0 for cc in closes)
                if back:
                    emit(i, "FALSE_BREAK", d, 0, lvl)
                else:
                    emit(i, "TRUE_BREAK", d, 0, lvl)
                    awaiting_retest.append([i, d, lvl])
        # first return to range after a true break
        for ar in awaiting_retest[:]:
            j, d, lvl = ar
            if i <= j:
                continue
            touched = (l <= lvl if d > 0 else h >= lvl)
            if touched:
                awaiting_retest.remove(ar)
                emit(i, "RETURN_TO_RANGE", d, 0, lvl)
                held = (c - lvl) * d > 0
                emit(i, "RETEST_HOLD" if held else "RETEST_FAIL", d, 0, lvl)
            elif i - j > 48:
                awaiting_retest.remove(ar)
        # FVG create / fill
        if i >= 2:
            if bars[i][3] > bars[i-2][2]:  # up imbalance
                fvgs.append([i, +1, bars[i][3], bars[i-2][2], False])
                emit(i, "FVG_UP", +1, (bars[i][3]-bars[i-2][2]) / A, c)
            if bars[i][2] < bars[i-2][3]:  # down imbalance
                fvgs.append([i, -1, bars[i-2][3], bars[i][2], False])
                emit(i, "FVG_DN", -1, (bars[i-2][3]-bars[i][2]) / A, c)
        for g in fvgs[:]:
            j, d, top, bot, _ = g
            if i > j:
                mid = (top + bot) / 2
                if l <= mid <= h:
                    emit(i, "FVG_FILL", d, (i - j), mid)
                    fvgs.remove(g)
                elif i - j > 96:
                    fvgs.remove(g)
        # trend acceleration
        if i >= 3:
            b3 = bars[i-2:i+1]
            dirs = [1 if x[4] > x[1] else -1 for x in b3]
            rngs = [x[2] - x[3] for x in b3]
            if len(set(dirs)) == 1 and rngs[0] < rngs[1] < rngs[2]:
                emit(i, "TREND_ACCEL", dirs[0], rngs[2] / A, c)

    out = os.path.join(HERE, "events.csv")
    with open(out, "w") as f:
        f.write("epoch,dt_utc,event,dir,mag,price,src\n")
        for t, ev, d, mag, px in events:
            dt = datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
            f.write(f"{t},{dt},{ev},{d},{mag},{px},{src}\n")
    from collections import Counter
    cnt = Counter(e[1] for e in events)
    print(f"SOURCE: {src}  bars={n}  events={len(events)}")
    for ev, c_ in cnt.most_common():
        print(f"  {ev:16s} {c_}")
    return events

if __name__ == "__main__":
    run()
