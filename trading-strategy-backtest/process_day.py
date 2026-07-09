#!/usr/bin/env python3
"""Parse a Yahoo v8 chart JSON (from stdin), save compact CSV, and screen
the US-open box-breakout strategy for that day.

Usage: python3 process_day.py 2026-06-09 < raw.json
Saves: data/1m_2026-06-09.csv  (epoch,open,high,low,close rounded to 2dp)
Prints a one-line signal summary so the caller knows whether the day
needs the extra session/pre-open fetches.
"""
import json, sys, os

def parse(raw):
    j = json.loads(raw)
    r = j["chart"]["result"][0]
    ts = r["timestamp"]
    q = r["indicators"]["quote"][0]
    bars = []
    for i, t in enumerate(ts):
        o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
        if None in (o, h, l, c):
            continue
        bars.append((t, round(o, 2), round(h, 2), round(l, 2), round(c, 2)))
    return bars

def sanitize(bars):
    """Clamp obviously bogus wicks (Yahoo 1m data sometimes injects a stray
    identical low/high $20+ away from the body across scattered bars)."""
    if not bars:
        return bars
    rngs = sorted(b[2] - b[3] for b in bars)
    med = rngs[len(rngs) // 2] or 0.5
    thresh = max(6 * med, 8.0)
    fixed = []
    n_fix = 0
    for t, o, h, l, c in bars:
        body_lo, body_hi = min(o, c), max(o, c)
        if body_lo - l > thresh:
            l = body_lo
            n_fix += 1
        if h - body_hi > thresh:
            h = body_hi
            n_fix += 1
        fixed.append((t, o, h, l, c))
    if n_fix:
        print(f"  sanitized {n_fix} bogus wick(s)")
    return fixed

def resample_5m(bars):
    """Aggregate 1m bars into 5m bars aligned to 5-minute boundaries."""
    out = {}
    for t, o, h, l, c in bars:
        key = t - (t % 300)
        if key not in out:
            out[key] = [o, h, l, c]
        else:
            b = out[key]
            b[1] = max(b[1], h)
            b[2] = min(b[2], l)
            b[3] = c
    return [(k, *v) for k, v in sorted(out.items())]

def screen(bars, open_epoch):
    """Return signal info for the day. open_epoch = 9:30 ET epoch."""
    b5 = resample_5m(bars)
    box_bar = next((b for b in b5 if b[0] == open_epoch), None)
    if box_bar is None:
        return {"status": "NO_OPEN_BAR"}
    box_hi, box_lo = box_bar[2], box_bar[3]
    sig = {"status": "NO_BREAKOUT", "box_hi": box_hi, "box_lo": box_lo}
    # breakout: first subsequent 5m candle CLOSING beyond the box
    # (loose = close beyond edge; strict = full body beyond edge)
    for b in b5:
        t, o, h, l, c = b
        if t <= open_epoch:
            continue
        if t > open_epoch + 3600:  # cap breakout search at 10:30 ET
            break
        if c > box_hi:
            sig.update(status="BREAKOUT", side="LONG", bo_t=t, bo_close=c,
                       strict=(min(o, c) >= box_hi))
            break
        if c < box_lo:
            sig.update(status="BREAKOUT", side="SHORT", bo_t=t, bo_close=c,
                       strict=(max(o, c) <= box_lo))
            break
    return sig

if __name__ == "__main__":
    date = sys.argv[1]
    raw = sys.stdin.read().strip()
    if raw.startswith("```"):
        raw = raw.strip("`\n")
        if raw.startswith("json"):
            raw = raw[4:]
    bars = sanitize(parse(raw))
    os.makedirs("data", exist_ok=True)
    path = f"data/1m_{date}.csv"
    with open(path, "w") as f:
        f.write("epoch,open,high,low,close\n")
        for b in bars:
            f.write(",".join(str(x) for x in b) + "\n")
    # 9:30 ET in July/June 2026 = 13:30 UTC (EDT)
    first = bars[0][0]
    open_epoch = first - (first % 86400) + 13 * 3600 + 30 * 60
    sig = screen(bars, open_epoch)
    print(f"{date}: {len(bars)} bars -> {path}")
    print(f"SIGNAL {date}: {sig}")
