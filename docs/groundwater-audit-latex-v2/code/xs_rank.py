"""Relative severity heatmap test (xsite_prereg.md addendum 4): does the index rank cells by true
pumping inside one region? Scales 2, 4, 8 km; regions R1 Arizona ESRV, R2 Texas west (+ Houston ref).
Writes realdata/xsite_rank.json. Usage: python xs_rank.py
"""
import json
import numpy as np
from scipy.stats import spearmanr
import xs_model as X

coef = json.load(open(f"{X.R0}/xsite_confirm.json"))["demand_coef"]


def kept(f, a):
    s = a / 16                                   # addendum-3 thresholds were set for 16 km2 blocks
    return f[(f.valid_frac >= 0.25) & ((f.Q > 0) | (f.sub_mean > 5) | (f.crop_km2 > s) | (f.built_km2 > 2 * s))]


def index(f):
    dem = np.maximum(f[["built_km2", "irr"]].values @ coef, 0)
    return dict(S5=np.sqrt(dem * f.sub_vol.values), demand=dem, subsidence=f.sub_vol.values)


def scores(q, w):
    r = np.argsort(np.argsort(w)) / len(w)
    t = np.argsort(np.argsort(q)) / len(q)
    top = w >= np.quantile(w, 0.8)
    return dict(spearman=round(float(spearmanr(w, q)[0]), 3),
                top20_capture=round(float(q[top].sum() / q.sum()), 3),
                quintile_within1=round(float(np.mean(np.abs(np.floor(r * 5) - np.floor(t * 5)) <= 1)), 3))


def loader(name):
    if name == "R1_arizona_ESRV":
        a = X.arizona()
        return a[a.clay_frac < 0.5]
    return X.houston("texas_w" if name == "R2_texas_west" else "houston")


out = {}
for name in ("R1_arizona_ESRV", "R2_texas_west", "houston_ref"):
    out[name] = {}
    for blk, k, km in ((2000.0, 1, 2), (4000.0, 1, 4), (4000.0, 2, 8)):
        X.BLK = blk
        f = kept(loader(name), (blk / 1e3) ** 2)
        idx = index(f)
        g = f.assign(**idx).assign(cx=f.bx // k, cy=f.by // k).groupby(["cx", "cy"])[["Q", *idx]].sum()
        out[name][f"{km}km"] = dict(cells=len(g), **{m: scores(g.Q.values, g[m].values) for m in idx})
        print(name, km, "km", out[name][f"{km}km"])
X.BLK = 4000.0
ok = {km: all(out[r][km]["S5"]["spearman"] >= 0.5 and out[r][km]["S5"]["top20_capture"] >= 0.4
              for r in ("R1_arizona_ESRV", "R2_texas_west")) for km in ("2km", "4km", "8km")}
out["useful"] = ok
json.dump(out, open(f"{X.R0}/xsite_rank.json", "w"), indent=1)
print("USEFUL:", ok)
