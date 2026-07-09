#!/usr/bin/env python3
"""Save a 5m session-tail CSV from Yahoo chart JSON on stdin."""
import json, sys

raw = sys.stdin.read().strip()
j = json.loads(raw)
r = j["chart"]["result"][0]
ts, q = r["timestamp"], r["indicators"]["quote"][0]
date = sys.argv[1]
n = 0
with open(f"data/5m_tail_{date}.csv", "w") as f:
    f.write("epoch,open,high,low,close\n")
    for i, t in enumerate(ts):
        vals = (q["open"][i], q["high"][i], q["low"][i], q["close"][i])
        if None in vals:
            continue
        f.write(f"{t},{round(vals[0],2)},{round(vals[1],2)},{round(vals[2],2)},{round(vals[3],2)}\n")
        n += 1
print("saved", date, n, "bars")
