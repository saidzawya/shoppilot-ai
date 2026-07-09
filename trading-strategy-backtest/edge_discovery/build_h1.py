#!/usr/bin/env python3
"""Parse Yahoo v8 chart JSON (Firecrawl envelope files) into a cumulative
hourly bar table h1.csv (epoch,open,high,low,close,volume). Dedup on epoch.
Usage: python3 build_h1.py <envelope.txt> [more...]
"""
import json, os, sys

rows = {}
path_out = os.path.join(os.path.dirname(__file__), "h1.csv")
if os.path.exists(path_out):
    with open(path_out) as f:
        next(f)
        for line in f:
            p = line.strip().split(",")
            rows[int(p[0])] = line.strip()

for src in sys.argv[1:]:
    raw = open(src).read().strip()
    if raw.lstrip().startswith("{") and '"markdown"' in raw[:200]:
        raw = json.loads(raw)["markdown"]
    if raw.startswith("```"):
        raw = raw.strip("`\n")
        if raw.startswith("json"):
            raw = raw[4:]
    j = json.loads(raw)
    r = j["chart"]["result"][0]
    ts = r["timestamp"]
    q = r["indicators"]["quote"][0]
    added = 0
    for i, t in enumerate(ts):
        o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
        v = (q.get("volume") or [None]*len(ts))[i] or 0
        if None in (o, h, l, c) or t in rows:
            continue
        # sanity: reject absurd bars (bad ticks)
        if h < l or h <= 0 or (h - l) > 0.2 * c:
            continue
        rows[t] = f"{t},{round(o,2)},{round(h,2)},{round(l,2)},{round(c,2)},{int(v)}"
        added += 1
    print(f"{os.path.basename(src)}: +{added} bars")

with open(path_out, "w") as f:
    f.write("epoch,open,high,low,close,volume\n")
    for t in sorted(rows):
        f.write(rows[t] + "\n")
print(f"h1.csv total {len(rows)} bars")
