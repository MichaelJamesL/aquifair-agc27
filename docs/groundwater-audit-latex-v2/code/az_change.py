"""Arizona T4: does the change in subsidence rate follow the change in metered pumping?
(pre-registered in az_prereg.md, addendum). Inputs: opera_rate_200m_P1/_P2.npz, pump_all.csv."""
import json
import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import fftconvolve
import synth as S

A = "C:/Kuliah/hackathon/agc-26/realdata/arizona"
AF = 1.23348
p1, p2 = np.load(f"{A}/opera_rate_200m_P1.npz"), np.load(f"{A}/opera_rate_200m_P2.npz")
E0, N0, PIX = float(p1["E0"]), float(p1["N0"]), float(p1["PIX"])
mask = p1["mask"].astype(bool) & p2["mask"].astype(bool)
dD = np.where(mask, p2["D"].astype(float) - p1["D"].astype(float), 0.0)
NY, NX = dD.shape

w = pd.read_csv(f"{A}/pump_all.csv", dtype={"REGISTRY_ID": str})
w["q1"] = w[[str(y) for y in range(2016, 2021)]].fillna(0).mean(1) * AF
w["q2"] = w[[str(y) for y in range(2021, 2026)]].fillna(0).mean(1) * AF
sb = {}
for name in ("ELOY", "MARICOPA-STANFIELD", "EAST_SALT_RIVER_VALLEY"):
    for f in json.load(open(f"{A}/pumpwells_{name}.json"))["features"]:
        sb[f["attributes"]["REGISTRY_ID"]] = name
w["sub"] = w["REGISTRY_ID"].map(sb)
w["x"], w["y"] = w["UTM_X_METERS"] - E0, w["UTM_Y_METERS"] - N0
w = w[((w.q1 > 0) | (w.q2 > 0)) & w.x.between(0, NX * PIX - 1) & w.y.between(0, NY * PIX - 1)]
WX, DQ = w[["x", "y"]].to_numpy(), (w.q2 - w.q1).to_numpy()
res = dict(n_wells=int(len(w)), pump_P1=float(w.q1.sum()), pump_P2=float(w.q2.sum()),
           n_cells=int(mask.sum()), dD_pct=np.percentile(dD[mask], [5, 50, 95]).round(1).tolist())
rng = np.random.default_rng(0)


def grid_of(vals, off=(0.0, 0.0)):
    g = np.zeros((NY, NX))
    gx = ((WX[:, 0] + off[0]) % (NX * PIX) // PIX).astype(int)
    gy = ((WX[:, 1] + off[1]) % (NY * PIX) // PIX).astype(int)
    np.add.at(g, (gy, gx), vals)
    return g


def pred(off, B):
    nk = int(4 * B // PIX)
    ky, kx = np.mgrid[-nk:nk + 1, -nk:nk + 1] * PIX
    return fftconvolve(grid_of(DQ, off), S.kern(np.hypot(kx, ky), "k0", B), mode="same")


offs = [rng.uniform(5000, [NX * PIX - 5000, NY * PIX - 5000]) for _ in range(500)]
res["T4a"] = {}
for B in (1500.0, 3000.0):
    obs = stats.spearmanr(pred((0, 0), B)[mask], dD[mask])[0]
    sims = np.array([stats.spearmanr(pred(o, B)[mask], dD[mask])[0] for o in offs])
    res["T4a"][int(B)] = dict(rho=float(obs), null_p95=float(np.percentile(sims, 95)), p=float((sims >= obs).mean()))

# T4b: 3 km blocks
BL = int(3000 // PIX)
by, bx = np.arange(NY) // BL, np.arange(NX) // BL
bid = by[:, None] * (bx.max() + 1) + bx[None, :]
nb = bid.max() + 1
dV = np.bincount(bid.ravel(), (dD * mask).ravel() * PIX * PIX / 1e6, minlength=nb)   # thousand m3/yr
cov = np.bincount(bid.ravel(), mask.ravel(), minlength=nb) / BL ** 2


def block_pump(off=(0.0, 0.0)):
    q1, q2 = grid_of(w.q1.to_numpy(), off), grid_of(w.q2.to_numpy(), off)
    return np.bincount(bid.ravel(), q1.ravel(), minlength=nb), np.bincount(bid.ravel(), q2.ravel(), minlength=nb)


Q1, Q2 = block_pump()
sel = ((Q1 >= 500) | (Q2 >= 500)) & (cov >= 0.5)
dQ = Q2 - Q1
rho = stats.spearmanr(dV[sel], dQ[sel])[0]
sims = []
for o in offs:
    a, b = block_pump(o)
    s2 = ((a >= 500) | (b >= 500)) & (cov >= 0.5)
    if s2.sum() > 5:
        sims.append(stats.spearmanr(dV[s2], (b - a)[s2])[0])
sims = np.array(sims)
# block sub-basin = majority sub-basin of its wells
gx, gy = (WX[:, 0] // PIX).astype(int), (WX[:, 1] // PIX).astype(int)
wb = bid[gy, gx]
bsub = {b: pd.Series(w["sub"].to_numpy()[wb == b]).mode().iat[0] for b in np.unique(wb) if pd.notna(w["sub"].to_numpy()[wb == b]).any()}
subs = np.array([bsub.get(b, None) for b in range(nb)], dtype=object)
cal = sel & np.isin(subs, ["ELOY", "MARICOPA-STANFIELD"]) & (np.abs(dQ) > 100)
hold = sel & (subs == "EAST_SALT_RIVER_VALLEY") & (np.abs(dQ) > 100)
slope = float(np.sum(dV[cal] * dQ[cal]) / np.sum(dQ[cal] ** 2)) if cal.any() else None   # LS through origin
err = np.abs(dV[hold] / slope - dQ[hold]) / np.abs(dQ[hold]) if (slope and hold.any()) else np.array([])
res["T4b"] = dict(n_blocks=int(sel.sum()), rho=float(rho), null_p95=float(np.percentile(sims, 95)),
                  p=float((sims >= rho).mean()), slope_dsubsidence_per_dpumped=slope,
                  n_calib=int(cal.sum()), n_holdout=int(hold.sum()),
                  holdout_median_err=float(np.median(err)) if len(err) else None,
                  holdout_sign_agree=float(np.mean(np.sign(dV[hold]) == np.sign(dQ[hold]))) if hold.any() else None)
json.dump(res, open(f"{A}/az_change.json", "w"), indent=1)
print(json.dumps(res, indent=1))
