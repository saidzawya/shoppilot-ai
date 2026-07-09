#!/usr/bin/env python3
"""Unsupervised regime discovery: k-means (numpy, k=4, 30 restarts) on
standardized volatility/structure features. Interpretability first: we
report centroids in original units, regime persistence (transition matrix
diagonal), and NY-session outcomes per regime with a split-half check.
No prediction model is built — per the brief, structure before prediction."""
import csv, os
import numpy as np

np.random.seed(5)
HERE = os.path.dirname(__file__)

FEATS = ["asia_range", "london_range", "preNY_vol", "prev_range", "atr5",
         "gap_abs", "preNY_net_abs"]

rows = []
with open(os.path.join(HERE, "features.csv")) as f:
    for r in csv.DictReader(f):
        rows.append(r)
rows = rows[5:]
for r in rows:
    r["gap_abs"] = abs(float(r["gap_open"]))
    r["preNY_net_abs"] = abs(float(r["preNY_net"]))
X = np.array([[float(r[k]) for k in FEATS] for r in rows])
mu, sd = X.mean(0), X.std(0)
Z = (X - mu) / sd

def kmeans(Z, k=4, iters=100, restarts=30):
    best, best_inertia = None, np.inf
    n = len(Z)
    for _ in range(restarts):
        C = Z[np.random.choice(n, k, replace=False)]
        for _ in range(iters):
            d = ((Z[:, None, :] - C[None]) ** 2).sum(-1)
            lab = d.argmin(1)
            newC = np.array([Z[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(k)])
            if np.allclose(newC, C):
                break
            C = newC
        inertia = ((Z - C[lab]) ** 2).sum()
        if inertia < best_inertia:
            best_inertia, best = inertia, (C.copy(), lab.copy())
    return best

C, lab = kmeans(Z)
k = len(C)
ny_net = np.array([float(r["ny_net"]) for r in rows])
ny_rng = np.array([float(r["ny_range"]) for r in rows])
half = len(rows) // 2

print(f"K-MEANS REGIMES (k={k}) on {len(rows)} days — centroids in original units\n")
hdr = "regime  N    " + "  ".join(f"{f[:9]:>9s}" for f in FEATS) + "   nyRng$  nyNet$  P(up)"
print(hdr); print("-" * len(hdr))
order = np.argsort([-(lab == j).sum() for j in range(k)])
names = {}
for rank, j in enumerate(order):
    m = lab == j
    cent = C[j] * sd + mu
    pu = (ny_net[m] > 0).mean()
    print(f"  R{rank+1}   {m.sum():3d}  " + "  ".join(f"{v:9.1f}" for v in cent) +
          f"  {ny_rng[m].mean():7.1f} {ny_net[m].mean():+7.2f}  {pu:.2f}")
    names[j] = f"R{rank+1}"

# persistence
trans_same = sum(1 for i in range(1, len(lab)) if lab[i] == lab[i-1]) / (len(lab)-1)
print(f"\nRegime persistence P(same regime tomorrow) = {trans_same:.2f} "
      f"(random would be ~{sum(((lab==j).mean())**2 for j in range(k)):.2f})")

# split-half stability of regime outcome differences
print("\nSplit-half check of regime NY-range ordering:")
for j in order:
    m1 = (lab[:half] == j); m2 = (lab[half:] == j)
    r1 = ny_rng[:half][m1].mean() if m1.any() else float('nan')
    r2 = ny_rng[half:][m2].mean() if m2.any() else float('nan')
    print(f"  {names[j]}: H1 avg NY range {r1:6.1f}$   H2 {r2:6.1f}$   N={m1.sum()}/{m2.sum()}")
