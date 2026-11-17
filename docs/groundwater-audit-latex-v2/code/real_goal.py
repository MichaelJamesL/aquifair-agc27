"""Detection-limit harness on cached rate maps: target recall >= 60 % and median |volume error|
< 30 % for planted q = 100 (1000 m^3/yr) K0 cones, B = 1.5 km.

Usage: python real_goal.py OUT.json [--tracks d|da] [--span 1822|1422|1426|1826] [--bg edge|med]
                           [--floor none|robust] [--trials N] [--qs 100,200] [--medw 2000]
Rate maps: stacking of pairs >= 24 d (GACOS off: no measurable effect), cached per stack in
realdata/semarang/exp/goal_<stack>.npz (num/den sums so stacks of different years add).
"""
import sys, os, json, time
import numpy as np
from scipy import ndimage
import synth as S
import real_lib as R

ROOT = "C:/Kuliah/hackathon/agc-26/realdata/semarang"
A = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
OUTP = sys.argv[1]
TRACKS, SPAN, BG, FLOOR = A("--tracks", "da"), A("--span", "1822"), A("--bg", "edge"), A("--floor", "robust")
PRE = A("--prefilt", 0)
NTR, QS, MEDW = A("--trials", 6), [float(q) for q in A("--qs", "100,200").split(",")], A("--medw", 2000.0)
grid = R.Grid(428000.0, 9220000.0, 32749)
t0 = time.time()


def cached_sums(stack):
    """Pair-by-pair stacking sums (pairs >= 24 d) on the native grid; low memory."""
    fn = f"{ROOT}/exp/goal_{stack}.npz"
    if os.path.exists(fn):
        return dict(np.load(fn))
    z = np.load(f"{ROOT}/{stack}/stack.npz")
    pairs, hgt, land = z["pairs"], z["hgt"], z["landmask"]
    unw, cc = z["unw"], z["cc"]
    ta = np.array([np.datetime64(f"{p[:4]}-{p[4:6]}-{p[6:8]}") for p in pairs])
    tb = np.array([np.datetime64(f"{p[9:13]}-{p[13:15]}-{p[15:]}") for p in pairs])
    dt = (tb - ta).astype(int) / 365.25
    ref = (hgt > 60) & (land > 0)
    num = np.zeros(hgt.shape); den = np.zeros(hgt.shape); cnt = np.zeros(hgt.shape); n = 0
    for k in np.flatnonzero(dt * 365.25 >= 23.5):
        v = np.isfinite(unw[k]) & (unw[k] != 0) & (cc[k] >= 0.15 * 255)
        r = v & ref
        if r.sum() < 50:
            continue
        los = (unw[k] - np.median(unw[k][r])) * (-R.LAM / (4 * np.pi) * 1000)
        num += np.where(v, los, 0); den += v * dt[k]; cnt += v; n += 1
    out = dict(num=num, den=den, cnt=cnt, n=n, U=z["U"], hgt=hgt, land=land, transform=z["transform"])
    np.savez(fn, **out)
    return out


def track_map(stacks):
    ss = [cached_sums(s) for s in stacks]
    num, den, cnt, n = sum(s["num"] for s in ss), sum(s["den"] for s in ss), sum(s["cnt"] for s in ss), sum(int(s["n"]) for s in ss)
    s0 = ss[0]
    ok = (cnt / n >= 0.5) & (s0["land"] > 0)
    sub = np.where(ok, -(num / np.maximum(den, 1e-9)) / s0["U"], np.nan)
    return dict(sub=sub, hgt=s0["hgt"], transform=s0["transform"])


desc = {"1822": ["t076"], "1422": ["t076", "t076_1517"], "1426": ["t076", "t076_1517", "t076_2326"],
        "1826": ["t076", "t076_2326"]}[SPAN]
rms = [track_map(desc)] + ([track_map(["t127"])] if TRACKS == "da" else [])
H = R.grid_hgt(rms[0], grid)
if len(rms) == 2:
    D, mask, qc = R.combine_tracks(rms, grid, H)
else:
    D, c = grid.block_mean(rms[0]["sub"], rms[0]["transform"])
    mask, qc = c >= 1, {}
