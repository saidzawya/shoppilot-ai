#!/usr/bin/env python3
"""Slice a wide Yahoo v8 5m chart JSON (stdin) into per-day RTH CSVs.

RTH day = 09:30-16:00 ET (13:30-20:00 UTC during EDT). Writes/overwrites
data/5m_<date>.csv for every day found. Applies the same bogus-tick repair
used for 1m data. Prints one summary line per day so the giant JSON never
needs to be re-read into context.
"""
import json, os, sys
from datetime import datetime, timezone

def clean(bars):
    if len(bars) < 3:
        return bars
    rng = sorted(b[2] - b[3] for b in bars)
    thresh = max(6 * (rng[len(rng) // 2] or 0.5), 8.0)
    out = []
    for t, o, h, l, c in bars:
        bl, bh = min(o, c), max(o, c)
        if bl - l > thresh:
            l = bl
        if h - bh > thresh:
            h = bh
        out.append((t, o, h, l, c))
    return out

raw = sys.stdin.read().strip()
# Unwrap Firecrawl envelope: {"markdown": "```json\n{...}\n```", ...}
if raw.lstrip().startswith("{") and '"markdown"' in raw[:200]:
    env = json.loads(raw)
    raw = env["markdown"]
if raw.startswith("```"):
    raw = raw.strip("`\n")
    if raw.startswith("json"):
        raw = raw[4:]
j = json.loads(raw)
r = j["chart"]["result"][0]
ts = r["timestamp"]
q = r["indicators"]["quote"][0]
days = {}
for i, t in enumerate(ts):
    o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
    if None in (o, h, l, c):
        continue
    # keep only RTH: 13:30 <= UTC-time-of-day < 20:00 (EDT session)
    sod = t % 86400
    if not (13 * 3600 + 30 * 60 <= sod <= 20 * 3600):
        continue
    d = datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d")
    days.setdefault(d, []).append((t, round(o, 2), round(h, 2), round(l, 2), round(c, 2)))

os.makedirs("data", exist_ok=True)
for d, bars in sorted(days.items()):
    bars = clean(sorted(bars))
    if len(bars) < 30:  # partial/holiday day
        print(f"  skip {d}: only {len(bars)} bars")
        continue
    with open(f"data/5m_{d}.csv", "w") as f:
        f.write("epoch,open,high,low,close\n")
        for b in bars:
            f.write(",".join(str(x) for x in b) + "\n")
    print(f"  {d}: {len(bars)} RTH bars")
print(f"TOTAL {len([d for d in days if len(days[d])>=30])} days written")
