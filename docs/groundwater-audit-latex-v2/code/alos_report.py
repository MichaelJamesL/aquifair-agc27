"""Summary numbers + figure for the ALOS-1 rate map written by alos_analyze.py.
Reads exp/alos_rate_grid.npz and exp/alos_result.json; writes alos/alos_rate_map.png,
alos/alos_rate_grid.npz and alos/alos_summary.json (realdata/semarang/alos/).
Well test (no detector): mean ALOS rate at PANGAEA production-well cells vs the same number of
cells drawn uniformly from the coherent mask (Monte Carlo), plus the share of wells in the top-10% cells."""
import json, shutil
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
import synth as S
import real_lib as R
import real_goal_maps as GM

ROOT = GM.ROOT
z = np.load(f"{ROOT}/exp/alos_rate_grid.npz")
D, mask = z["D"], z["mask"]
res = json.load(open(f"{ROOT}/exp/alos_result.json"))
grid = GM.grid
water = np.load(f"{ROOT}/worldcover_grid.npz")["water"]
mask_all = mask
mask = mask & (water < 0.5)          # land only: L-band coherence >= 0.3 still leaks over the sea
v = D[mask]
pct = {f"p{q}": float(np.percentile(v, q)) for q in (1, 5, 25, 50, 75, 95, 99)}
iy, ix = np.unravel_index(np.nanargmax(np.where(mask, D, -np.inf)), D.shape)
E, N = grid.E0 + (ix + 0.5) * S.PIX, grid.N0 + (iy + 0.5) * S.PIX
lon, lat = grid.inv.transform(E, N)

Ds, mask_s, H, _ = GM.load("da", "1822")
both = mask & mask_s
s1 = dict(n=int(both.sum()), pearson=float(np.corrcoef(D[both], Ds[both])[0, 1]),
          spearman=float(spearmanr(D[both], Ds[both])[0]),
          ratio_median_alos_over_s1=float(np.median(D[both]) / np.median(Ds[both])))
# ramp indicator: ALOS = a + b*S1 + c*x + d*y on the overlap (c, d in mm/yr per km)
Am = np.c_[np.ones(both.sum()), Ds[both], S.XX[both] / 1e3, S.YY[both] / 1e3]
cf = np.linalg.lstsq(Am, D[both], rcond=None)[0]
s1["fit_alos_on_s1_plus_plane"] = dict(b=float(cf[1]), dEast_per_km=float(cf[2]), dNorth_per_km=float(cf[3]))
half = S.XX >= S.NX * S.PIX / 2
s1["pearson_west_half"] = float(np.corrcoef(D[both & ~half], Ds[both & ~half])[0, 1])
s1["pearson_east_half"] = float(np.corrcoef(D[both & half], Ds[both & half])[0, 1])

wells, _ = R.pangaea_wells(f"{ROOT}/pangaea.tab", grid)
wi = (wells[:, 0] // S.PIX).astype(int).clip(0, S.NX - 1); wj = (wells[:, 1] // S.PIX).astype(int).clip(0, S.NY - 1)
inm = mask[wj, wi]
wr = D[wj[inm], wi[inm]]
rng = np.random.default_rng(11)
cells = np.flatnonzero(mask.ravel())
null = D.ravel()[rng.choice(cells, (10000, len(wr)))].mean(1)
top = np.percentile(v, 90)
well = dict(n_wells=int(len(wells)), n_in_mask=int(inm.sum()), mean_rate_at_wells=float(wr.mean()),
            median_rate_at_wells=float(np.median(wr)), null_mean=float(null.mean()), null_sd=float(null.std()),
            p_uniform=float((null >= wr.mean()).mean()), frac_wells_in_top10pct=float((wr >= top).mean()))
out = dict(source="ALOS-1 PALSAR path 431, ISCE2 stripmapStack on DGX Spark", percentiles_mm_yr=pct,
           max_sinking=dict(rate=float(D[iy, ix]), E=float(E), N=float(N), lon=float(lon), lat=float(lat), row=int(iy), col=int(ix)),
           mask_frac=float(mask_all.mean()), land_mask_frac=float(mask.mean()),
           note="percentiles, max, S1 comparison and well test use coherent land cells only (WorldCover water < 0.5)", s1_2018_22=s1, pangaea_wells=well,
           analyze=dict((k, res[k]) for k in res if k != "detections") | {"n_det": res.get("detections", {}).get("n")})
A = f"{ROOT}/alos"
json.dump(out, open(f"{A}/alos_summary.json", "w"), indent=1)
shutil.copy(f"{ROOT}/exp/alos_rate_grid.npz", f"{A}/alos_rate_grid.npz")

ext = [grid.E0 / 1e3, (grid.E0 + S.NX * S.PIX) / 1e3, grid.N0 / 1e3, (grid.N0 + S.NY * S.PIX) / 1e3]
fig, ax = plt.subplots(1, 2, figsize=(13, 4.6), constrained_layout=True)
for a, M, t in ((ax[0], D, "ALOS-1 2006-10"), (ax[1], np.where(mask_s, Ds, np.nan), "Sentinel-1 2018-22")):
    im = a.imshow(np.where(np.isfinite(M), M, np.nan), origin="lower", extent=ext, cmap="RdYlBu_r", vmin=-20, vmax=120)
    a.plot((wells[:, 0] + grid.E0) / 1e3, (wells[:, 1] + grid.N0) / 1e3, "k.", ms=3, label="PANGAEA wells")
    a.set_title(f"{t} vertical rate (mm/yr, + sinking)"); a.set_xlabel("UTM 49S E (km)"); a.set_ylabel("N (km)")
ax[0].plot(E / 1e3, N / 1e3, "m*", ms=12, label="max")
ax[0].legend(loc="lower left", fontsize=8)
fig.colorbar(im, ax=ax, shrink=0.8)
fig.savefig(f"{A}/alos_rate_map.png", dpi=130)
print(json.dumps({k: out[k] for k in ("percentiles_mm_yr", "max_sinking", "s1_2018_22", "pangaea_wells")}, indent=1))
