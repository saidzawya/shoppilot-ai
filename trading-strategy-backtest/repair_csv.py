#!/usr/bin/env python3
"""Repair bogus ticks in saved 1m CSVs: closes/opens that jump > threshold
away from BOTH neighbors get replaced by the neighbor median; highs/lows
are then re-clamped to the corrected body when they sit absurdly far out."""
import glob, statistics

def repair(path):
    rows = []
    with open(path) as f:
        header = f.readline()
        for line in f:
            t, o, h, l, c = line.strip().split(",")
            rows.append([int(t), float(o), float(h), float(l), float(c)])
    if len(rows) < 3:
        return 0
    rng = sorted(r[2] - r[3] for r in rows)
    thresh = max(6 * (rng[len(rng) // 2] or 0.5), 8.0)
    n = 0
    for i in range(len(rows)):
        prev_c = rows[i - 1][4] if i > 0 else rows[i][4]
        next_o = rows[i + 1][1] if i < len(rows) - 1 else rows[i][4]
        # bogus close
        if abs(rows[i][4] - prev_c) > thresh and abs(rows[i][4] - next_o) > thresh:
            rows[i][4] = round(statistics.median([prev_c, rows[i][1], next_o]), 2)
            n += 1
        # bogus open
        if abs(rows[i][1] - prev_c) > thresh and abs(rows[i][1] - rows[i][4]) > thresh:
            rows[i][1] = round(prev_c, 2)
            n += 1
        body_hi = max(rows[i][1], rows[i][4])
        body_lo = min(rows[i][1], rows[i][4])
        if rows[i][2] - body_hi > thresh:
            rows[i][2] = body_hi
            n += 1
        if body_lo - rows[i][3] > thresh:
            rows[i][3] = body_lo
            n += 1
        rows[i][2] = max(rows[i][2], body_hi)
        rows[i][3] = min(rows[i][3], body_lo)
    if n:
        with open(path, "w") as f:
            f.write(header)
            for r in rows:
                f.write(",".join(str(x) for x in r) + "\n")
    return n

if __name__ == "__main__":
    for p in sorted(glob.glob("data/1m_*.csv")):
        n = repair(p)
        if n:
            print(f"{p}: repaired {n} field(s)")
    print("repair done")
