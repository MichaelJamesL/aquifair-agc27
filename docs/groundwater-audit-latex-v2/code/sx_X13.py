"""X13 (stage 2): attribution. Grouped Shapley split of block-CV R2 of the sinking map into cause groups, using the
driver features saved by X01-X12 (observations of the deformation itself are excluded) (sx_prereg.md)."""
import glob
import itertools
import json
import os
from scipy import ndimage
from math import factorial
import numpy as np
import sx_common as C

TARGET = os.environ.get("TARGET", "da1822")
feats, group = {}, {}
pat = "feat_X*.npz" if TARGET == "da1822" else "feat_[XL]*.npz"     # pre-registered run: X01-X12 features only
for f in sorted(glob.glob(f"{C.OUT}/{pat}")):
    z = np.load(f)
    gm = json.loads(str(z["_groups"]))
    for k in z.files:
        if k != "_groups" and gm.get(k) in ("soil", "load", "pumping", "tectonic"):
            if np.isfinite(z[k][C.LAND]).mean() > 0.2:
                feats[k], group[k] = z[k], gm[k]
groups = sorted(set(group.values()))
# target variants (stage 2 runs several in parallel): TARGET=da1822 (pre-registered) | d1517 | d2326 | alos |
# regional (Gaussian 1.5 km smooth) | local (T - regional) | strain (T / soft thickness from L3)
if TARGET in ("da1822", "withL"):
    tgt = C.T
elif TARGET in ("d1517", "d2326"):
    tgt = C.B[f"D_{TARGET}"].astype(float)
elif TARGET == "alos":
    tgt = C.B["D_alos"].astype(float)
else:
    fill = np.where(C.LAND, C.T, np.nanmean(C.T[C.LAND]))
    w = ndimage.gaussian_filter(C.LAND.astype(float), 7.5)
    reg = ndimage.gaussian_filter(fill * C.LAND, 7.5) / np.maximum(w, 1e-6)
    tgt = {"regional": reg, "local": C.T - reg}.get(TARGET)
    if TARGET == "strain":
        thk = np.load(f"{C.OUT}/feat_L3.npz")["lo2022_soft_thickness"]
        tgt = np.where(thk >= 20, C.T / thk, np.nan)               # mm/yr per m of soft sediment
        feats.pop("lo2022_soft_thickness", None)
m = C.LAND & np.isfinite(tgt)
y = tgt[m]
BK = int(os.environ.get("BLOCK_KM", "2"))                         # 2 = pre-registered; 8 = added after X20 (location check)
nb = BK * 1000 // int(C.PIX)
BLK = ((C.IY // nb) * (C.NX // nb + 1) + C.IX // nb)[m]
cols = {g: [k for k in feats if group.get(k) == g] for g in groups}
cache = {}


def r2(sub):
    key = tuple(sorted(sub))
    if key not in cache:
        ks = [k for g in key for k in cols[g]]
        cache[key] = 0.0 if not ks else C.block_cv_r2(np.c_[[feats[k][m] for k in ks]].T, y, BLK)
    return cache[key]


n = len(groups)
shap = {}
for g in groups:
    others = [h for h in groups if h != g]
    v = 0.0
    for k in range(n):
        for S in itertools.combinations(others, k):
            w = factorial(k) * factorial(n - k - 1) / factorial(n)
            v += w * (r2(S + (g,)) - r2(S))
    shap[g] = v
full = r2(tuple(groups))
# permutation importance of single features in the full model (fit on all, scored on held-out blocks)
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score
ks = [k for g in groups for k in cols[g]]
X = np.c_[[feats[k][m] for k in ks]].T
blk = BLK
test = np.isin(blk, np.random.default_rng(1).choice(np.unique(blk), len(np.unique(blk)) // 4, replace=False))
mdl = HistGradientBoostingRegressor(max_iter=200, random_state=0).fit(X[~test], y[~test])
base = r2_score(y[test], mdl.predict(X[test]))
imp = {}
for j, k in enumerate(ks):
    Xp = X[test].copy()
    Xp[:, j] = np.random.default_rng(j).permutation(Xp[:, j])
    imp[k] = dict(group=group[k], drop_r2=float(base - r2_score(y[test], mdl.predict(Xp))))
res = dict(groups=cols, cv_r2_full=full, shapley_r2=shap, subset_r2={"+".join(k) or "none": v for k, v in cache.items()},
           single_group_r2={g: r2((g,)) for g in groups}, holdout_r2=base,
           permutation_importance=dict(sorted(imp.items(), key=lambda kv: -kv[1]["drop_r2"])))
res["target"] = TARGET
res["n_cells"] = int(m.sum())
res["block_km"] = BK
C.save(("X13" if TARGET == "da1822" else f"X13_{TARGET}") + ("" if BK == 2 else f"_{BK}km"), res)
