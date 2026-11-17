"""MODIS MOD16A3GF annual evapotranspiration (500 m, v061) 2016-2020 on the Arizona 200 m grid.
Run in WSL env `alos` (earthaccess with ~/.netrc). Output: realdata/arizona/et_200m.npz (mm/yr)."""
import glob, os
import numpy as np
import earthaccess
import rasterio
from pyproj import Transformer

A = "/mnt/c/Kuliah/hackathon/agc-26/realdata/arizona"
z = np.load(f"{A}/opera_rate_200m.npz", allow_pickle=True)
E0, N0, PIX = float(z["E0"]), float(z["N0"]), float(z["PIX"])
NY, NX = z["D"].shape
earthaccess.login(strategy="netrc")
os.makedirs(f"{A}/modis", exist_ok=True)
res = earthaccess.search_data(short_name="MOD16A3GF", version="061", bounding_box=(-112.1, 32.6, -111.2, 33.45),
                              temporal=("2016-01-01", "2020-12-31"))
earthaccess.download(res, f"{A}/modis")
# MODIS sinusoidal grid -> 200 m UTM cells (nearest)
SIN = "+proj=sinu +R=6371007.181 +nadgrids=@null +wktext"
Ec, Nc = np.meshgrid(E0 + (np.arange(NX) + .5) * PIX, N0 + (np.arange(NY) + .5) * PIX)
xs, ys = Transformer.from_crs(32612, SIN, always_xy=True).transform(Ec, Nc)
ET = []
for f in sorted(glob.glob(f"{A}/modis/MOD16A3GF*.hdf")):
    with rasterio.open(f'HDF4_EOS:EOS_GRID:"{f}":MOD_Grid_MOD16A3:ET_500m') as s:
        a = s.read(1).astype(float)
        t = s.transform
    a[a > 32700] = np.nan                              # fill / non-vegetated codes
    a *= 0.1                                           # kg/m2/yr = mm/yr
    col, row = ((xs - t.c) / t.a).astype(int), ((ys - t.f) / t.e).astype(int)
    ok = (col >= 0) & (col < a.shape[1]) & (row >= 0) & (row < a.shape[0])
    g = np.full((NY, NX), np.nan)
    g[ok] = a[row[ok], col[ok]]
    ET.append(g)
    print(os.path.basename(f), np.nanmean(g).round(1), flush=True)
et = np.nanmean(np.stack(ET), 0)
np.savez_compressed(f"{A}/et_200m.npz", et_mm=et.astype(np.float32))
print("saved; mean ET", round(float(np.nanmean(et)), 1))
