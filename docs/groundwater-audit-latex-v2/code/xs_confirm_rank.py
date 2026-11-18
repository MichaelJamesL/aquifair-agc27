"""Confirmation of the relative ranking (xsite_prereg.md addendum 5): demand-only index at 8 km on the
new GULF regions R3-R7 (layers built on the DGX Spark by xs_spark_run.sh, copied to realdata/<site>/).
Truth = GULF WEL 2016-18 (laptop). Writes realdata/xsite_confirm_rank.json. Usage: python xs_confirm_rank.py
"""
import json
import math
import xs_model as X
import xs_rank as K

NEW = ("r3_east", "r4_brazos", "r5_south", "r6_north", "r7_northeast")
X.GULF = X.GULF + NEW                                   # GNSS tie where >= 5 stations, as for R2
out = {}
for site in NEW:
    out[site] = {}
    for blk, k, km in ((4000.0, 1, 4), (4000.0, 2, 8)):
        X.BLK = blk
        f = K.kept(X.houston(site), 16.0)
        idx = K.index(f)
        g = f.assign(**idx).assign(cx=f.bx // k, cy=f.by // k).groupby(["cx", "cy"])[["Q", *idx]].sum()
        out[site][f"{km}km"] = dict(cells=len(g), total_Mm3=round(float(g.Q.sum() / 1e3), 1),
                                    **{m: K.scores(g.Q.values, g[m].values) for m in idx})
        print(site, km, "km", out[site][f"{km}km"])
elig = [s for s in NEW if out[s]["8km"]["cells"] >= 20 and out[s]["8km"]["total_Mm3"] >= 10]
hit = [s for s in elig if out[s]["8km"]["demand"]["spearman"] >= 0.5 and out[s]["8km"]["demand"]["top20_capture"] >= 0.4]
need = math.ceil(0.75 * len(elig))
out["verdict"] = dict(eligible=elig, passing=hit, needed=need, confirmed=len(elig) > 0 and len(hit) >= need)
json.dump(out, open(f"{X.R0}/xsite_confirm_rank.json", "w"), indent=1)
print(out["verdict"])
