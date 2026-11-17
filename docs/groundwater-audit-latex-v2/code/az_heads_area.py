"""Arizona T5 (subsidence vs water-level trends) and T6 (sinking areas + pumped-volume ranges),
pre-registered in az_prereg.md (addendum 2). Water levels: ADWR GWSI exports wl_*.xls."""
import glob, json
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from scipy import ndimage, stats
from pyproj import Transformer

A = "C:/Kuliah/hackathon/agc-26/realdata/arizona"
NS = "{urn:schemas-microsoft-com:office:spreadsheet}"
AF, FT = 1.23348, 0.3048


def read_xml(path):
    rows, head = [], None
    for _, el in ET.iterparse(path):
        if el.tag == NS + "Row":
            vals = [(c.find(NS + "Data").text if c.find(NS + "Data") is not None else None) for c in el.findall(NS + "Cell")]
            if head is None:
                head = vals
            else:
                rows.append(vals[:len(head)])
            el.clear()
    return pd.DataFrame(rows, columns=head)


wl = pd.concat([read_xml(f) for f in sorted(glob.glob(f"{A}/heads/wl_*.xls"))], ignore_index=True)
wl["t"] = pd.to_datetime(wl["WLWA_MEASUREMENT_DATE"], errors="coerce")
wl["dtw"] = pd.to_numeric(wl["WLWA_DEPTH_TO_WATER"], errors="coerce") * FT
wl = wl[wl.t.between("2016-08-01", "2021-03-31") & wl.dtw.notna() & wl["WLWA_REMARK_CODE"].isna()]
sid = wl["WLWA_SITE_WELL_SITE_ID"].astype(str)
# GWSI site id = DDMMSS (lat) DDDMMSS (lon, west) + 2-digit sequence
wl["lat"] = sid.str[0:2].astype(float) + sid.str[2:4].astype(float) / 60 + sid.str[4:6].astype(float) / 3600
wl["lon"] = -(sid.str[6:9].astype(float) + sid.str[9:11].astype(float) / 60 + sid.str[11:13].astype(float) / 3600)

trend = []
for s, g in wl.groupby("WLWA_SITE_WELL_SITE_ID"):
    yrs = (g.t - pd.Timestamp("2016-01-01")).dt.days / 365.25
    if len(g) >= 3 and yrs.max() - yrs.min() >= 3:
        sl = stats.theilslopes(g.dtw, yrs)[0]                     # m/yr, + = water table falling
        trend.append((s, g.lon.iat[0], g.lat.iat[0], sl, len(g)))
tr = pd.DataFrame(trend, columns=["site", "lon", "lat", "decline_m_yr", "n"])

