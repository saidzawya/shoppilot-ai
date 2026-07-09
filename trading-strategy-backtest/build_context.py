#!/usr/bin/env python3
"""From a coarse (60m) Yahoo JSON with pre/post, compute per-day:
 - pre_high / pre_low : extreme of the pre-open session (03:30-13:30 UTC),
   used as the strategy's 'liquidity' TP target;
 - onight_trend : sign of the pre-open session net change (last close in the
   window minus first open) = overnight directional context for the filter;
 - onight_range : high-low of the pre-open session (a volatility proxy / ATR
   stand-in on days where 5m ATR is not separately computed).
Writes context.json = {date: {...}}.
"""
import json, sys, os
from datetime import datetime, timezone

raw = sys.stdin.read().strip()
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

PRE_LO, PRE_HI = 3 * 3600 + 30 * 60, 13 * 3600 + 30 * 60  # 03:30-13:30 UTC
days = {}
for i, t in enumerate(ts):
    o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
    if None in (o, h, l, c):
        continue
    sod = t % 86400
    if not (PRE_LO <= sod < PRE_HI):
        continue
    d = datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d")
    days.setdefault(d, []).append((t, o, h, l, c))

out = {}
for d, bars in days.items():
    bars.sort()
    if len(bars) < 3:
        continue
    hi = round(max(b[2] for b in bars), 2)
    lo = round(min(b[3] for b in bars), 2)
    net = bars[-1][4] - bars[0][1]
    out[d] = {
        "pre_high": hi, "pre_low": lo,
        "onight_trend": 1 if net > 0 else (-1 if net < 0 else 0),
        "onight_net": round(net, 2),
        "onight_range": round(hi - lo, 2),
    }

path = "context.json"
existing = json.load(open(path)) if os.path.exists(path) else {}
existing.update(out)
json.dump(existing, open(path, "w"), indent=1, sort_keys=True)
print(f"context for {len(out)} days written (total {len(existing)})")
