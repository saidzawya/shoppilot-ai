#!/usr/bin/env python3
"""Append extra 1m bars (Yahoo chart JSON on stdin) to an existing day CSV,
dedup by epoch, keep sorted, then re-run the repair pass."""
import json, sys
import repair_csv

date = sys.argv[1]
path = f"data/1m_{date}.csv"
j = json.loads(sys.stdin.read().strip())
r = j["chart"]["result"][0]
ts, q = r["timestamp"], r["indicators"]["quote"][0]
rows = {}
with open(path) as f:
    header = f.readline()
    for line in f:
        p = line.strip().split(",")
        rows[int(p[0])] = line.strip()
added = 0
for i, t in enumerate(ts):
    vals = (q["open"][i], q["high"][i], q["low"][i], q["close"][i])
    if None in vals or t in rows:
        continue
    rows[t] = f"{t},{round(vals[0],2)},{round(vals[1],2)},{round(vals[2],2)},{round(vals[3],2)}"
    added += 1
with open(path, "w") as f:
    f.write(header)
    for t in sorted(rows):
        f.write(rows[t] + "\n")
n = repair_csv.repair(path)
print(f"{date}: +{added} bars (total {len(rows)}), repaired {n}")
