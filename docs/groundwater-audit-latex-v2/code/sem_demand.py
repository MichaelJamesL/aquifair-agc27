"""Semarang groundwater-pumping estimate as AREAS with volume RANGES (demand model + InSAR).

Pumping per 200 m cell (m3/yr) = domestic + industrial
  domestic   = footprint_m2 / m2_per_person * L_per_person_day * 365/1000 * (1 - piped_coverage)
  industrial = OSM industrial area * intensity, intensity set so that industrial pumping in the
               grid = registered industrial/commercial abstraction (15-25 Mm3/yr) * share in grid
Parameters are drawn from ranges (Monte Carlo); Arizona's measured model error at 4 km
(median |log10| ~0.37 -> sigma_log10 0.55) is added per block. Reported per 4 km block and per
InSAR hotspot area: P10-P50-P90 pumping, subsidence volume, detector volume.
Sanity check only (no per-well truth in Semarang): grid total vs city totals 38-61 Mm3/yr.
Assumptions are listed in the output JSON."""
import json
import numpy as np
from scipy import ndimage
from scipy.spatial import ConvexHull
from matplotlib.path import Path
import synth as S
import real_lib as R
import real_goal_maps as GM
import real_mf as MF

ROOT = GM.ROOT
OUT = f"{ROOT}/exp/sem_areas"
rng = np.random.default_rng(42)
NS = 4000
D, mask, H, info = GM.load("da", "1822")
Dz = np.nan_to_num(D)
grid = GM.grid
foot = np.load("C:/Kuliah/hackathon/agc-26/realdata/msbuild/semarang_grid.npz")["frac"] * S.PIX ** 2   # m2 per cell
ind, _ = R.osm_layers(f"{ROOT}/osm.json", grid)
lon, lat = grid.inv.transform(S.XX + grid.E0, S.YY + grid.N0)
adm = json.load(open(f"{ROOT}/admin/idn_adm2.geojson"))
district = np.full(S.XX.shape, "other", dtype=object)
for f in adm["features"]:
    name = f["properties"]["shapeName"]
    if name not in ("Kota Semarang", "Demak"):
        continue
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for p in polys:
        inside = Path(np.array(p[0])).contains_points(np.c_[lon.ravel(), lat.ravel()]).reshape(lon.shape)
        district[inside] = name
kota, demak = district == "Kota Semarang", district == "Demak"

ASSUME = dict(m2_footprint_per_person=(31, 40), litres_per_person_day=(80, 150),
              piped_coverage_kota=(0.52, 0.65), piped_coverage_demak=(0.20, 0.45),
              industrial_registered_Mm3=(15, 25), industrial_share_in_grid=(0.6, 1.0),
              model_sigma_log10_per_4km=0.55,
              sources=["m2/person calibrated: Kota 35.6, Demak 33.1 (BPS population / Microsoft footprints, sem_popcal.py)",
                       "PDAM Tirta Moedal site: 52 % coverage; ANTARA: 60-65 %",
                       "registered industrial/commercial wells 15.3 Mm3 (2003) - 21.0 Mm3 (2006)",
                       "city groundwater total ~38 Mm3/yr (2000s), ~61 Mm3/yr (2010 model)",
                       "Demak coverage range is an assumption (no data found)"])
