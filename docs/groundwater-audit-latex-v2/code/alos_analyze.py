"""ALOS-1 (2006-2010, L-band, ascending path 431) rate map of Semarang on the model grid,
then the local matched-filter detector and the truth tests vs PANGAEA wells / OSM industrial.

Usage: python alos_analyze.py [--sign auto|+1|-1]
Writes realdata/semarang/exp/alos_result.json and alos_rate_grid.npz.
shortcut: stacking (sum of referenced LOS / sum of dt), vertical-only (LOS / cos(incidence)).
Sign: ISCE vs LiCSAR phase conventions differ; 'auto' picks the sign whose map correlates
positively with the Sentinel-1 2018-22 subsidence map (subsidence pattern is long-lived), and
the result records the correlation so this choice is visible.
"""
import sys, json
import numpy as np
import synth as S
import real_lib as R
import real_goal_maps as GM
import real_mf as MF

ROOT = GM.ROOT
LAM = 0.2360571                                           # ALOS PALSAR L-band wavelength, m
z = np.load(f"{ROOT}/alos/stack_alos.npz")
pairs, unw, coh = z["pairs"], z["unw"], z["coh"]
lat, lon, hgt, inc = z["lat"], z["lon"], z["hgt"], z["inc"]
d = lambda s: np.datetime64(f"{s[:4]}-{s[4:6]}-{s[6:8]}")
dt = np.array([(d(p.split("_")[1]) - d(p.split("_")[0])).astype(int) for p in pairs]) / 365.25
grid = GM.grid
E, N = grid.fw.transform(lon.astype(float), lat.astype(float))
inbox = (E >= grid.E0) & (E < grid.E0 + S.NX * S.PIX) & (N >= grid.N0) & (N < grid.N0 + S.NY * S.PIX)
ref = (hgt > 60) & inbox
valid = (unw != 0) & np.isfinite(unw) & (coh >= 0.3)
num = np.zeros(unw.shape[1:]); den = np.zeros(unw.shape[1:]); cnt = np.zeros(unw.shape[1:]); used = 0
for k in range(len(pairs)):
    r = valid[k] & ref
    if r.sum() < 50:
        continue
    los = (unw[k] - np.median(unw[k][r])) * (-LAM / (4 * np.pi) * 1000)   # mm, + towards satellite
    num += np.where(valid[k], los, 0); den += valid[k] * dt[k]; cnt += valid[k]; used += 1
ok = (cnt / max(used, 1) >= 0.5) & inbox
U = np.cos(np.deg2rad(inc))
sub = np.where(ok, -(num / np.maximum(den, 1e-9)) / U, np.nan)        # + = sinking, mm/yr

# bin to the model grid (arbitrary lat/lon per pixel)
ix = ((E - grid.E0) // S.PIX).astype(int); iy = ((N - grid.N0) // S.PIX).astype(int)
g = ok & np.isfinite(sub)
lin = iy[g] * S.NX + ix[g]
c = np.bincount(lin, minlength=S.NX * S.NY)
Da = (np.bincount(lin, sub[g], minlength=S.NX * S.NY) / np.maximum(c, 1)).reshape(S.NY, S.NX)
mask_a = c.reshape(S.NY, S.NX) >= 1

# Sentinel-1 2018-22 two-track map for sanity and sign
Ds, mask_s, H, _ = GM.load("da", "1822")
both = mask_a & mask_s
r_s1 = float(np.corrcoef(Da[both], Ds[both])[0, 1])
arg = sys.argv[sys.argv.index("--sign") + 1] if "--sign" in sys.argv else "auto"
sign = (1.0 if r_s1 >= 0 else -1.0) if arg == "auto" else float(arg)
Da = sign * Da
D = np.where(mask_a, Da, np.nan)
res = dict(pairs_used=used, n_pairs=int(len(pairs)), span=[str(min(p[:8] for p in pairs)), str(max(p[9:] for p in pairs))],
           sign=sign, corr_with_s1_raw=r_s1, mask_frac=float(mask_a.mean()),
           p99=float(np.nanpercentile(D, 99)), max=float(np.nanmax(D)), stable=R.stable_noise(D, H, mask_a),
           s1_compare=dict(n=int(both.sum()), pearson=abs(r_s1),
                           median_alos=float(np.nanmedian(D[both])), median_s1=float(np.nanmedian(Ds[both])),
                           p95_alos=float(np.nanpercentile(D[both], 95)), p95_s1=float(np.nanpercentile(Ds[both], 95)),
                           robust_sd_diff=float(1.4826 * np.nanmedian(np.abs((D - Ds)[both] - np.nanmedian((D - Ds)[both]))))))
np.savez(f"{ROOT}/exp/alos_rate_grid.npz", D=D, mask=mask_a)
print(json.dumps(res, indent=1), flush=True)

# detector (same settings as the validated Sentinel-1 run) + truth tests
Dz = np.nan_to_num(D)
det = MF.Detector(mask_a, H, Dz)
srcs = det.detect(Dz)
wells, _ = R.pangaea_wells(f"{ROOT}/pangaea.tab", grid)
ind, _ = R.osm_layers(f"{ROOT}/osm.json", grid)
rng = np.random.default_rng(11)
res["detections"] = dict(n=int(len(srcs)), sources=srcs.round(1).tolist())
if len(srcs):
    res["wells_1km"] = R.location_test(srcs, det.ok, Dz, lambda p: R.dist_to_points(p, wells), 1000, rng)
    res["industrial_500m"] = R.location_test(srcs, det.ok, Dz, lambda p: R.dist_to_raster(p, ind), 500, rng)
    big = srcs[srcs[:, 2] >= 150]
    if len(big):
        res["big_ge150"] = dict(n=int(len(big)),
                                wells_1km=R.location_test(big, det.ok, Dz, lambda p: R.dist_to_points(p, wells), 1000, rng),
                                industrial_500m=R.location_test(big, det.ok, Dz, lambda p: R.dist_to_raster(p, ind), 500, rng))
json.dump(res, open(f"{ROOT}/exp/alos_result.json", "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ("detections",)} | {"n_det": res["detections"]["n"]}, indent=1))
