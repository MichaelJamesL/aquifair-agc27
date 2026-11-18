"""Apply the validated split (xsite_prereg.md addendum 3, passed in xs_confirm.py) to Semarang.
Kota Semarang cells of the 24 x 16 km grid share the city groundwater total (38-61 Mm3/yr, uniform) by
S5 = sqrt(demand x subsidence volume) per 4 km block, summed to 16 km cells (the validated scale).
Subsidence is reduced by the natural-compaction share for Kota Semarang (0-9 %, Sarah et al. 2020).
Ranges: total draw x a per-cell error drawn from the confirmatory regions' errors, weighted by true volume.
8 km and 4 km numbers are also written but are NOT validated (Houston 8 km error ~ factor 2.3).
Writes realdata/semarang/exp/sem_areas/xsite_semarang_split.json + .geojson.
"""
import json
import numpy as np
import pandas as pd
from matplotlib.path import Path
import synth as S
import real_goal_maps as GM
import xs_model as X

rng = np.random.default_rng(4)
R0 = X.R0
conf = json.load(open(f"{R0}/xsite_confirm.json"))
a_built, b_irr = conf["demand_coef"]
err = np.concatenate([r["S5"]["log10_pred_over_true"] for r in conf["regions"].values()])
werr = np.concatenate([r["S5"]["true_kt"] for r in conf["regions"].values()])
werr = werr / werr.sum()

D, mask, H, _ = GM.load("da", "1822")
wc = np.load(f"{R0}/semarang/worldcover_grid.npz")
ET = np.nan_to_num(np.load(f"{R0}/semarang/et_200m.npz")["et_mm"].astype(float))
lon, lat = GM.grid.inv.transform(S.XX + GM.grid.E0, S.YY + GM.grid.N0)
kota = np.zeros(S.XX.shape, bool)
for f in json.load(open(f"{R0}/semarang/admin/idn_adm2.geojson"))["features"]:
    if f["properties"]["shapeName"] == "Kota Semarang":
        g = f["geometry"]
        for p in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
            kota |= Path(np.array(p[0])).contains_points(np.c_[lon.ravel(), lat.ravel()]).reshape(lon.shape)

BL = int(X.BLK // S.PIX)
nbx = (S.NX - 1) // BL + 1
bid = (np.arange(S.NY)[:, None] // BL) * nbx + np.arange(S.NX)[None, :] // BL
nb = bid.max() + 1
Sum = lambda a: np.bincount(bid.ravel(), np.asarray(a, float).ravel(), minlength=nb)
ck = S.PIX ** 2 / 1e6
km, cm = kota, kota & mask
area = Sum(km) * ck
dem = a_built * Sum(wc["built"] * km) * ck + b_irr * Sum(wc["crop"] * ET * km) * ck
pos = Sum(np.where(cm, np.clip(np.nan_to_num(D), 0, None), 0)) / np.maximum(Sum(cm), 1)   # mean + sinking, mm/yr
blk = pd.DataFrame(dict(bx=np.arange(nb) % nbx, by=np.arange(nb) // nbx, area_km2=area, demand_kt=dem,
                        sinking_mm=pos, coherent_frac=Sum(cm) / np.maximum(Sum(km), 1)))
blk = blk[blk.area_km2 > 0]

sims = {k: [] for k in (1, 2, 4)}
for _ in range(4000):
    nat = rng.uniform(0, 0.09)
    sub = blk.sinking_mm * (1 - nat) * blk.area_km2                 # thousand m3/yr
    w = np.sqrt(np.maximum(blk.demand_kt, 0) * sub)
    tot = rng.uniform(38, 61) * 1e3                                 # thousand m3/yr
    pred = w / w.sum() * tot
    for k in sims:
        agg = blk.assign(p=pred).assign(cx=blk.bx // k, cy=blk.by // k).groupby(["cx", "cy"]).p.sum()
        # true = pred / 10**err (err = log10(pred/true) seen on the unseen regions, volume-weighted draw),
        # then rescaled so the cells still add up to the known total
        t = agg / 10 ** rng.choice(err, len(agg), p=werr)
        sims[k].append(t * tot / t.sum())
out = dict(method="S5 split of the city total, validated at 16 km (xsite_prereg.md addendum 3)",
           city_total_Mm3=[38, 61], demand_coef=[a_built, b_irr], cells={})
feats = []
for k, km_ in ((4, 16), (2, 8), (1, 4)):
    df = pd.concat(sims[k], axis=1)
    q = np.percentile(df.values, [10, 50, 90], axis=1) / 1e3
    rows = []
    for i, (cx, cy) in enumerate(df.index):
        sel = blk[(blk.bx // k == cx) & (blk.by // k == cy)]
        x0, y0 = cx * k * BL * S.PIX, cy * k * BL * S.PIX
        x1, y1 = min(x0 + k * X.BLK, S.NX * S.PIX), min(y0 + k * X.BLK, S.NY * S.PIX)
        ring = [list(GM.grid.inv.transform(GM.grid.E0 + a, GM.grid.N0 + b)) for a, b in
                ((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0))]
        props = dict(scale_km=km_, validated=km_ == 16, kota_area_km2=round(float(sel.area_km2.sum()), 1),
                     pump_p10=round(q[0, i], 1), pump_p50=round(q[1, i], 1), pump_p90=round(q[2, i], 1),
                     mean_sinking_mm=round(float(np.average(sel.sinking_mm, weights=sel.area_km2)), 1))
        rows.append(props)
        feats.append(dict(type="Feature", properties=props, geometry=dict(type="Polygon", coordinates=[ring])))
    out["cells"][f"{km_}km"] = rows
    print(f"{km_} km cells:", [(r["kota_area_km2"], r["pump_p10"], r["pump_p50"], r["pump_p90"]) for r in rows])
d = f"{R0}/semarang/exp/sem_areas"
json.dump(out, open(f"{d}/xsite_semarang_split.json", "w"), indent=1)
json.dump(dict(type="FeatureCollection", features=feats), open(f"{d}/xsite_semarang_split.geojson", "w"))