D = np.where(mask, D, np.nan)
Dz = np.nan_to_num(D)
res = dict(prefilt=PRE, tracks=TRACKS, span=SPAN, bg=BG, floor=FLOOR, medw=MEDW, qc=qc,
           stable=R.stable_noise(D, H, mask), mask_frac=float(mask.mean()))
print(json.dumps(res), flush=True)
if FLOOR == "robust":
    R.use_robust_floor()


def med_bg(d, model=None, w=MEDW):
    """Median-filter background of (d - cone model) on the coherent cells (NaN-aware)."""
    x = np.where(mask, d - (0 if model is None else model), np.nan)
    k = int(round(w / S.PIX)) | 1
    return ndimage.generic_filter(x, np.nanmedian, size=k, mode="nearest")


def prefilter(d):
    """Remove compact features (< window) with a NaN-aware median filter: fills, landfills and
    other sub-km real motion are not pumping cones (B >= 1 km keeps cones broad)."""
    if PRE <= 1:
        return d
    x = np.where(mask, d, np.nan)
    return np.where(mask, np.nan_to_num(ndimage.generic_filter(x, np.nanmedian, size=PRE, mode="nearest")), 0.0)


def fit(d):
    d = prefilter(d)
    """Sparse K0 fit with the chosen background; 'med' backgrounds are re-estimated against the
    fitted cones twice so a cone is not absorbed by the filter."""
    if BG == "edge":
        clay = R.background("edge", H, d, mask, grid)
        return S.fit_sparse(R.model_input_grid(d, mask, clay), params=(1500.,), seed=0)["sources"]
    model = None
    for it in range(3):
        b = np.nan_to_num(med_bg(d, model))
        sc = R.model_input_grid(d, mask, b)
        src = S.fit_sparse(sc, params=(1500.,), seed=0)["sources"]
        model = sum((q * S.kern(np.hypot(S.XX - x, S.YY - y), "k0", 1500.0) for x, y, q in src),
                    np.zeros_like(d))
    return src


base = fit(Dz)
res["n_base"] = int(len(base))
print("base sources", len(base), f"{time.time() - t0:.0f}s", flush=True)
mp = np.flatnonzero(ndimage.binary_erosion(mask, iterations=5).ravel())
rng = np.random.default_rng(3)
res["detect"] = {}
for q in QS:
    rec, fal, vols, vadj = [], [], [], []
    for t in range(NTR):
        pts = []
        while len(pts) < 5:
            j = rng.choice(mp)
            p = np.array([S.XX.ravel()[j], S.YY.ravel()[j]])
            if all(np.hypot(*(p - o)) > 2500 for o in pts):
                pts.append(p)
        pts = np.array(pts)
        add = sum(q * S.kern(np.hypot(S.XX - x, S.YY - y), "k0", 1500.0) for x, y in pts)
        est = fit(np.where(mask, Dz + add, 0.0))
        pr = S.match(pts, est)
        got = {j for _, j in pr}
        rec.append(len(pr) / 5)
        for i, j in pr:
            vols.append(float((est[j, 2] - q) / q))
            # volume already present at that spot without the plant (real signal under the cone)
            near = np.hypot(base[:, 0] - est[j, 0], base[:, 1] - est[j, 1]) < 1000 if len(base) else np.zeros(0, bool)
            vadj.append(float((est[j, 2] - base[near, 2].sum() - q) / q))
        fal.append(sum(1 for j in range(len(est)) if j not in got and
                       (len(base) == 0 or np.hypot(base[:, 0] - est[j, 0], base[:, 1] - est[j, 1]).min() > 1000)))
    res["detect"][q] = dict(recall=float(np.mean(rec)), n_cones=5 * NTR, new_false=float(np.mean(fal)),
                            med_vol_err=float(np.median(vols)) if vols else None,
                            med_abs_vol_err=float(np.median(np.abs(vols))) if vols else None,
                            med_abs_vol_err_baseadj=float(np.median(np.abs(vadj))) if vadj else None)
    print("detect", q, json.dumps(res["detect"][q]), f"{time.time() - t0:.0f}s", flush=True)
    json.dump(res, open(OUTP, "w"), indent=1)
print("done")
