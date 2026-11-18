"""Top-down pumping test (xsite_prereg.md, addendum 2): the regional total is known (+-23 %, like
Semarang's 38-61 Mm3/yr); a share model trained at the other site splits it into areas.
Writes realdata/xsite_share.json. Usage: python xs_share.py
"""
import json
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import nnls
from sklearn.linear_model import Ridge
import xs_model as X

rng = np.random.default_rng(1)
L = lambda a: np.log10(np.maximum(np.asarray(a, float), 1.0))
COLS = ["sub_vol", "clay", "built_km2", "irr"]
MODELS = ["S0", "S1", "S2", "S3", "S4", "S5"]


def weights(tr, te, m):
    """Unnormalised weights for the test blocks from a model fit on the training site."""
    if m == "S0":
        return te.area_km2.values.astype(float)
    if m == "S1":
        coef, _ = nnls(tr[["built_km2", "irr"]].values, tr.Q.values)
        return te[["built_km2", "irr"]].values @ coef
    if m == "S2":
        return te.sub_vol.values.astype(float)
    if m == "S3":
        q = tr[tr.Q > 0]
        A = np.c_[np.ones(len(q)), L(q.sub_vol), L(q.clay)]
        c = np.linalg.lstsq(A, L(q.Q), rcond=None)[0]
        return 10 ** (c[1] * L(te.sub_vol) + c[2] * L(te.clay))
    if m == "S4":
        mu, sd = L(tr[COLS]).mean(0), L(tr[COLS]).std(0) + 1e-9
        mdl = Ridge(alpha=1.0).fit((L(tr[COLS]) - mu) / sd, np.log10(tr.Q + 10))
        return np.clip(10 ** mdl.predict((L(te[COLS]) - mu) / sd) - 10, 0, None)
    if m == "S5":
        return np.sqrt(np.maximum(weights(tr, te, "S1"), 0) * np.maximum(weights(tr, te, "S2"), 0))


def aggregate(df, k):
    """Sum blocks into k x k super-cells (k = 1, 2, 4 -> 4, 8, 16 km)."""
    return df.assign(cx=df.bx // k, cy=df.by // k).groupby(["cx", "cy"])[["Q", "pred"]].sum()


def train_resid(tr, m):
    """log10(true/pred) on the training site when its own total is known (share error only)."""
    w = weights(tr, tr, m)
    p = w / w.sum() * tr.Q.sum()
    q = tr.Q.values > 0
    return np.log10(tr.Q.values[q] / np.maximum(p[q], 1))


if __name__ == "__main__":
    sites = {"arizona": X.keep(X.arizona()), "houston": X.keep(X.houston())}
    out = {}
    for a, b in (("arizona", "houston"), ("houston", "arizona")):
        tr, te = sites[a], sites[b]
        for m in MODELS:
            w = weights(tr, te, m)
            share = w / w.sum()
            rs = train_resid(tr, m)
            for k, km in ((1, 4), (2, 8), (4, 16)):
                agg = aggregate(te.assign(pred=share * te.Q.sum()), k)
                ok = agg.Q > 0
                lr = np.log10(np.maximum(agg.pred[ok], 1) / agg.Q[ok])
                # 10-90 % range: total drawn in +-23 % x training-site share residuals per block, summed up
                sims = [aggregate(te.assign(pred=share * te.Q.sum() * rng.uniform(0.77, 1.23)
                                            * 10 ** rng.choice(rs, len(te))), k).pred.values for _ in range(200)]
                lo, hi = np.percentile(np.array(sims), [10, 90], 0)
                out.setdefault(f"{a}->{b}", {}).setdefault(m, {})[f"{km}km"] = dict(
                    n=int(ok.sum()), med_abs_log10=round(float(np.median(np.abs(lr))), 3),
                    within_x2=round(float(np.mean(np.abs(lr) <= np.log10(2))), 2),
                    spearman=round(float(stats.spearmanr(agg.pred, agg.Q)[0]), 2),
                    coverage80=round(float(np.mean((agg.Q.values >= lo) & (agg.Q.values <= hi))), 2))
    splits = [s for s in out]
    passing = {}
    for km in ("4km", "8km", "16km"):
        for m in MODELS:
            r = [out[s][m][km] for s in splits]
            s0 = [out[s]["S0"][km]["med_abs_log10"] for s in splits]
            if all(x["med_abs_log10"] <= 0.30 and 0.70 <= x["coverage80"] <= 0.90 for x in r) and \
                    all(x["med_abs_log10"] < y for x, y in zip(r, s0)):
                passing.setdefault(km, []).append(m)
    out["passing"] = passing
    json.dump(out, open(f"{X.R0}/xsite_share.json", "w"), indent=1)
    rows = [dict(split=s, model=m, scale=km, **v) for s in splits for m in out[s] for km, v in out[s][m].items()]
    print(pd.DataFrame(rows).sort_values(["scale", "split", "model"]).to_string(index=False))
    print("passing:", passing)
