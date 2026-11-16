"""Synthetic twin for the groundwater audit: forward model + sparse source inversion.

Units: velocity in mm/yr, source strength q in 1000 m^3/yr of compaction volume,
lengths in metres. Kernels are normalised so that the integral over the plane is 1,
therefore v[mm/yr] = sum_j q_j[1000 m^3/yr] * k(r)[1/m^2] * 1e6.
"""
import numpy as np
from scipy.special import k0
from scipy import ndimage
from scipy.optimize import nnls, minimize, linear_sum_assignment
from sklearn.linear_model import lasso_path

PIX, NX, NY = 200.0, 120, 80          # 24 km x 16 km at 200 m
CAND = 500.0                           # candidate source spacing
R0 = 150.0                             # well-field core radius (caps the K0 singularity)
QMIN = 20.0                            # smallest reported source, 1000 m^3/yr
MATCH = 1000.0                         # detection tolerance, m

xs = (np.arange(NX) + 0.5) * PIX
ys = (np.arange(NY) + 0.5) * PIX
XX, YY = np.meshgrid(xs, ys)
cx1 = np.arange(CAND / 2, NX * PIX, CAND)
cy1 = np.arange(CAND / 2, NY * PIX, CAND)
CXX, CYY = np.meshgrid(cx1, cy1)
CX, CY = CXX.ravel(), CYY.ravel()
NCX, NCY = len(cx1), len(cy1)
RFULL = np.hypot(XX.ravel()[:, None] - CX[None, :], YY.ravel()[:, None] - CY[None, :])


def _norm(fun, p):
    r = np.linspace(0, 60000, 600001)
    return np.trapezoid(fun(r, p) * 2 * np.pi * r, r)


def k_k0_raw(r, B):
    return k0(np.maximum(r, R0) / B)


def k_gauss_raw(r, s):
    return np.exp(-r ** 2 / (2 * s ** 2))


_RAW = {"k0": k_k0_raw, "gauss": k_gauss_raw}
_NORMC = {}


def kern(r, fam, p):
    """Normalised kernel in mm/yr per (1000 m^3/yr)."""
    key = (fam, p)
    if key not in _NORMC:
        _NORMC[key] = _norm(_RAW[fam], p)
    return _RAW[fam](r, p) / _NORMC[key] * 1e6


_KCACHE = {}


def Kfull(fam, p):
    key = (fam, p)
    if key not in _KCACHE:
        _KCACHE[key] = kern(RFULL, fam, p)
    return _KCACHE[key]


def grf(rng, L):
    f = ndimage.gaussian_filter(rng.standard_normal((NY, NX)), L / PIX, mode="reflect")
    return f / f.std()


def make_scenario(seed, noise_scale=1.0, B_true=1500.0, sources=None):
    rng = np.random.default_rng(seed)
    if sources is None:
        n = int(rng.integers(6, 11))
        pts = []
        while len(pts) < n:
            p = np.array([rng.uniform(2000, 22000), rng.uniform(5000, 14500)])
            if all(np.hypot(*(p - q)) > 1200 for q in pts):
                pts.append(p)
        pts = np.array(pts)
        q = np.exp(rng.uniform(np.log(40.0), np.log(400.0), n))
    else:
        pts, q = sources
    v_src = np.zeros((NY, NX))
    for (px, py), qj in zip(pts, q):
        v_src += qj * kern(np.hypot(XX - px, YY - py), "k0", B_true)
    clay = np.clip((YY / (NY * PIX)) ** 1.5 + 0.15 * grf(rng, 4000), 0, 1.3)
    bg = 12.0 * clay + 3.0 * grf(rng, 6000)
    noise = noise_scale * (1.5 * grf(rng, 3000) + 1.5 * rng.standard_normal((NY, NX)))
    mfield = grf(rng, 1500)
    mask = mfield < np.quantile(mfield, 0.75)          # True = coherent pixel (75 %)
    clay_obs = clay + 0.1 * grf(rng, 2000)
    d = v_src + bg + noise
    return dict(pts=pts, q=q, v_src=v_src, bg=bg, d=d, mask=mask, clay_obs=clay_obs,
                noise_sd=float(noise.std()), B_true=B_true)


def Zmat(clay_obs):
    x = XX.ravel() / 12000 - 1
    y = YY.ravel() / 8000 - 1
    cols = [clay_obs.ravel()]
    u, v = XX.ravel() / (NX * PIX), YY.ravel() / (NY * PIX)
    for k in range(4):                 # cosine basis, wavelengths >= 12 km (E-W) and >= 16 km (N-S)
        for l in range(3):
            cols.append(np.cos(np.pi * k * u) * np.cos(np.pi * l * v))
    return np.column_stack(cols)


