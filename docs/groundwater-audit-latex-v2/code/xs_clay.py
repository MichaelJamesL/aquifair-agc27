"""Compressible clay thickness (m) on each site's 200 m grid, for the cross-site volume test.
Each site uses its best available source (they differ, so the model uses log-thickness / classes):
  houston : USGS GULF model (Knight et al. 2023, doi:10.5066/P9XM8A1P) fine-grained thickness
            fine_m2..m5 summed (Chicot + Evangeline + Burkeville + Jasper), 1 km Albers grid, metres
  arizona : ADWR Pinal AMA geology update (Dubas & Liu 2010) Fig. 7 MSCU isopach (ft), digitized
            by legend colour; georeferenced with the PLSS township grid (Gila & Salt River meridian).
            Outside the Pinal model (East Salt River Valley) = NaN.
  semarang: Sarah et al. 2020 (IJOG 7(3)) Fig. 2a W-E section, cumulative clay at 6 boreholes,
            IDW-interpolated, tapered to 0 on the volcanic foothills (height 5 -> 25 m).
Output: realdata/<site>/clay_200m.npz (clay_m, float32, NaN = unknown).
Usage: python xs_clay.py houston|arizona|semarang
"""
import sys
import numpy as np
from pyproj import Transformer
from scipy import ndimage

R0 = "C:/Kuliah/hackathon/agc-26/realdata"
site = sys.argv[1]


def site_grid(name):
    import os
    os.environ["SITE"] = name
    from opera_site import SITES
    s = SITES[name]
    E0, N0, PIX, NX, NY = s["grid"]
    E, N = np.meshgrid(E0 + (np.arange(NX) + .5) * PIX, N0 + (np.arange(NY) + .5) * PIX)
    return Transformer.from_crs(s["epsg"], 4326, always_xy=True).transform(E, N)


if site == "houston":
    G = f"{R0}/houston/gulf/source_data/gulf_grid/arrays"
    fine = sum(np.loadtxt(f"{G}/fine_m{k}.dat") for k in range(2, 6))         # (350, 380), row 0 = north
    lon, lat = site_grid("houston")
    x, y = Transformer.from_crs(4326, 5070, always_xy=True).transform(lon, lat)
    col, row = ((x + 134045) // 1000).astype(int), ((920285 - y) // 1000).astype(int)  # modelgeoref.txt corners
    ok = (col >= 0) & (col < 380) & (row >= 0) & (row < 350)
    clay = np.full(lon.shape, np.nan)
    clay[ok] = fine[row[ok], col[ok]]
    clay[clay <= 0] = np.nan                                       # inactive / outcrop cells

elif site == "arizona":
    from PIL import Image
    a = np.asarray(Image.open(f"{R0}/arizona/clay/fig7-31.png").convert("RGB")).astype(float)
    # legend colours (sampled from the swatches) -> class mid-thickness in ft; 301-1000 merged (same colour)
    leg = [((131, 166, 128), 25), ((182, 203, 152), 75), ((215, 229, 186), 150), ((245, 252, 206), 250),
           ((246, 238, 196), 600), ((231, 202, 176), 1250), ((219, 178, 161), 1750), ((205, 158, 156), 2500),
           ((229, 199, 196), 3500)]
    cols = np.array([c for c, _ in leg])
    d = np.linalg.norm(a[:, :, None, :] - cols[None, None], axis=-1)
    cls = d.argmin(-1)
    val = np.array([v for _, v in leg], float)[cls]
    white = a.min(-1) >= 248
    val[(d.min(-1) > 18) & ~white] = np.nan                       # grid lines, labels, hardrock
    inside = np.zeros(white.shape, bool)
    inside[93:878, 317:1403] = True                                # map frame
    # 4001-6000 ft is near-white: white holes enclosed by mapped cells = thickest class
    mapped = np.isfinite(val) & inside
    hole = ndimage.binary_fill_holes(ndimage.binary_closing(mapped, iterations=3)) & white & ~mapped
    val[hole] = 5000
    val[~inside | (white & ~hole)] = np.nan
    val = ndimage.generic_filter(val, np.nanmedian, size=7, mode="nearest")   # remove grid lines
    lon, lat = site_grid("arizona")
    # PLSS: T1S top = baseline 33.3742 N at y=35 px, R1E west edge = 112.2985 W at x=322 px; 85.2 px / 6 mi
    # shortcut: assumes regular 6-mile townships (real PLSS drifts ~0.5 km); fine at the 4 km scale used
    px = 322 + (lon + 112.2985) * 57.95 / 6 * 85.2
    py = 35 + (33.3742 - lat) * 69.05 / 6 * 85.25
    ix, iy = np.round(px).astype(int), np.round(py).astype(int)
    ok = (ix >= 0) & (ix < val.shape[1]) & (iy >= 0) & (iy < val.shape[0])
    clay = np.full(lon.shape, np.nan)
    clay[ok] = val[iy[ok], ix[ok]] * 0.3048
    lab, n = ndimage.label(np.isfinite(clay))                        # drop specks (colour misreads at map edges)
    size = ndimage.sum(np.ones_like(clay), lab, range(1, n + 1))
    clay[np.isin(lab, 1 + np.flatnonzero(size < 400))] = np.nan
    # self-check: Eloy (32.755 N, 111.555 W) lies in T7S R8E, inside the thick MSCU (> 300 m)
    ex, ey = 322 + (-111.555 + 112.2985) * 57.95 / 6 * 85.2, 35 + (33.3742 - 32.755) * 69.05 / 6 * 85.25
    assert 918 < ex < 1003 and 546 < ey < 716, (ex, ey)

elif site == "semarang":
    import real_goal_maps as GM
    import synth as S
    _, _, H, _ = GM.load("da", "1822")
    lon, lat = GM.grid.inv.transform(S.XX + GM.grid.E0, S.YY + GM.grid.N0)
    # boreholes on section A-A' (positions read from Fig. 1 / inset; +-1 km), cumulative clay to the Damar base
    bh = np.array([(110.380, -6.965, 45), (110.417, -6.987, 40), (110.445, -6.975, 75),
                   (110.473, -6.960, 100), (110.500, -6.940, 105), (110.538, -6.945, 115)])
    dx = (lon[..., None] - bh[:, 0]) * 110.6
    dy = (lat[..., None] - bh[:, 1]) * 110.6
    w = 1 / np.maximum(np.hypot(dx, dy), 0.5) ** 2
    clay = (w * bh[:, 2]).sum(-1) / w.sum(-1)
    clay *= np.clip((25 - np.nan_to_num(H, nan=0)) / 20, 0, 1)    # thin out onto the foothills
    clay[~np.isfinite(H)] = np.nan
    lon_ = lon

np.savez_compressed(f"{R0}/{site}/clay_200m.npz", clay_m=clay.astype(np.float32))
v = clay[np.isfinite(clay)]
print(site, "cells", clay.size, "known", v.size, "p10/50/90 m", np.percentile(v, [10, 50, 90]).round(0) if v.size else None)
