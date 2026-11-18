"""Confirmatory test (xsite_prereg.md addendum 3): S5 = sqrt(demand x subsidence) with the regional total
known, on two regions never used before: R1 Arizona ESRV, R2 Texas west of Houston. 16 km cells.
Writes realdata/xsite_confirm.json. Usage: python xs_confirm.py
"""
import json
import numpy as np
from scipy.optimize import nnls
import xs_model as X
import xs_share as XS

rng = np.random.default_rng(3)


def wmed(x, w):
    o = np.argsort(x)
    return float(x[o][np.searchsorted(np.cumsum(w[o]) / w.sum(), .5)])


def other_rules(f):
    return f[(f.valid_frac >= 0.25) & ((f.Q > 0) | (f.sub_mean > 5) | (f.crop_km2 > 1) | (f.built_km2 > 2))]


train = X.pd.concat([X.keep(X.arizona()), X.keep(X.houston())])
coef, _ = nnls(train[["built_km2", "irr"]].values, train.Q.values)   # demand weights, fixed before testing
az = X.arizona()
regions = {"R1_arizona_ESRV": other_rules(az[az.clay_frac < 0.5]), "R2_texas_west": other_rules(X.houston("texas_w"))}
out = dict(demand_coef=coef.round(4).tolist(), regions={})
for name, te in regions.items():
    dem = te[["built_km2", "irr"]].values @ coef
    w = dict(S0=te.area_km2.values.astype(float), S5=np.sqrt(np.maximum(dem, 0) * te.sub_vol.values))
    res = {}
    for m, wm in w.items():
        share = wm / wm.sum()
        agg = XS.aggregate(te.assign(pred=share * te.Q.sum()), 4)
        ok = (agg.Q > 0).values
        e = np.abs(np.log10(np.maximum(agg.pred.values[ok], 1) / agg.Q.values[ok]))
        sims = np.array([XS.aggregate(te.assign(pred=share * te.Q.sum() * rng.uniform(0.77, 1.23)), 4).pred.values
                         for _ in range(200)])
        lo, hi = np.percentile(sims, [10, 90], 0)
        res[m] = dict(cells=int(ok.sum()), weighted_med_abs_log10=round(wmed(e, agg.Q.values[ok]), 3),
                      med_abs_log10=round(float(np.median(e)), 3),
                      coverage80_total_only=round(float(np.mean((agg.Q.values >= lo) & (agg.Q.values <= hi))), 2),
                      total_Mm3=round(float(te.Q.sum() / 1e3), 1))
    out["regions"][name] = res
    print(name, res)
out["pass"] = all(r["S5"]["weighted_med_abs_log10"] <= 0.30 and r["S5"]["weighted_med_abs_log10"] < r["S0"]["weighted_med_abs_log10"]
                  for r in out["regions"].values())
json.dump(out, open(f"{X.R0}/xsite_confirm.json", "w"), indent=1)
print("PASS" if out["pass"] else "FAIL", out["demand_coef"])
