"""Arizona level-1 validation against metered pumping (pre-registered design: az_prereg.md).

Usage: python az_validate.py [--B 1500 --rw 2000]
"""
import sys, json
import numpy as np
import pandas as pd
from scipy import ndimage, stats
from scipy.signal import fftconvolve
import synth as S

A = "C:/Kuliah/hackathon/agc-26/realdata/arizona"
arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
B, RW, THR, NMS = arg("--B", 1500.0), arg("--rw", 2000.0), 60.0, 1000.0
AF = 1.23348                                            # acre-ft/yr -> thousand m3/yr
z = np.load(f"{A}/opera_rate_200m.npz", allow_pickle=True)
D, mask = z["D"].astype(float), z["mask"].astype(bool) & np.isfinite(z["D"])
E0, N0, PIX = float(z["E0"]), float(z["N0"]), float(z["PIX"])
NY, NX = D.shape
XX, YY = np.meshgrid((np.arange(NX) + .5) * PIX, (np.arange(NY) + .5) * PIX)

# ---- detector: cubic background removed, then local matched filter ------------------------------
u, v = XX / XX.max() - .5, YY / YY.max() - .5
P = np.stack([u ** i * v ** j for i in range(4) for j in range(4 - i)], -1)
beta = np.linalg.lstsq(P[mask], D[mask], rcond=None)[0]
r0 = np.where(mask, D - P @ beta, 0.0)
n = int(RW // PIX)
yy, xx = np.mgrid[-n:n + 1, -n:n + 1] * PIX
disc = (np.hypot(xx, yy) <= RW).astype(float)
bu, bv = xx / RW, yy / RW
basis = [S.kern(np.hypot(xx, yy), "k0", B) * disc] + [b * disc for b in (1, bu, bv, bu * bu, bv * bv, bu * bv)]
conv = lambda a, k: fftconvolve(a, k[::-1, ::-1], mode="same")
m = mask.astype(float)
nb = len(basis)
NM = np.empty((NY, NX, nb, nb))
for i in range(nb):
    for j in range(i, nb):
        NM[..., i, j] = NM[..., j, i] = conv(m, basis[i] * basis[j])
NM += np.eye(nb) * 1e-9
rhs = np.stack([conv(r0, b) for b in basis], -1)
qmap = np.linalg.solve(NM, rhs[..., None])[..., 0, 0]
ok = mask & (conv(m, disc) / disc.sum() >= 0.5)
q = np.where(ok, qmap, -np.inf)
k = int(NMS // PIX) * 2 + 1
iy, ix = np.nonzero((q == ndimage.maximum_filter(q, size=k)) & (q > THR))
det = np.c_[XX[iy, ix], YY[iy, ix], q[iy, ix]]

# ---- truth ---------------------------------------------------------------------------------------
w = pd.read_csv(f"{A}/pump_all.csv", dtype={"REGISTRY_ID": str})
yrs = [str(y) for y in range(2016, 2021)]
w["q"] = w[yrs].fillna(0).mean(1) * AF
sb = {}
for name in ("ELOY", "MARICOPA-STANFIELD", "EAST_SALT_RIVER_VALLEY"):
    for f in json.load(open(f"{A}/pumpwells_{name}.json"))["features"]:
        sb[f["attributes"]["REGISTRY_ID"]] = name
w["sub"] = w["REGISTRY_ID"].map(sb)
w["x"], w["y"] = w["UTM_X_METERS"] - E0, w["UTM_Y_METERS"] - N0
w = w[(w.q > 0) & w.x.between(0, NX * PIX) & w.y.between(0, NY * PIX)]
WX, WQ = w[["x", "y"]].to_numpy(), w.q.to_numpy()


def pump_within(pts, rad=2000.0):
    d = np.hypot(pts[:, None, 0] - WX[None, :, 0], pts[:, None, 1] - WX[None, :, 1])
    return (WQ[None, :] * (d <= rad)).sum(1)


res = dict(B=B, rw=RW, n_det=int(len(det)), n_wells=int(len(w)), pumped_total=float(WQ.sum()),
           period="2016-2020 pumping vs 2016-08..2021-03 InSAR")

# T1 location
hit = pump_within(det[:, :2]) >= 1000 if len(det) else np.zeros(0, bool)
cells = np.flatnonzero(ok.ravel())
rng = np.random.default_rng(0)
Dpos = np.clip(np.nan_to_num(D), 0, None).ravel()[cells] + 1e-6
nulls = {}
for nm, p in (("uniform", None), ("rate_weighted", Dpos / Dpos.sum())):
    sims = []
    for _ in range(4000):
        c = rng.choice(cells, len(det), p=p)
        sims.append(np.mean(pump_within(np.c_[XX.ravel()[c], YY.ravel()[c]]) >= 1000))
    sims = np.array(sims)
    nulls[nm] = dict(mean=float(sims.mean()), p=float((sims >= hit.mean()).mean()))
res["T1"] = dict(hit_rate=float(hit.mean()) if len(det) else None, nulls=nulls)

# T2 map correlation with pumping-predicted subsidence
def predicted(off=(0.0, 0.0), Bp=1500.0):
    g = np.zeros((NY, NX))
    gx = ((WX[:, 0] + off[0]) % (NX * PIX) // PIX).astype(int)
    gy = ((WX[:, 1] + off[1]) % (NY * PIX) // PIX).astype(int)
    np.add.at(g, (gy, gx), WQ)
    nk = int(4 * Bp // PIX)
    ky, kx = np.mgrid[-nk:nk + 1, -nk:nk + 1] * PIX
    return fftconvolve(g, S.kern(np.hypot(kx, ky), "k0", Bp), mode="same")


res["T2"] = {}
for Bp in (1500.0, 3000.0):
    obs = stats.spearmanr(predicted(Bp=Bp)[mask], D[mask])[0]
    sims = []
    for _ in range(500):
        off = rng.uniform(5000, [NX * PIX - 5000, NY * PIX - 5000])
        sims.append(stats.spearmanr(predicted(off, Bp)[mask], D[mask])[0])
    res["T2"][int(Bp)] = dict(rho=float(obs), null_p95=float(np.percentile(sims, 95)),
                              null_mean=float(np.mean(sims)), p=float((np.array(sims) >= obs).mean()))

# T3 volume (calibration on Eloy + Maricopa-Stanfield, hold-out East Salt River Valley)
if len(det):
    pw = pump_within(det[:, :2])
    near = np.argmin(np.hypot(det[:, None, 0] - WX[None, :, 0], det[:, None, 1] - WX[None, :, 1]), 1)
    dsub = w["sub"].to_numpy()[near]
    use = pw > 0
    rho = stats.spearmanr(det[use, 2], pw[use])[0] if use.sum() > 2 else None
    cal = use & np.isin(dsub, ["ELOY", "MARICOPA-STANFIELD"])
    hold = use & (dsub == "EAST_SALT_RIVER_VALLEY")
    c = float(np.median(det[cal, 2] / pw[cal])) if cal.any() else None
    err = np.abs(det[hold, 2] / c - pw[hold]) / pw[hold] if (c and hold.any()) else np.array([])
    res["T3"] = dict(n_with_pumping=int(use.sum()), spearman=float(rho) if rho is not None else None,
                     calib_factor_subsidence_per_pumped=c, n_calib=int(cal.sum()), n_holdout=int(hold.sum()),
                     holdout_median_err=float(np.median(err)) if len(err) else None,
                     holdout_within_30pct=float(np.mean(err <= 0.3)) if len(err) else None)
res["detections"] = [dict(x=float(x + E0), y=float(y + N0), q=float(qq), pump_2km=float(p))
                     for (x, y, qq), p in zip(det, pump_within(det[:, :2]) if len(det) else [])]
json.dump(res, open(f"{A}/az_validate_B{int(B)}.json", "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "detections"}, indent=1))