def block_ids(size=4000.0):
    bx = (XX.ravel() // size).astype(int)
    by = (YY.ravel() // size).astype(int)
    return by * (int(NX * PIX // size) + 1) + bx


def resid(Zt, M, w=None):
    """Remove the unpenalised background columns from M (least squares)."""
    if w is not None:
        sw = np.sqrt(w)[:, None]
        Zt = Zt * sw
        M = M * (sw if M.ndim == 2 else sw[:, 0])
    coef = np.linalg.lstsq(Zt, M, rcond=None)[0]
    return M - Zt @ coef, coef


def cv_folds(idx, rng, k=4, size=4000.0):
    b = block_ids(size)[idx]
    ub = np.unique(b)
    perm = rng.permutation(ub.size)
    fold_of = dict(zip(ub, perm % k))
    return np.array([fold_of[v] for v in b])


def surrogate_floor(sc, fam, p, qgrid, idx, rng, n_sur=30, pct=95):
    """Noise-calibrated penalty floor: phase-randomised surrogates of the residual field keep its
    spatial correlation; the floor is the pct-th percentile of the largest source-data correlation
    that such pure-noise fields produce (in units of the lasso penalty)."""
    Zf = Zmat(sc["clay_obs"])
    A = Kfull(fam, p)
    d = sc["d"].ravel()
    beta = np.linalg.lstsq(Zf[idx], d[idx] - A[idx] @ qgrid, rcond=None)[0]
    res = np.zeros(NY * NX)
    res[idx] = d[idx] - A[idx] @ qgrid - Zf[idx] @ beta
    res = res.reshape(NY, NX)
    ind = ndimage.distance_transform_edt(~sc["mask"], return_distances=False, return_indices=True)
    res = res[tuple(ind)]
    amp = np.abs(np.fft.fft2(res))
    Ar, _ = resid(Zf[idx], A[idx])
    mx = []
    for _ in range(n_sur):
        ph = np.angle(np.fft.fft2(rng.standard_normal((NY, NX))))
        sur = np.real(np.fft.ifft2(amp * np.exp(1j * ph))).ravel()[idx]
        sr, _ = resid(Zf[idx], sur)
        mx.append((Ar.T @ sr).max() / idx.size)
    return float(np.percentile(mx, pct))


def fit_sparse(sc, fam="k0", params=(1000., 1250., 1500., 1750., 2000., 2500.), seed=0,
               n_alpha=14, return_cv=False, floor=True, cv_block=2000.0):
    """Non-negative lasso. Kernel width and penalty by spatial block CV, penalty floored by the
    surrogate-noise level, then NNLS refit on the selected support."""
    rng = np.random.default_rng(seed)
    idx = np.flatnonzero(sc["mask"].ravel())
    d = sc["d"].ravel()[idx]
    Z = Zmat(sc["clay_obs"])[idx]
    folds = cv_folds(idx, rng, size=cv_block)
    rel = np.logspace(0, -3.0, n_alpha)
    cv = {}
    for p in params:
        A = Kfull(fam, p)[idx]
        err = np.zeros((4, n_alpha))
        for f in range(4):
            tr, te = folds != f, folds == f
            Ar, cA = resid(Z[tr], A[tr])
            dr, cd = resid(Z[tr], d[tr])
            G = Ar.T @ Ar
            Xy = Ar.T @ dr
            amax = Xy.max() / tr.sum()
            _, coefs, _ = lasso_path(Ar, dr, alphas=amax * rel, positive=True, precompute=G,
                                     Xy=Xy, max_iter=10000, tol=1e-5)
            for a in range(n_alpha):
                qa = coefs[:, a]
                pred = A[te] @ qa + Z[te] @ (cd - cA @ qa)
                err[f, a] = np.sqrt(np.mean((d[te] - pred) ** 2))
        cv[p] = (err.mean(0), err.std(0) / 2.0)
    pbest = min(cv, key=lambda p: cv[p][0].min())
    m, se = cv[pbest]
    a_min = int(np.argmin(m))
    a_1se = a_min                                                  # CV minimum; the floor guards overfit
    A = Kfull(fam, pbest)[idx]
    Ar, _ = resid(Z, A)
    dr, _ = resid(Z, d)
    amax = float((Ar.T @ dr).max() / idx.size)
    alpha = amax * rel[a_1se]
    first = final_fit(sc, fam, pbest, alpha, idx=idx)
    a_floor = 0.0
    if floor:
        a_floor = surrogate_floor(sc, fam, pbest, first["qgrid"], idx, rng)
        if a_floor > alpha:
            alpha = a_floor
            first = final_fit(sc, fam, pbest, alpha, idx=idx)
    out = first
    out.update(param=pbest, alpha=alpha, alpha_cv=amax * rel[a_1se], alpha_floor=a_floor,
               cv_rmse=float(m[a_min]))
    if return_cv:
        out["cv"] = {p: cv[p][0].tolist() for p in cv}
    return out


def final_fit(sc, fam, p, alpha, idx=None, w=None, cols=None):
    """Lasso at a fixed absolute penalty alpha, then NNLS refit. cols restricts the candidates."""
    if idx is None:
        idx = np.flatnonzero(sc["mask"].ravel())
    d = sc["d"].ravel()[idx]
    Z = Zmat(sc["clay_obs"])[idx]
    A = Kfull(fam, p)[idx]
    if cols is not None:
        A = A[:, cols]
    if w is not None:
        keep = w > 0
        A, Z, d, w = A[keep], Z[keep], d[keep], w[keep]
    Ar, _ = resid(Z, A, w)
    dr, _ = resid(Z, d, w)
    G = Ar.T @ Ar
    Xy = Ar.T @ dr
    _, coefs, _ = lasso_path(Ar, dr, alphas=[alpha * len(dr) / (w.sum() if w is not None else len(dr))],
                             positive=True, precompute=G, Xy=Xy, max_iter=10000, tol=1e-5)
    q = coefs[:, 0]
    S = np.flatnonzero(q > 0)
    qsub = np.zeros_like(q)
    if S.size:
        qs, _ = nnls(Ar[:, S], dr, maxiter=20 * S.size)       # debias on the selected support
        qsub[S] = qs
    qfull = np.zeros(CX.size)
    if cols is not None:
        qfull[cols] = qsub
    else:
        qfull = qsub
    return dict(qgrid=qfull, sources=cluster(qfull))


def cluster(qgrid):
    """Merge adjacent selected candidates into sources: (x, y, volume)."""
    g = qgrid.reshape(NCY, NCX)
    lab, n = ndimage.label(g > 0, structure=np.ones((3, 3)))
    src = []
    for k in range(1, n + 1):
        m = lab == k
        qk = g[m].sum()
        if qk >= QMIN:
            src.append((float((CXX[m] * g[m]).sum() / qk), float((CYY[m] * g[m]).sum() / qk), float(qk)))
    return np.array(src).reshape(-1, 3)


def fit_smooth(sc, p=1500.0, seed=0, mus=np.logspace(1.5, -2, 8)):
    """Baseline: non-negative Tikhonov (L2) inversion; sources = local maxima of the smooth map."""
    rng = np.random.default_rng(seed)
    idx = np.flatnonzero(sc["mask"].ravel())
    d = sc["d"].ravel()[idx]
    Z = Zmat(sc["clay_obs"])[idx]
    A = Kfull("k0", p)[idx]
    folds = cv_folds(idx, rng)

    def solve(G, b, mu):
        n = len(b)
        H = G + mu * np.eye(n)
        f = lambda q: (0.5 * q @ H @ q - b @ q, H @ q - b)
        r = minimize(f, np.zeros(n), jac=True, method="L-BFGS-B", bounds=[(0, None)] * n,
                     options=dict(maxiter=300))
        return r.x

    err = np.zeros((4, len(mus)))
    for f in range(4):
        tr, te = folds != f, folds == f
        Ar, cA = resid(Z[tr], A[tr])
        dr, cd = resid(Z[tr], d[tr])
        G, b = Ar.T @ Ar, Ar.T @ dr
        for i, mu in enumerate(mus):
            qa = solve(G, b, mu)
            pred = A[te] @ qa + Z[te] @ (cd - cA @ qa)
            err[f, i] = np.sqrt(np.mean((d[te] - pred) ** 2))
    mu = mus[int(np.argmin(err.mean(0)))]
    Ar, _ = resid(Z, A)
    dr, _ = resid(Z, d)
    q = solve(Ar.T @ Ar, Ar.T @ dr, mu)
    g = q.reshape(NCY, NCX)
    peaks = (g == ndimage.maximum_filter(g, size=3)) & (g > 0)
    py, px = np.nonzero(peaks)
    src = []
    if len(px):
        pk = np.column_stack([CXX[py, px], CYY[py, px]])
        dist = np.hypot(CX[:, None] - pk[None, :, 0], CY[:, None] - pk[None, :, 1])
        near = dist.argmin(1)
        ok = dist.min(1) <= 1500
        for k in range(len(px)):
            qk = q[(near == k) & ok].sum()
            if qk >= QMIN:
                src.append((pk[k, 0], pk[k, 1], float(qk)))
    return dict(qgrid=q, sources=np.array(src).reshape(-1, 3), mu=float(mu))


def fit_bowls(sc, thr=8.0):
    """Baseline: integrate subsidence bowls after removing a fitted background."""
    idx = np.flatnonzero(sc["mask"].ravel())
    Zf = Zmat(sc["clay_obs"])
    beta = np.linalg.lstsq(Zf[idx], sc["d"].ravel()[idx], rcond=None)[0]
    r = (sc["d"].ravel() - Zf @ beta).reshape(NY, NX)
    ind = ndimage.distance_transform_edt(~sc["mask"], return_distances=False, return_indices=True)
    r = r[tuple(ind)]                                        # fill masked pixels by nearest
    r = ndimage.gaussian_filter(r, 300 / PIX)
    lab, n = ndimage.label(r > thr)
    src = []
    for k in range(1, n + 1):
        m = lab == k
        if m.sum() * PIX ** 2 < 0.5e6:
            continue
        vol = r[m].sum() * PIX ** 2 / 1e6                    # mm/yr * m^2 -> 1000 m^3/yr
        if vol >= QMIN:
            src.append((float((XX[m] * r[m]).sum() / r[m].sum()),
                        float((YY[m] * r[m]).sum() / r[m].sum()), float(vol)))
    return dict(sources=np.array(src).reshape(-1, 3))


def match(true_pts, est, tol=MATCH):
    """One-to-one matching by distance. Returns list of (i_true, j_est)."""
    if len(true_pts) == 0 or len(est) == 0:
        return []
    D = np.hypot(true_pts[:, None, 0] - est[None, :, 0], true_pts[:, None, 1] - est[None, :, 1])
    C = np.where(D <= tol, D, 1e9)
    i, j = linear_sum_assignment(C)
    return [(a, b) for a, b in zip(i, j) if D[a, b] <= tol]


def score(sc, est, tol=MATCH):
    pairs = match(sc["pts"], est, tol)
    nt, ne, tp = len(sc["q"]), len(est), len(pairs)
    rel = [abs(est[j, 2] - sc["q"][i]) / sc["q"][i] for i, j in pairs]
    loc = [float(np.hypot(*(est[j, :2] - sc["pts"][i]))) for i, j in pairs]
    return dict(n_true=nt, n_est=ne, tp=tp, recall=tp / nt, precision=tp / ne if ne else 0.0,
                rel_err=rel, loc_err=loc, tot_ratio=float(est[:, 2].sum() / sc["q"].sum()) if ne else 0.0,
                pairs=pairs)


def bootstrap(sc, fit, fam="k0", n_boot=60, seed=0, screen=1500.0):
    """Spatial block bootstrap at fixed hyper-parameters over a screened candidate set
    (all candidates within `screen` metres of a selected candidate). Returns per-source
    5/50/95 % volumes and the selection frequency (stability)."""
    rng = np.random.default_rng(seed)
    idx = np.flatnonzero(sc["mask"].ravel())
    b = block_ids(2000.0)[idx]
    ub = np.unique(b)
    src = fit["sources"]
    if len(src) == 0:
        return np.zeros((0, 3)), np.zeros(0)
    sel = np.flatnonzero(fit["qgrid"] > 0)
    dsel = np.hypot(CX[:, None] - CX[None, sel], CY[:, None] - CY[None, sel]).min(1)
    cols = np.flatnonzero(dsel <= screen)
    dist = np.hypot(CX[:, None] - src[None, :, 0], CY[:, None] - src[None, :, 1])
    near, ok = dist.argmin(1), dist.min(1) <= 1000
    vols = np.zeros((n_boot, len(src)))
    for t in range(n_boot):
        draw = rng.choice(ub, ub.size, replace=True)
        cnt = dict(zip(*np.unique(draw, return_counts=True)))
        w = np.array([cnt.get(v, 0) for v in b], float)
        qb = final_fit(sc, fam, fit["param"], fit["alpha"], idx=idx, w=w, cols=cols)["qgrid"]
        for k in range(len(src)):
            vols[t, k] = qb[(near == k) & ok].sum()
    ci = np.percentile(vols, [5, 50, 95], axis=0).T
    stab = (vols >= 0.5 * QMIN).mean(0)
    return ci, stab
