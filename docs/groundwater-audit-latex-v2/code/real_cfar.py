"""Local matched-filter cone detector (alternative to the global lasso).

At every cell: least squares of the map in a disc of radius RW on [K0 cone (B), 1, x, y], on
coherent cells only, all via FFT convolutions of the mask with basis products. Gives qhat (cone
volume, 1000 m^3/yr) everywhere. Detections = local maxima of qhat above a threshold set from
the clutter level of the clean map. Volume = qhat at the detected peak.

Usage: python real_cfar.py OUT.json [--tracks da] [--span 1822] [--prefilt 0] [--rw 3000]
                           [--trials 40] [--qs 100,200] [--nms 1500]
"""
import sys, json, time
import numpy as np
from scipy import ndimage
from scipy.signal import fftconvolve
import synth as S
import real_lib as R
import real_goal_maps as GM

A = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
OUTP = sys.argv[1]
RW, NMS, NTR, PRE = A("--rw", 3000.0), A("--nms", 1500.0), A("--trials", 40), A("--prefilt", 0)
QS = [float(q) for q in A("--qs", "100,200").split(",")]
BK = A("--B", 1500.0)
POLY = A("--poly", 1)
SEED, BPL = A("--seed", 3), A("--Bplant", 1500.0)
RRW = A("--refine", 0.0)
BGRID = [float(x) for x in A("--Bgrid", "750,1000,1500,2000,2500,3000").split(",")]
TOL = A("--tol", 1000.0)
THRS = [float(x) for x in A("--thrs", "40,60,80,100,120,150,200,250").split(",")]
t0 = time.time()

D, mask, H, info = GM.load(A("--tracks", "da"), A("--span", "1822"))
grid = GM.grid
clay = R.background("edge", H, np.nan_to_num(D), mask, grid)
Z = S.Zmat(clay)
idx = np.flatnonzero(mask.ravel())


def detrend(d):
    """Remove the global background (edge step + long-wavelength cosines) by least squares."""
    beta = np.linalg.lstsq(Z[idx], d.ravel()[idx], rcond=None)[0]
    return np.where(mask, d - (Z @ beta).reshape(d.shape), 0.0)


def prefilter(r):
    if PRE <= 1:
        return r
    x = np.where(mask, r, np.nan)
    return np.where(mask, np.nan_to_num(ndimage.generic_filter(x, np.nanmedian, size=PRE, mode="nearest")), 0.0)


