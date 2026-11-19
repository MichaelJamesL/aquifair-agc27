"""X09: tectonics. Rate steps across mapped active faults (GEM Global Active Faults), tilt and uplift on high ground,
and horizontal (east) motion from ascending + descending 2018-22 (sx_prereg.md)."""
import json
import urllib.request
import numpy as np
from scipy import ndimage
import sx_common as C

U = "https://raw.githubusercontent.com/GEMScienceTools/gem-global-active-faults/master/geojson/gem_active_faults_harmonized.geojson"
fc = json.load(urllib.request.urlopen(U, timeout=300))
lo0, la0, lo1, la1 = C.bbox_ll(20000)
near = []
for f in fc["features"]:
    g = f["geometry"]
    lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
    for ln in lines:
        a = np.array(ln)[:, :2]
        if ((a[:, 0] > lo0) & (a[:, 0] < lo1) & (a[:, 1] > la0) & (a[:, 1] < la1)).any():
            near.append((f["properties"].get("name"), f["properties"].get("slip_type"), a))
FM = np.zeros((C.NY, C.NX), bool)
for _, _, a in near:
    E, N = C.FW.transform(a[:, 0], a[:, 1])
    for p, q in zip(np.c_[E, N][:-1], np.c_[E, N][1:]):
        s = np.linspace(0, 1, max(int(np.hypot(*(q - p)) // 40), 1) + 1)[:, None]
        iy, ix = C.en_to_cell(*(p + (q - p) * s).T)
        FM[iy, ix] = True
gy, gx = np.gradient(np.where(C.LAND, C.T, np.nan), C.PIX / 1000, C.PIX / 1000)
G = np.hypot(gx, gy)                                                 # mm/yr per km


def step(M):
    near_ = C.LAND & (ndimage.distance_transform_edt(~M) * C.PIX <= 300) & np.isfinite(G)
    return np.nanmean(G[near_]) if near_.sum() >= 5 else np.nan


fault = dict(n_faults_near=len(near), names=sorted({str(n) for n, _, _ in near}), fault_cells=int(FM.sum()))
if FM.any():
    o = step(FM)
    p, ns = C.shift_p(step, FM, o)
    fault.update(mean_grad_near_fault=o, p_shift=p, null=ns, PASS=bool(p < 0.05))
hi = C.LAND & (C.H > 30)
A = np.c_[np.ones(hi.sum()), C.XX[hi] / 1000, C.YY[hi] / 1000]
coef = np.linalg.lstsq(A, C.T[hi], rcond=None)[0]
east = C.B["east2"].astype(float)
egx = np.gradient(east, C.PIX / 1000, axis=1)                         # d(v_east)/dx, 1/yr * mm/km
r = C.rho(egx, C.T, C.LAND)
pr, nr = C.shift_p(lambda e: C.rho(e, C.T, C.LAND), egx, r, 999, -1)
res = dict(faults=fault, tilt_high_ground=dict(offset=coef[0], mm_yr_per_km_east=coef[1], mm_yr_per_km_north=coef[2]),
           uplift_share_land=float(np.mean(C.T[C.LAND] < -5)), uplift_share_high_ground=float(np.mean(C.T[hi] < -5)),
           uplift_median_H=float(np.median(C.H[C.LAND & (C.T < -5)])) if (C.LAND & (C.T < -5)).any() else None,
           east_strain_vs_T=dict(rho=r, p_shift=pr, null=nr, note="negative = horizontal contraction over sinking"),
           east_rate_pct=np.nanpercentile(east[C.LAND], [5, 50, 95]).tolist())
C.save("X09", res, dict(dist_fault=np.minimum(ndimage.distance_transform_edt(~FM) * C.PIX, 20000) if FM.any()
                        else np.full((C.NY, C.NX), np.nan)), dict(dist_fault="tectonic"))
