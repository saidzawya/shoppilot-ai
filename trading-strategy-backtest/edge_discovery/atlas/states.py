#!/usr/bin/env python3
"""Unsupervised market-state discovery + transition probability engine.

Unit of analysis: 6-hour windows of the bar stream (4 windows/day).
Features per window (all in ATR-normalized or scale-free units):
  net_atr, range_atr, efficiency (|net|/gross), ret_vol, n_displacement,
  n_compression, n_explosion, updown_balance
k chosen by silhouette over k=3..7. Labels are NEUTRAL (S1..Sk) — the data
defines the groups; we only describe centroids afterward.
Outputs: state sequence, transition matrix, per-state expectations
(P(next state), continuation, expected range/vol/duration).
"""
import csv, os, statistics
import numpy as np

np.random.seed(9)
HERE = os.path.dirname(os.path.abspath(__file__))
ED = os.path.dirname(HERE)

def load_bars():
    src = os.path.join(ED, "m1_full.csv")
    lbl = "MT5_M1"
    if not os.path.exists(src):
        src, lbl = os.path.join(ED, "h1.csv"), "REF_H1_YAHOO"
    bars = []
    with open(src) as f:
        next(f)
        for r in csv.reader(f):
            bars.append((int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4])))
    return bars, lbl

def windows(bars, secs=6 * 3600):
    w = {}
    for b in bars:
        k = b[0] - (b[0] % secs)
        w.setdefault(k, []).append(b)
    return [(k, v) for k, v in sorted(w.items()) if len(v) >= 4]

def feats(win, atr):
    o, c = win[0][1], win[-1][4]
    hi, lo = max(b[2] for b in win), min(b[3] for b in win)
    rets = [b[4] - b[1] for b in win]
    gross = sum(abs(r) for r in rets) or 1e-9
    A = atr or 1e-9
    disp = sum(1 for b in win if abs(b[4]-b[1]) > 1.5*A and (b[2]-b[3]) > 0 and abs(b[4]-b[1])/(b[2]-b[3]) > 0.7)
    comp = sum(1 for b in win if (b[2]-b[3]) < 0.4*A)
    expl = sum(1 for b in win if (b[2]-b[3]) > 3*A)
    ups = sum(1 for r in rets if r > 0)
    return [ (c-o)/A, (hi-lo)/A, abs(c-o)/gross, statistics.pstdev(rets)/A,
             disp, comp, expl, ups/len(rets) ], (c-o), (hi-lo)

def kmeans(Z, k, restarts=20, iters=100):
    best, bi = None, np.inf
    n = len(Z)
    for _ in range(restarts):
        C = Z[np.random.choice(n, k, replace=False)]
        for _ in range(iters):
            d = ((Z[:, None] - C[None])**2).sum(-1)
            lab = d.argmin(1)
            NC = np.array([Z[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(k)])
            if np.allclose(NC, C): break
            C = NC
        inertia = ((Z - C[lab])**2).sum()
        if inertia < bi: bi, best = inertia, (C.copy(), lab.copy())
    return best, bi

def silhouette(Z, lab, k, sample=400):
    idx = np.random.choice(len(Z), min(sample, len(Z)), replace=False)
    s = []
    for i in idx:
        d = np.sqrt(((Z - Z[i])**2).sum(1))
        a = d[lab == lab[i]].mean()
        b = min(d[lab == j].mean() for j in range(k) if j != lab[i] and (lab == j).any())
        s.append((b - a) / max(a, b, 1e-9))
    return float(np.mean(s))

def run():
    bars, srclbl = load_bars()
    # ATR context: rolling 48-bar mean range
    rngs = [b[2]-b[3] for b in bars]
    atr_by_epoch = {}
    w = []
    for i, b in enumerate(bars):
        w.append(rngs[i])
        if len(w) > 48: w.pop(0)
        atr_by_epoch[b[0]] = statistics.mean(w)
    ws = windows(bars)
    X, nets, ranges, keys = [], [], [], []
    for k_, win in ws:
        f, net, rng = feats(win, atr_by_epoch.get(win[0][0], 1.0))
        X.append(f); nets.append(net); ranges.append(rng); keys.append(k_)
    X = np.array(X); nets = np.array(nets); ranges = np.array(ranges)
    Z = (X - X.mean(0)) / (X.std(0) + 1e-9)

    print(f"SOURCE {srclbl}: {len(Z)} six-hour windows")
    best_k, best_sil, best_lab = None, -1, None
    for k in range(3, 8):
        (C, lab), _ = kmeans(Z, k)
        sil = silhouette(Z, lab, k)
        print(f"  k={k}: silhouette={sil:.3f}")
        if sil > best_sil:
            best_k, best_sil, best_lab, best_C = k, sil, lab, C
    k, lab, C = best_k, best_lab, best_C
    print(f"-> data chooses k={k} (silhouette {best_sil:.3f})\n")

    names = {}
    order = np.argsort([-(lab == j).sum() for j in range(k)])
    FN = ["net", "range", "efficiency", "vol", "n_disp", "n_comp", "n_expl", "up_share"]
    mu, sd = X.mean(0), X.std(0)
    print("STATE PROFILES (centroids, original units; ATR-normalized where noted)")
    for rank, j in enumerate(order):
        names[j] = f"S{rank+1}"
        cent = C[j] * sd + mu
        m = lab == j
        desc = ", ".join(f"{FN[i]}={cent[i]:.2f}" for i in range(len(FN)))
        print(f"  {names[j]} (N={m.sum():4d}, {100*m.mean():.0f}%): {desc}")
        print(f"      expected |range| ${ranges[m].mean():.1f}, net ${nets[m].mean():+.2f}, P(up)={ (nets[m]>0).mean():.2f}")

    # transition matrix + per-state dynamics
    print("\nTRANSITION MATRIX  P(next | current)   (rows=current)")
    hdr = "        " + "  ".join(f"{names[j]:>5s}" for j in order)
    print(hdr)
    trans = np.zeros((k, k))
    for a, b in zip(lab[:-1], lab[1:]):
        trans[a, b] += 1
    for j in order:
        row = trans[j] / max(trans[j].sum(), 1)
        print(f"  {names[j]:>5s} " + "  ".join(f"{row[jj]:5.2f}" for jj in order))

    print("\nPER-STATE DYNAMICS")
    for j in order:
        m = lab == j
        idx = np.where(m)[0]
        idx = idx[idx < len(lab) - 1]
        nxt = idx + 1
        cont = ((nets[idx] > 0) == (nets[nxt] > 0)).mean()
        nxt_rng = ranges[nxt].mean()
        # spell duration
        dur, cur, spells = 1, 1, []
        for a, b in zip(lab[:-1], lab[1:]):
            if a == j and b == j: cur += 1
            elif a == j: spells.append(cur); cur = 1
        d_mean = statistics.mean(spells) if spells else 1
        print(f"  {names[j]}: P(direction continues into next window)={cont:.2f}   "
              f"E[next range]=${nxt_rng:.1f}   E[duration]={d_mean:.1f} windows (~{6*d_mean:.0f}h)")

    np.save(os.path.join(HERE, "state_lab.npy"), lab)
    with open(os.path.join(HERE, "state_windows.csv"), "w") as f:
        f.write("epoch,state,net,range\n")
        for kk, l_, ne, ra in zip(keys, lab, nets, ranges):
            f.write(f"{kk},{names[l_]},{ne:.2f},{ra:.2f}\n")

if __name__ == "__main__":
    run()
