"""EXPLORATORY (not pre-registered): how many local calibration areas with known pumping are needed?
At the test site, n random 4 km blocks with known pumping are revealed (plus the regional total, +-23 %).
A log-linear model log10 Q ~ log10 [subsidence, clay, built, crop*ET] is fit on those n blocks (ridge,
anchored by the other site's data at weight 1/10), turned into shares of the remaining total, and scored
on the hidden blocks at 4 / 8 / 16 / 32 km. 50 random draws per n. Also: 32 km for the top-down S-models.
Writes realdata/xsite_calcurve.json.
"""
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
import xs_model as X
import xs_share as XS

rng = np.random.default_rng(2)
L = XS.L
COLS = XS.COLS
sites = {"arizona": X.keep(X.arizona()), "houston": X.keep(X.houston())}
out = {"topdown_32km": {}, "calcurve": {}}
for a, b in (("arizona", "houston"), ("houston", "arizona")):
    tr, te = sites[a], sites[b]
    for m in XS.MODELS:
        w = XS.weights(tr, te, m)
        agg = XS.aggregate(te.assign(pred=w / w.sum() * te.Q.sum()), 8)
        ok = agg.Q > 0
        out["topdown_32km"].setdefault(f"{a}->{b}", {})[m] = dict(
            n=int(ok.sum()), med_abs_log10=round(float(np.median(np.abs(np.log10(np.maximum(agg.pred[ok], 1) / agg.Q[ok])))), 3))
    for n in (5, 10, 20, 40, 80):
        res = {k: [] for k in (1, 2, 4, 8)}
        for _ in range(50):
            cal = rng.choice(len(te), n, replace=False)
            c, h = te.iloc[cal], te.drop(te.index[cal])
            fit = pd.concat([c, tr])
            sw = np.r_[np.ones(len(c)), np.full(len(tr), 0.1)]
            mu, sd = L(fit[COLS]).mean(0), L(fit[COLS]).std(0) + 1e-9
            mdl = Ridge(alpha=1.0).fit((L(fit[COLS]) - mu) / sd, np.log10(fit.Q + 10), sample_weight=sw)
            wgt = np.clip(10 ** mdl.predict((L(h[COLS]) - mu) / sd) - 10, 0, None)
            rest = te.Q.sum() * rng.uniform(0.77, 1.23) - c.Q.sum()
            d = h.assign(pred=wgt / max(wgt.sum(), 1e-9) * max(rest, 0))
            for k in res:
                agg = XS.aggregate(d, k)
                ok = agg.Q > 0
                res[k].append(np.median(np.abs(np.log10(np.maximum(agg.pred[ok], 1) / agg.Q[ok]))))
        out["calcurve"].setdefault(f"{a}->{b}", {})[n] = {f"{4 * k}km": round(float(np.median(v)), 3) for k, v in res.items()}
json.dump(out, open(f"{X.R0}/xsite_calcurve.json", "w"), indent=1)
print(json.dumps(out, indent=1))