NSIM = 2000
bs = int(NS // S.PIX)
bid = (np.arange(S.NY)[:, None] // bs) * (S.NX // bs + 1) + np.arange(S.NX)[None, :] // bs
nbk = bid.max() + 1
ind_area = (ind & mask).sum() * S.PIX ** 2
U = lambda a: rng.uniform(*a)

# hotspot areas from the matched filter: connected region of fitted volume > 60 around each peak
det = MF.Detector(mask, H, Dz)
qmap = np.where(det.ok, det.qhat(Dz), 0)
peaks = det.detect(Dz)
lab, _ = ndimage.label(qmap > 60)
hot, seen = [], set()
for x, y, q in sorted(peaks.tolist(), key=lambda p: -p[2]):
    k = lab[int(y // S.PIX), int(x // S.PIX)]
    if k and k in seen:
        continue
    seen.add(k)
    reg = (lab == k) if k else (np.hypot(S.XX - x, S.YY - y) <= 500)
    hot.append(dict(x=x, y=y, q_det=q, reg=reg, buf=ndimage.binary_dilation(reg, iterations=5)))  # +1 km

blk_sims, hot_sims, tot_sims = [], [], []
for _ in range(NSIM):
    pop = foot / U(ASSUME["m2_footprint_per_person"])
    cov = np.where(kota, U(ASSUME["piped_coverage_kota"]), np.where(demak, U(ASSUME["piped_coverage_demak"]), 0.5))
    dom = pop * U(ASSUME["litres_per_person_day"]) * 365 / 1000 * (1 - cov)
    inten = U(ASSUME["industrial_registered_Mm3"]) * 1e6 * U(ASSUME["industrial_share_in_grid"]) / max(ind_area, 1)
    cell = dom + ind * inten * S.PIX ** 2
    err = 10 ** rng.normal(0, ASSUME["model_sigma_log10_per_4km"], nbk)       # per-block structural error
    bt = np.bincount(bid.ravel(), cell.ravel(), minlength=nbk)
    err *= bt.sum() / max((bt * err).sum(), 1e-9)       # spread blocks, keep the regional total unbiased
    cell = cell * err[bid]
    blk_sims.append(np.bincount(bid.ravel(), cell.ravel(), minlength=nbk))
    hot_sims.append([cell[h["buf"]].sum() for h in hot])
    tot_sims.append([cell[kota].sum(), cell[demak].sum(), cell.sum()])
blk = np.percentile(np.array(blk_sims), [10, 50, 90], 0) / 1e6           # Mm3/yr
hs = np.percentile(np.array(hot_sims), [10, 50, 90], 0) / 1e6 if hot else np.zeros((3, 0))
tot = np.percentile(np.array(tot_sims), [10, 50, 90], 0) / 1e6

subvol = np.bincount(bid.ravel(), (np.clip(Dz, 0, None) * mask).ravel() * S.PIX ** 2 / 1e3, minlength=nbk) / 1e6  # Mm3/yr
blocks, feats = [], []
for b in range(nbk):
    cells = bid == b
    if not (cells & mask).any():
        continue
    (r0, c0), (r1, c1) = np.argwhere(cells)[[0, -1]]
    x0, y0, x1, y1 = c0 * S.PIX, r0 * S.PIX, (c1 + 1) * S.PIX, (r1 + 1) * S.PIX
    ring = [grid.inv.transform(grid.E0 + a, grid.N0 + c) for a, c in ((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0))]
    props = dict(kind="4km_block", pump_p10=round(blk[0, b], 3), pump_p50=round(blk[1, b], 3), pump_p90=round(blk[2, b], 3),
                 subsidence_volume=round(subvol[b], 3), mean_subsidence_mm=round(float(np.nanmean(D[cells & mask])), 1),
                 coherent_frac=round(float(mask[cells].mean()), 2))
    blocks.append(props)
    feats.append(dict(type="Feature", properties=props, geometry=dict(type="Polygon", coordinates=[[list(p) for p in ring]])))
for i, h in enumerate(hot):
    yy, xx = np.nonzero(h["reg"])
    pts = np.c_[np.r_[xx, xx + 1, xx, xx + 1], np.r_[yy, yy, yy + 1, yy + 1]] * S.PIX   # cell corners
    o = ConvexHull(pts).vertices                                # outline = convex hull of the area
    ring = [grid.inv.transform(grid.E0 + pts[j, 0], grid.N0 + pts[j, 1]) for j in o]
    ring.append(ring[0])
    lo_, la_ = grid.inv.transform(grid.E0 + h["x"], grid.N0 + h["y"])
    props = dict(kind="insar_hotspot", id=i, lon=round(lo_, 4), lat=round(la_, 4), area_km2=round(float(h["reg"].sum() * 0.04), 2),
                 detector_volume_k=round(float(h["q_det"]), 0),
                 subsidence_volume=round(float((np.clip(Dz, 0, None) * h["reg"] * mask).sum() * S.PIX ** 2 / 1e9), 4),
                 pump_p10=round(hs[0, i], 3), pump_p50=round(hs[1, i], 3), pump_p90=round(hs[2, i], 3),
                 industrial_share=round(float((ind & h["buf"]).sum() / max(h["buf"].sum(), 1)), 2))
    feats.append(dict(type="Feature", properties=props, geometry=dict(type="Polygon", coordinates=[[list(p) for p in ring]])))
import os
os.makedirs(OUT, exist_ok=True)
json.dump(dict(type="FeatureCollection", features=feats), open(f"{OUT}/semarang_areas.geojson", "w"))
summary = dict(assumptions=ASSUME, grid_total_Mm3={k: [round(float(v), 1) for v in tot[:, i]] for i, k in enumerate(("kota_cells", "demak_cells", "all"))},
               city_total_reference_Mm3=[38, 61], n_blocks=len(blocks), n_hotspots=len(hot),
               note="Volumes cannot be validated in Semarang; ranges inherit Arizona's 4 km model error.")
json.dump(summary, open(f"{OUT}/summary.json", "w"), indent=1)
print(json.dumps({k: v for k, v in summary.items() if k != "assumptions"}, indent=1))
hp = sorted([f["properties"] for f in feats if f["properties"]["kind"] == "insar_hotspot"], key=lambda p: -p["pump_p50"])
for p in hp[:10]:
    print(p)
