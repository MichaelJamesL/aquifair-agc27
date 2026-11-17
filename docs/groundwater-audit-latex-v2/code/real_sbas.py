"""Small-baseline time series from a clipped LiCSAR stack (LiCSBAS-style, simplified).

Usage: python real_sbas.py STACKDIR [--gacos] [--gamma=1e-4]
Writes STACKDIR/ts[_gacos].npz: epochs, cum (n_ep, ny, nx; LOS mm, + = towards satellite),
vel (mm/yr), rms (ifg misfit, mm), n_ifg (pairs used per pixel), and loop-closure statistics.

Steps
 1. loop closure on every triplet (ab + bc - ac): |closure| > pi marks an unwrapping error;
    a pair-pixel is masked when most of its loops are bad; a whole pair is dropped when every
    loop it belongs to has RMS closure > 1.5 rad (LiCSBAS rule: bad loops, no good loop).
 2. optional GACOS: subtract the slant-delay difference (cancels inside loops, so after step 1).
 3. reference every pair to the median of stable high ground.
 4. NSBAS: unknowns = displacement increments between consecutive epochs + a velocity; a weak
    constraint gamma*(inc_k - v*dt_k) = 0 bridges gaps in the network. Pixels sharing one
    valid-pair pattern share one pseudo-inverse.
"""
import sys
from collections import defaultdict
import numpy as np

LAM = 0.055465763
R2MM = -LAM / (4 * np.pi) * 1000          # rad -> mm, + = towards satellite


def dates(p):
    return p[:8], p[9:]


def jd(d):
    return np.datetime64(f"{d[:4]}-{d[4:6]}-{d[6:]}")


def loops_of(pairs):
    idx = {p: k for k, p in enumerate(pairs)}
    out = []
    for p in pairs:
        a, c = dates(p)
        for q in pairs:
            a2, b = dates(q)
            if a2 == a and b < c and f"{b}_{c}" in idx:
                out.append((idx[q], idx[f"{b}_{c}"], idx[p]))    # ab, bc, ac
    return out


