"""Can pumping volume per area be PREDICTED (with a range) from transferable data types?
Arizona, 4 km blocks, truth = ADWR metered pumping 2016-2020. Region hold-out (SOUTH <-> ESRV)
and within-region spatial CV. Models:
  baseline : regional mean per block
  physics  : Q = a * crop_area*ET + b * built_area   (non-negative LS; demand formula)
  ml_all   : gradient boosting (quantile 10/50/90) on InSAR + heads + land cover + ET
  ml_noinsar / ml_insar_only : ablations
Usage: python az_model.py [--block 4000]
"""
import sys, json
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import nnls
from sklearn.ensemble import HistGradientBoostingRegressor

A = "C:/Kuliah/hackathon/agc-26/realdata/arizona"
AF = 1.23348
BLK = float(sys.argv[sys.argv.index("--block") + 1]) if "--block" in sys.argv else 4000.0
z = np.load(f"{A}/opera_rate_200m.npz", allow_pickle=True)
D, mask = z["D"].astype(float), z["mask"].astype(bool) & np.isfinite(z["D"])
amp = np.nan_to_num(z["seasonal_amp_los"].astype(float))
E0, N0, PIX = float(z["E0"]), float(z["N0"]), float(z["PIX"])
NY, NX = D.shape
F = np.load(f"{A}/features_200m.npz")
ET = np.nan_to_num(np.load(f"{A}/et_200m.npz")["et_mm"].astype(float))
BL = int(BLK // PIX)
by, bx = np.arange(NY) // BL, np.arange(NX) // BL
nbx = bx.max() + 1
bid = (by[:, None] * nbx + bx[None, :]).ravel()
nb = bid.max() + 1
cell_km2 = PIX * PIX / 1e6
S = lambda a: np.bincount(bid, np.asarray(a, float).ravel(), minlength=nb)
nvalid = S(mask)
f = pd.DataFrame(dict(
    sub_vol=S(np.clip(D, 0, None) * mask) * cell_km2,               # thousand m3/yr
    sub_mean=S(D * mask) / np.maximum(nvalid, 1),
    sub_p90=[0.0] * nb,
    seas_amp=S(amp * mask) / np.maximum(nvalid, 1),
    crop_km2=S(F["wc_crop"]) * cell_km2, built_km2=S(F["wc_built"]) * cell_km2,
    bare_frac=S(F["wc_bare"]) / BL ** 2, shrub_frac=S(F["wc_shrub"]) / BL ** 2,
    et_mean=S(ET) / BL ** 2, irr_demand=S(F["wc_crop"] * ET) * cell_km2,  # thousand m3/yr (mm x km2)
    valid_frac=nvalid / BL ** 2))
Dm = np.where(mask, D, np.nan).ravel()
for b in np.unique(bid):
    v = Dm[bid == b]
    v = v[np.isfinite(v)]
    f.loc[b, "sub_p90"] = np.percentile(v, 90) if len(v) else 0.0
# heads (IDW 10 km)
tr = pd.read_csv(f"{A}/az_head_trends.csv")
cy, cx = (np.arange(by.max() + 1) + .5) * BL, (np.arange(nbx) + .5) * BL
CY, CX = np.meshgrid(cy, cx, indexing="ij")
dd = np.hypot(CY.ravel()[:, None] - tr.iy.values[None], CX.ravel()[:, None] - tr.ix.values[None]) * PIX
wgt = np.where(dd <= 10000, 1 / np.maximum(dd, 500) ** 2, 0)
f["head_decline"] = np.where(wgt.sum(1) > 0, (wgt @ tr.decline_m_yr.values) / np.maximum(wgt.sum(1), 1e-12), np.nan)

w = pd.read_csv(f"{A}/pump_all.csv", dtype={"REGISTRY_ID": str})
w["q"] = w[[str(y) for y in range(2016, 2021)]].fillna(0).mean(1) * AF
sb = {}
for name in ("ELOY", "MARICOPA-STANFIELD", "EAST_SALT_RIVER_VALLEY"):
    for ft in json.load(open(f"{A}/pumpwells_{name}.json"))["features"]:
        sb[ft["attributes"]["REGISTRY_ID"]] = name
w["sub"] = w.REGISTRY_ID.map(sb)
w = w[w.q > 0]
gx, gy = ((w.UTM_X_METERS - E0) // PIX).astype(int), ((w.UTM_Y_METERS - N0) // PIX).astype(int)
ok = gx.between(0, NX - 1) & gy.between(0, NY - 1)
w, gx, gy = w[ok], gx[ok], gy[ok]
wb = bid.reshape(NY, NX)[gy.values, gx.values]
Q = np.bincount(wb, w.q.values, minlength=nb)
# region of every block = majority sub-basin of wells within 8 km (blocks without wells too)
wbx, wby = gx.values * PIX, gy.values * PIX
reg_w = np.where(pd.Series(w["sub"].values).isin(["ELOY", "MARICOPA-STANFIELD"]), "SOUTH",
                 np.where(w["sub"].values == "EAST_SALT_RIVER_VALLEY", "ESRV", None))
bcx, bcy = (CX.ravel() + .5) * PIX, (CY.ravel() + .5) * PIX
region = np.full(nb, None, dtype=object)
for b in range(nb):
    dist = np.hypot(wbx - bcx[b], wby - bcy[b])
    near = (dist < 8000) & (reg_w != None)
    if near.any():
        region[b] = pd.Series(reg_w[near]).mode().iat[0]
f["Q"], f["region"] = Q, region
units = f[(f.valid_frac >= 0.25) & f.head_decline.notna() & f.region.notna() &
          ((f.Q > 0) | (f.sub_mean > 5) | (f.crop_km2 > 1) | (f.built_km2 > 2))].copy()
units["y"] = np.log10(units.Q + 10)                          # 10 thousand m3/yr floor

INSAR = ["sub_vol", "sub_mean", "sub_p90", "seas_amp"]
OTHER = ["head_decline", "crop_km2", "built_km2", "bare_frac", "shrub_frac", "et_mean", "irr_demand"]
SETS = {"ml_all": INSAR + OTHER, "ml_noinsar": OTHER, "ml_insar_only": INSAR + ["head_decline"]}


def score(y_true_q, pred_q, lo_q=None, hi_q=None):
    ok = y_true_q > 0
    lr = np.log10(np.maximum(pred_q[ok], 1) / y_true_q[ok])
    out = dict(n=int(len(y_true_q)), spearman=float(stats.spearmanr(pred_q, y_true_q)[0]),
               med_abs_log10=float(np.median(np.abs(lr))),
               within_x3=float(np.mean(np.abs(lr) <= np.log10(3))),
               total_err=float(pred_q.sum() / y_true_q.sum() - 1))
    if lo_q is not None:
        out["coverage80"] = float(np.mean((y_true_q >= lo_q) & (y_true_q <= hi_q)))
        out["median_range_factor"] = float(np.median(np.maximum(hi_q, 1) / np.maximum(lo_q, 1)))
    return out


def fit_predict(tr_, te_, name):
    if name == "baseline":
        m = tr_.Q.mean()
        lo, hi = np.percentile(tr_.Q, [10, 90])
        return np.full(len(te_), m), np.full(len(te_), lo), np.full(len(te_), hi)
    if name == "physics":
        Xa = tr_[["irr_demand", "built_km2"]].to_numpy()
        coef, _ = nnls(Xa, tr_.Q.to_numpy())
        p_tr = Xa @ coef
        r = np.log10((tr_.Q + 10) / (p_tr + 10))
        lo, hi = np.percentile(r, [10, 90])
        p = te_[["irr_demand", "built_km2"]].to_numpy() @ coef
        return p, (p + 10) * 10 ** lo - 10, (p + 10) * 10 ** hi - 10
    cols = SETS[name]
    preds = []
    for a in (0.1, 0.5, 0.9):
        m = HistGradientBoostingRegressor(loss="quantile", quantile=a, max_depth=3, max_iter=300,
                                          learning_rate=0.05, min_samples_leaf=10, random_state=0)
        m.fit(tr_[cols], tr_.y)
        preds.append(10 ** m.predict(te_[cols]) - 10)
    return np.clip(preds[1], 0, None), np.clip(preds[0], 0, None), np.clip(preds[2], 0, None)


MODELS = ["baseline", "physics", "ml_all", "ml_noinsar", "ml_insar_only"]
res = dict(block_m=BLK, n_units=int(len(units)), by_region=units.region.value_counts().to_dict(), region_holdout={}, spatial_cv={})
for cal, hold in (("SOUTH", "ESRV"), ("ESRV", "SOUTH")):
    tr_, te_ = units[units.region == cal], units[units.region == hold]
    res["region_holdout"][f"{cal}->{hold}"] = {m: score(te_.Q.to_numpy(), *fit_predict(tr_, te_, m)) for m in MODELS}
# within-region spatial CV: 16 km super-blocks, 5 folds (the case "some local training data")
sbk = ((CY.ravel() * PIX) // 16000).astype(int) * 100 + ((CX.ravel() * PIX) // 16000).astype(int)
units["fold"] = pd.Series(sbk[units.index]).rank(method="dense").astype(int).values % 5
for m in MODELS:
    P, L, H = np.zeros(len(units)), np.zeros(len(units)), np.zeros(len(units))
    for k in range(5):
        trm, tem = units.fold != k, units.fold == k
        p, l, h = fit_predict(units[trm], units[tem], m)
        P[tem.values], L[tem.values], H[tem.values] = p, l, h
    res["spatial_cv"][m] = score(units.Q.to_numpy(), P, L, H)
json.dump(res, open(f"{A}/az_model_{int(BLK)}.json", "w"), indent=1)
rows = []
for split, d in list(res["region_holdout"].items()) + [("spatialCV", res["spatial_cv"])]:
    for m, s in d.items():
        rows.append(dict(split=split, model=m, **{k: round(v, 2) if isinstance(v, float) else v for k, v in s.items()}))
print(json.dumps({k: v for k, v in res.items() if k in ("block_m", "n_units", "by_region")}))
print(pd.DataFrame(rows).to_string(index=False))
