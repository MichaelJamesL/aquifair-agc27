"""Land-cover composition (ESA WorldCover 2021, 10 m) at detected sources vs coherent cells.

Usage: python real_landcover.py SOURCES.json
Writes realdata/semarang/worldcover_grid.npz (class fractions per 200 m cell).
"""
import sys, json
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from scipy import ndimage
import real_lib as R
import synth as S

SD = "C:/Kuliah/hackathon/agc-26/realdata/semarang/"
g = R.Grid(428000.0, 9220000.0, 32749)
URL = ("/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
       "ESA_WorldCover_10m_2021_v200_S09E108_Map.tif")
with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"), rasterio.open(URL) as s:
    w = from_bounds(*g.lonlat_bounds(500), s.transform).round_offsets().round_lengths()
    a = s.read(1, window=w)
    t = s.window_transform(w)
ny, nx = a.shape
LON, LAT = np.meshgrid(t.c + t.a * (np.arange(nx) + .5), t.f + t.e * (np.arange(ny) + .5))
E, N = g.fw.transform(LON, LAT)
ix = ((E - g.E0) // S.PIX).astype(int)
iy = ((N - g.N0) // S.PIX).astype(int)
ok = (ix >= 0) & (ix < S.NX) & (iy >= 0) & (iy < S.NY)
lin = (iy * S.NX + ix)[ok]
tot = np.maximum(np.bincount(lin, minlength=S.NX * S.NY), 1)
names = {10: "tree", 20: "shrub", 30: "grass", 40: "crop", 50: "built", 60: "bare", 80: "water",
         90: "wetland", 95: "mangrove"}
frac = {nm: (np.bincount(lin, (a == k)[ok].astype(float), minlength=S.NX * S.NY) / tot).reshape(S.NY, S.NX)
        for k, nm in names.items()}
np.savez_compressed(SD + "worldcover_grid.npz", **frac)

rms = [R.rate_map(SD + tr, gacos=True, min_dt=24) for tr in ("t076", "t127")]
H = R.grid_hgt(rms[0], g)
D, m, _ = R.combine_tracks(rms, g, H)
src = np.array(json.load(open(sys.argv[1]))["fits"]["cv"]["sources"]).reshape(-1, 3)
fast = m & (np.nan_to_num(D) > 80)
print("class      coherent  fast(>80)  sources(600 m)")
for nm, f in frac.items():
    fs = ndimage.uniform_filter(f, 3)
    sv = [fs[int(s[1] // S.PIX), int(s[0] // S.PIX)] for s in src]
    print(f"{nm:9s}  {f[m].mean():.3f}     {f[fast].mean():.3f}      {np.mean(sv):.3f}")
allf = {nm: float(f[~m].mean()) for nm, f in frac.items()}
print("incoherent (masked) cells:", {k: round(v, 3) for k, v in allf.items()})