z = np.load(f"{A}/opera_rate_200m.npz", allow_pickle=True)
D, mask = z["D"].astype(float), z["mask"].astype(bool) & np.isfinite(z["D"])
E0, N0, PIX = float(z["E0"]), float(z["N0"]), float(z["PIX"])
NY, NX = D.shape
fw = Transformer.from_crs(4267, 32612, always_xy=True)                # GWSI coordinates are NAD27
ex, ny_ = fw.transform(tr.lon.values, tr.lat.values)
tr["ix"], tr["iy"] = ((ex - E0) // PIX).astype(int), ((ny_ - N0) // PIX).astype(int)
tr = tr[tr.ix.between(1, NX - 2) & tr.iy.between(1, NY - 2)]
Dm = np.where(mask, D, np.nan)
Ds = ndimage.generic_filter(np.nan_to_num(Dm, nan=0), np.mean, size=3)
cnt = ndimage.uniform_filter(mask.astype(float), 3)
Dloc = np.where(cnt > 0.3, ndimage.uniform_filter(np.nan_to_num(Dm), 3) / np.maximum(cnt, 1e-9), np.nan)
tr["sub"] = Dloc[tr.iy, tr.ix]
tr = tr[np.isfinite(tr["sub"])]
res = dict(n_wells_with_trend=int(len(tr)), decline_pct=np.percentile(tr.decline_m_yr, [10, 50, 90]).round(2).tolist(),
           share_rising=float((tr.decline_m_yr < 0).mean()))
rho = stats.spearmanr(tr["sub"], tr.decline_m_yr)[0]
rng = np.random.default_rng(0)
sims = []
for _ in range(1000):
    dy, dx = rng.integers(25, NY - 25), rng.integers(25, NX - 25)
    v = np.roll(np.roll(Dloc, dy, 0), dx, 1)[tr.iy, tr.ix]
    ok = np.isfinite(v)
    sims.append(stats.spearmanr(v[ok], tr.decline_m_yr.values[ok])[0])
sims = np.array(sims)
res["T5a"] = dict(rho=float(rho), null_p95=float(np.nanpercentile(sims, 95)), p=float(np.nanmean(sims >= rho)))

# T6 sinking areas
lab, n = ndimage.label(mask & (D > 10))
areas = []
w = pd.read_csv(f"{A}/pump_all.csv", dtype={"REGISTRY_ID": str})
w["q"] = w[[str(y) for y in range(2016, 2021)]].fillna(0).mean(1) * AF
w = w[w.q > 0]
wx, wy = ((w.UTM_X_METERS - E0) // PIX).astype(int).to_numpy(), ((w.UTM_Y_METERS - N0) // PIX).astype(int).to_numpy()
inb = (wx >= 0) & (wx < NX) & (wy >= 0) & (wy < NY)
wq = w.q.to_numpy()
tri, trj = tr.iy.to_numpy(), tr.ix.to_numpy()
for k in range(1, n + 1):
    reg = lab == k
    if reg.sum() * PIX * PIX < 1e6:
        continue
    V = float(D[reg].sum() * PIX * PIX / 1e6)                  # thousand m3/yr subsidence volume
    buf = ndimage.distance_transform_edt(~reg) * PIX <= 2000
    truth = float(wq[inb][buf[wy[inb], wx[inb]]].sum())
    near = np.hypot(tri[:, None] - np.argwhere(reg)[None, ::50, 0], trj[:, None] - np.argwhere(reg)[None, ::50, 1]).min(1)
    rising = float(np.mean(tr.decline_m_yr.values[near * PIX <= 2000] < 0)) if (near * PIX <= 2000).any() else None
    areas.append(dict(area_km2=round(float(reg.sum() * PIX * PIX / 1e6), 1), subs_volume=round(V, 0),
                      range_lo=round(V / 0.6, 0), range_hi=round(V / 0.03, 0), metered=round(truth, 0),
                      inside=bool(V / 0.6 <= truth <= V / 0.03) if truth > 0 else None,
                      c_implied=round(V / truth, 3) if truth > 0 else None, heads_rising_share=rising))
ar = pd.DataFrame(areas)
has = ar[ar.metered > 0]
res["T6"] = dict(n_areas=int(len(ar)), n_with_metered_pumping=int(len(has)),
                 coverage=float(has.inside.mean()) if len(has) else None,
                 c_implied_pct=np.percentile(has.c_implied, [10, 50, 90]).round(3).tolist() if len(has) else None,
                 share_of_metered_volume_near_areas=float(has.metered.sum() / wq[inb].sum()),
                 areas_rising_heads_majority=int((ar.heads_rising_share > 0.5).sum()))
res["T5b"] = dict(sinking_area_share_with_rising_heads=float(np.average(
    ar.heads_rising_share.fillna(0) > 0.5, weights=ar.area_km2)) if len(ar) else None)
ar.to_csv(f"{A}/az_areas.csv", index=False)
tr.to_csv(f"{A}/az_head_trends.csv", index=False)
json.dump(res, open(f"{A}/az_heads_area.json", "w"), indent=1)
print(json.dumps(res, indent=1))
print(ar.sort_values("subs_volume", ascending=False).head(12).to_string())
