"""Arizona T7: transferable volume-calibration methods (pre-registered, az_prereg.md addendum 3).
Uses only a regional pumping total for calibration; per-well meters only score the hold-out."""
import json
import numpy as np
import pandas as pd
from scipy import stats

A = "C:/Kuliah/hackathon/agc-26/realdata/arizona"
AF = 1.23348
z = np.load(f"{A}/opera_rate_200m.npz", allow_pickle=True)
D, mask = z["D"].astype(float), z["mask"].astype(bool) & np.isfinite(z["D"])
E0, N0, PIX = float(z["E0"]), float(z["N0"]), float(z["PIX"])
NY, NX = D.shape
BL = int(4000 // PIX)
by, bx = np.arange(NY) // BL, np.arange(NX) // BL
nbx = bx.max() + 1
bid = by[:, None] * nbx + bx[None, :]
nb = bid.max() + 1
area_km2 = np.bincount(bid.ravel(), mask.ravel(), minlength=nb) * PIX * PIX / 1e6
Vsub = np.bincount(bid.ravel(), (np.clip(D, 0, None) * mask).ravel(), minlength=nb) * PIX * PIX / 1e6
meanD = Vsub / np.maximum(area_km2, 1e-9) / 1e3                         # mm/yr over valid land

# head-decline field (IDW of GWSI trends) at block centres
tr = pd.read_csv(f"{A}/az_head_trends.csv")
cy, cx = (np.arange(by.max() + 1) + .5) * BL, (np.arange(nbx) + .5) * BL
CY, CX = np.meshgrid(cy, cx, indexing="ij")
d = np.hypot(CY.ravel()[:, None] - tr.iy.values[None], CX.ravel()[:, None] - tr.ix.values[None]) * PIX
wgt = np.where(d <= 10000, 1 / np.maximum(d, 500) ** 2, 0)
hdec = (wgt @ tr.decline_m_yr.values) / np.maximum(wgt.sum(1), 1e-12)
hdec[wgt.sum(1) == 0] = np.nan
Hdec = np.clip(hdec, 0, None) * area_km2

w = pd.read_csv(f"{A}/pump_all.csv", dtype={"REGISTRY_ID": str})
w["q"] = w[[str(y) for y in range(2016, 2021)]].fillna(0).mean(1) * AF
sb = {}
for name in ("ELOY", "MARICOPA-STANFIELD", "EAST_SALT_RIVER_VALLEY"):
    for f in json.load(open(f"{A}/pumpwells_{name}.json"))["features"]:
        sb[f["attributes"]["REGISTRY_ID"]] = name
w["sub"] = w.REGISTRY_ID.map(sb)
w = w[w.q > 0]
gx, gy = ((w.UTM_X_METERS - E0) // PIX).astype(int), ((w.UTM_Y_METERS - N0) // PIX).astype(int)
ok = gx.between(0, NX - 1) & gy.between(0, NY - 1)
w, gx, gy = w[ok], gx[ok], gy[ok]
wb = bid[gy.values, gx.values]
Q = np.bincount(wb, w.q.values, minlength=nb)
region = np.full(nb, None, dtype=object)
for b in np.unique(wb):
    region[b] = "SOUTH" if pd.Series(w["sub"].values[wb == b]).isin(["ELOY", "MARICOPA-STANFIELD"]).mean() >= 0.5 else "ESRV"
units = ((Q > 0) | (meanD > 5)) & (area_km2 >= 4) & np.isfinite(hdec) & (region != None)
pred_raw = {"C0": np.ones(nb), "C1": Vsub, "C2": Hdec, "C3": np.sqrt(Vsub * Hdec)}
res = dict(n_units=int(units.sum()), by_region={r: int((units & (region == r)).sum()) for r in ("SOUTH", "ESRV")}, splits={})
for cal_r, hold_r in (("SOUTH", "ESRV"), ("ESRV", "SOUTH")):
    cal, hold = units & (region == cal_r), units & (region == hold_r)
    out = {}
    for m, p in pred_raw.items():
        k = Q[cal].sum() / max(p[cal].sum(), 1e-12)                    # only the regional total
        pc, ph = k * p[cal], k * p[hold]
        use_c = cal & (Q > 0) & (p > 0)
        lr = np.log10(Q[use_c] / (k * p[use_c]))
        lo, hi = np.percentile(lr, [10, 90])
        use_h = hold & (Q > 0) & (p > 0)
        lrh = np.log10(Q[use_h] / (k * p[use_h]))
        out[m] = dict(spearman=float(stats.spearmanr(k * p[hold], Q[hold])[0]),
                      med_abs_log10=float(np.median(np.abs(lrh))),
                      coverage80=float(np.mean((lrh >= lo) & (lrh <= hi))),
                      range_factor=float(10 ** (hi - lo)),
                      total_err=float(ph.sum() / Q[hold].sum() - 1),
                      zero_pred_with_pumping=int((hold & (Q > 0) & (p <= 0)).sum()))
    res["splits"][f"{cal_r}->{hold_r}"] = out
json.dump(res, open(f"{A}/az_calib.json", "w"), indent=1)
print(json.dumps(res, indent=1))