# basis on the window (relative coordinates)
n = int(RW // S.PIX)
yy, xx = np.mgrid[-n:n + 1, -n:n + 1] * S.PIX
disc = (np.hypot(xx, yy) <= RW).astype(float)
Kw = S.kern(np.hypot(xx, yy), "k0", BK) * disc
basis = [Kw, disc, xx / RW * disc, yy / RW * disc]
if POLY == 2:
    basis += [(xx / RW) ** 2 * disc, (yy / RW) ** 2 * disc, xx * yy / RW ** 2 * disc]
NB = len(basis)
m = mask.astype(float)


def conv(a, k):
    # correlation = convolution with the flipped kernel (all bases are symmetric or antisymmetric)
    return fftconvolve(a, k[::-1, ::-1], mode="same")


NM = np.empty((NB, NB) + mask.shape)
for i in range(NB):
    for j in range(i, NB):
        NM[i, j] = NM[j, i] = conv(m, basis[i] * basis[j])
NMt = np.moveaxis(NM, (0, 1), (-2, -1)) + np.eye(NB) * 1e-9
cover = conv(m, disc) / disc.sum()


def qhat(r):
    rhs = np.stack([conv(r * m, b) for b in basis], -1)
    return np.linalg.solve(NMt, rhs[..., None])[..., 0, 0]


def detect(q, thr):
    """Local maxima of qhat above thr within NMS radius, on cells with >= 50 % disc coverage."""
    k = int(NMS // S.PIX) * 2 + 1
    q = np.where(mask & (cover >= 0.5), q, -np.inf)        # off-mask solves are ill-conditioned
    peak = (q == ndimage.maximum_filter(q, size=k)) & (q > thr)
    iy, ix = np.nonzero(peak)
    return np.c_[S.XX[iy, ix], S.YY[iy, ix], q[iy, ix]]


def refine(r, est):
    """Width/volume refinement per detection: in a disc of radius RRW, least squares on
    [K0(B), quadratic] for each B in BGRID; keep the B with the smallest residual."""
    if RRW <= 0 or len(est) == 0:
        return est
    n2 = int(RRW // S.PIX)
    out = est.copy()
    for k, (x, y, _) in enumerate(est):
        iy, ix = int(y // S.PIX), int(x // S.PIX)
        sl = (slice(max(iy - n2, 0), iy + n2 + 1), slice(max(ix - n2, 0), ix + n2 + 1))
        dx, dy = (S.XX[sl] - x) / RRW, (S.YY[sl] - y) / RRW
        sel = mask[sl] & (np.hypot(dx, dy) <= 1)
        base = np.c_[np.ones(sel.sum()), dx[sel], dy[sel], dx[sel] ** 2, dy[sel] ** 2, dx[sel] * dy[sel]]
        best = None
        for B in BGRID:
            Kc = S.kern(np.hypot(dx, dy)[sel] * RRW, "k0", B)
            M = np.c_[Kc, base]
            c, rss, *_ = np.linalg.lstsq(M, r[sl][sel], rcond=None)
            rss = float(np.sum((r[sl][sel] - M @ c) ** 2))
            if best is None or rss < best[0]:
                best = (rss, c[0], B)
        out[k, 2] = best[1]
    return out


r0 = prefilter(detrend(np.nan_to_num(D)))
q0 = qhat(r0)
ok = mask & (cover >= 0.5)
med = float(np.median(q0[ok])); sig = float(1.4826 * np.median(np.abs(q0[ok] - med)))
res = dict(refine=RRW, Bgrid=BGRID, seed=SEED, Bplant=BPL, poly=POLY, info=info, rw=RW, B=BK, nms=NMS, prefilt=PRE, clutter_median=med, clutter_robust_sd=sig,
           clutter_p95=float(np.percentile(q0[ok], 95)), clutter_p99=float(np.percentile(q0[ok], 99)))
print(json.dumps(res), flush=True)

mp = np.flatnonzero(ndimage.binary_erosion(mask, iterations=5).ravel())
rng = np.random.default_rng(SEED)
plants = {q: [] for q in QS}
for q in QS:
    for t in range(NTR):
        pts = []
        while len(pts) < 5:
            j = rng.choice(mp)
            p = np.array([S.XX.ravel()[j], S.YY.ravel()[j]])
            if all(np.hypot(*(p - o)) > 2500 for o in pts):
                pts.append(p)
        pts = np.array(pts)
        add = sum(q * S.kern(np.hypot(S.XX - x, S.YY - y), "k0", BPL) for x, y in pts)
        # planted cones go in before detrend/prefilter: the whole chain sees them
        rp = prefilter(detrend(np.where(mask, np.nan_to_num(D) + add, 0.0)))
        plants[q].append((pts, qhat(rp), rp))
print(f"planted maps ready {time.time() - t0:.0f}s", flush=True)

res["curve"] = []
for thr in THRS:
    base = detect(q0, thr)
    row = dict(thr=thr, n_base=int(len(base)))
    for q in QS:
        rec, fal, vols, hitp, hith, locerr, hiti, vi = [], [], [], [], [], [], [], []
        for pts, qm, rp in plants[q]:
            est = refine(rp, detect(qm, thr))
            pr = S.match(pts, est, tol=TOL)
            got = {j for _, j in pr}
            rec.append(len(pr) / 5)
            for i, j in pr:
                locerr.append(float(np.hypot(*(pts[i] - est[j, :2]))))
            for i, (x, y) in enumerate(pts):          # cones > 2 km from any real (clean-map) detection
                far = len(base) == 0 or np.hypot(base[:, 0] - x, base[:, 1] - y).min() > 2000
                if far:
                    hiti.append(any(ii == i for ii, _ in pr))
                    vi += [float((est[jj, 2] - q) / q) for ii, jj in pr if ii == i]
            for i, (x, y) in enumerate(pts):          # coastal plain (H < 20 m) vs hills
                (hitp if H[int(y // S.PIX), int(x // S.PIX)] < 20 else hith).append(any(ii == i for ii, _ in pr))
            vols += [float((est[j, 2] - q) / q) for _, j in pr]
            fal.append(sum(1 for j in range(len(est)) if j not in got and
                           (len(base) == 0 or np.hypot(base[:, 0] - est[j, 0], base[:, 1] - est[j, 1]).min() > TOL)))
        row[str(int(q))] = dict(recall_isolated=float(np.mean(hiti)), n_isolated=len(hiti),
                                med_abs_vol_err_isolated=float(np.median(np.abs(vi))) if vi else None,
                                med_loc_err_m=float(np.median(locerr)) if locerr else None,
                                p90_loc_err_m=float(np.percentile(locerr, 90)) if locerr else None,
                                recall=float(np.mean(rec)), recall_plain=float(np.mean(hitp)), n_plain=len(hitp),
                                recall_hills=float(np.mean(hith)) if hith else None, new_false=float(np.mean(fal)),
                                med_vol_err=float(np.median(vols)) if vols else None,
                                med_abs_vol_err=float(np.median(np.abs(vols))) if vols else None)
    res["curve"].append(row)
    print(json.dumps(row), flush=True)
json.dump(res, open(OUTP, "w"), indent=1)
print(f"done {time.time() - t0:.0f}s")

if "--truth" in sys.argv:
    # real-data detections at the first threshold vs truth layers (same null tests as before)
    thr = THRS[0]
    real = detect(q0, thr)
    wells, _ = R.pangaea_wells(f"{GM.ROOT}/pangaea.tab", grid)
    ind, _ = R.osm_layers(f"{GM.ROOT}/osm.json", grid)
    rng = np.random.default_rng(11)
    Dz = np.nan_to_num(D)
    tr = dict(thr=thr, n=int(len(real)), sources=real.round(1).tolist(),
              wells_1km=R.location_test(real, ok, Dz, lambda p: R.dist_to_points(p, wells), 1000, rng),
              industrial_500m=R.location_test(real, ok, Dz, lambda p: R.dist_to_raster(p, ind), 500, rng))
    big = real[real[:, 2] >= 150]
    if len(big):
        tr["big_ge150"] = dict(n=int(len(big)),
                               wells_1km=R.location_test(big, ok, Dz, lambda p: R.dist_to_points(p, wells), 1000, rng),
                               industrial_500m=R.location_test(big, ok, Dz, lambda p: R.dist_to_raster(p, ind), 500, rng))
    res["truth"] = tr
    json.dump(res, open(OUTP, "w"), indent=1)
    print("truth", json.dumps({k: v for k, v in tr.items() if k != "sources"}))