def run(stackdir, gacos=False, gamma=1e-4, cc_min=0.15, ref_hgt=60.0, min_dt=0):
    z = np.load(f"{stackdir}/stack.npz")
    pairs = list(z["pairs"])
    unw = z["unw"].astype(np.float32)
    valid = np.isfinite(unw) & (unw != 0) & (z["cc"] >= cc_min * 255)
    days = np.array([(jd(dates(p)[1]) - jd(dates(p)[0])).astype(int) for p in pairs])
    long_ = days >= min_dt               # short pairs carry phase bias ("fading signal"): remove them
    pairs = [p for p, k in zip(pairs, long_) if k]  # before building loops, else their loops look bad
    unw, valid = unw[long_], valid[long_]
    unw[~valid] = 0.0
    n_ifg, ny, nx = unw.shape

    # 1. loop closure
    L = loops_of(pairs)
    nloop = np.zeros((n_ifg, ny, nx), np.int16)
    nbad = np.zeros((n_ifg, ny, nx), np.int16)
    loop_rms = np.zeros(len(L))
    for k, (i, j, m) in enumerate(L):
        ok = valid[i] & valid[j] & valid[m]
        cl = unw[i] + unw[j] - unw[m]
        bad = ok & (np.abs(cl) > np.pi)
        loop_rms[k] = np.sqrt(np.mean(cl[ok] ** 2)) if ok.any() else np.nan
        for t in (i, j, m):
            nloop[t] += ok
            nbad[t] += bad
    good_loop = loop_rms <= 1.5
    in_good = np.zeros(n_ifg, bool)
    in_any = np.zeros(n_ifg, bool)
    for k, (i, j, m) in enumerate(L):
        in_any[[i, j, m]] = True
        if good_loop[k]:
            in_good[[i, j, m]] = True
    drop = in_any & ~in_good
    valid[drop] = False
    valid &= ~((nloop > 0) & (nbad * 2 > nloop))          # most of the pixel's loops are bad
    stats = dict(n_pairs=n_ifg, n_loops=len(L), pairs_dropped=int(drop.sum()),
                 masked_pair_pixels=float(((nloop > 0) & (nbad * 2 > nloop)).mean()),
                 median_loop_rms=float(np.nanmedian(loop_rms)))

    # 2. GACOS
    if gacos:
        g = np.load(f"{stackdir}/gacos.npz")
        ei = {e: k for k, e in enumerate(g["epochs"])}
        for k, p in enumerate(pairs):
            a, b = dates(p)
            if a in ei and b in ei:
                unw[k] -= g["sltd"][ei[b]] - g["sltd"][ei[a]]
            else:
                valid[k] = False
        stats["gacos_epochs"] = int(len(ei))

    # 3. reference
    ref = (z["hgt"] > ref_hgt) & (z["landmask"] > 0)
    for k in range(n_ifg):
        r = valid[k] & ref
        if r.sum() < 50:
            valid[k] = False
            continue
        unw[k] -= np.median(unw[k][r])
    keep = valid.any((1, 2))
    pairs = [p for p, kp in zip(pairs, keep) if kp]
    unw, valid = unw[keep], valid[keep]

    # 4. NSBAS
    eps = sorted({d for p in pairs for d in dates(p)})
    ei = {e: k for k, e in enumerate(eps)}
    t = np.array([(jd(e) - jd(eps[0])).astype(int) for e in eps]) / 365.25
    dtk = np.diff(t)
    ne = len(eps)
    G = np.zeros((len(pairs), ne - 1))
    for k, p in enumerate(pairs):
        a, b = dates(p)
        G[k, ei[a]:ei[b]] = 1.0
    C = np.hstack([gamma * np.eye(ne - 1), -gamma * dtk[:, None]])      # gamma*(inc - v*dt) = 0
    Gf = np.hstack([G, np.zeros((len(pairs), 1))])
    V = valid.reshape(len(pairs), -1)
    D = unw.reshape(len(pairs), -1)
    nvalid = V.sum(0)
    use = np.flatnonzero(nvalid >= 0.5 * len(pairs))
    cum = np.full((ne, ny * nx), np.nan, np.float32)
    vel = np.full(ny * nx, np.nan, np.float32)
    rms = np.full(ny * nx, np.nan, np.float32)
    groups = defaultdict(list)
    for px in use:
        groups[V[:, px].tobytes()].append(px)
    for key, pxs in groups.items():
        rows = np.frombuffer(key, bool)
        A = np.vstack([Gf[rows], C])
        P = np.linalg.pinv(A)
        pxs = np.array(pxs)
        y = np.vstack([D[rows][:, pxs], np.zeros((ne - 1, pxs.size))])
        x = P @ y
        inc, v = x[:-1], x[-1]
        cum[1:, pxs] = np.cumsum(inc, 0) * R2MM
        cum[0, pxs] = 0.0
        vel[pxs] = v * R2MM
        rms[pxs] = np.sqrt(np.mean((Gf[rows] @ x - D[rows][:, pxs]) ** 2, 0)) * abs(R2MM)
    stats.update(n_epochs=ne, pairs_used=len(pairs), groups=len(groups), pixels=int(use.size))
    return dict(epochs=np.array(eps), cum=cum.reshape(ne, ny, nx), vel=vel.reshape(ny, nx),
                rms=rms.reshape(ny, nx), n_ifg=nvalid.reshape(ny, nx)), stats


if __name__ == "__main__":
    sd = sys.argv[1]
    gac = "--gacos" in sys.argv
    gm = float(next((a.split("=")[1] for a in sys.argv if a.startswith("--gamma=")), 1e-4))
    mdt = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--min-dt=")), 0))
    out, st = run(sd, gacos=gac, gamma=gm, min_dt=mdt)
    np.savez_compressed(f"{sd}/ts{'_gacos' if gac else ''}{f'_dt{mdt}' if mdt else ''}.npz", **out)
    print(st)
