"""Open, globally available covariates on the site 200 m grid (opera_site.py, env SITE) (same grid as opera_rate_200m):
ESA WorldCover 2021 class fractions (10 m, windowed COG reads). Output: realdata/<site>/features_200m.npz."""
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from pyproj import Transformer

from opera_site import SITE, WIN_ROOT as A

E0, N0, PIX, NX, NY = SITE["grid"]
inv = Transformer.from_crs(SITE["epsg"], 4326, always_xy=True)
fw = Transformer.from_crs(4326, SITE["epsg"], always_xy=True)
lo0, la0 = inv.transform(E0 - 500, N0 - 500)
lo1, la1 = inv.transform(E0 + NX * PIX + 500, N0 + NY * PIX + 500)
ENV = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif")


def to_grid(a, t, classes=None):
    ny, nx = a.shape
    LON, LAT = np.meshgrid(t.c + t.a * (np.arange(nx) + .5), t.f + t.e * (np.arange(ny) + .5))
    E, N = fw.transform(LON, LAT)
    ix, iy = ((E - E0) // PIX).astype(int), ((N - N0) // PIX).astype(int)
    ok = (ix >= 0) & (ix < NX) & (iy >= 0) & (iy < NY)
    lin = (iy * NX + ix)[ok]
    tot = np.maximum(np.bincount(lin, minlength=NX * NY), 1)
    if classes is None:
        return (np.bincount(lin, a[ok].astype(float), minlength=NX * NY) / tot).reshape(NY, NX)
    return {k: (np.bincount(lin, (a == v)[ok].astype(float), minlength=NX * NY) / tot).reshape(NY, NX)
            for k, v in classes.items()}


out = {}
cls = dict(tree=10, shrub=20, grass=30, crop=40, built=50, bare=60, water=80)
acc = {k: np.zeros((NY, NX)) for k in cls}
n = np.zeros((NY, NX))
lon_t = range(int(np.floor(SITE["box"][0] / 3) * 3), int(np.floor(SITE["box"][2] / 3) * 3) + 1, 3)
lat_t = range(int(np.floor(SITE["box"][1] / 3) * 3), int(np.floor(SITE["box"][3] / 3) * 3) + 1, 3)
for tile in [f"N{la:02d}W{-lo:03d}" for la in lat_t for lo in lon_t]:   # 3-degree tiles named by SW corner
    url = f"/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
    with rasterio.Env(**ENV), rasterio.open(url) as s:
        b = s.bounds
        bb = (max(lo0, b.left), max(la0, b.bottom), min(lo1, b.right), min(la1, b.top))
        if bb[0] >= bb[2] or bb[1] >= bb[3]:
            continue
        # decimate 10 m -> 30 m on read to keep memory low (class fractions per 200 m cell)
        w = from_bounds(*bb, s.transform).round_offsets().round_lengths()
        a = s.read(1, window=w, out_shape=(int(w.height // 3), int(w.width // 3)))
        t = s.window_transform(w) * rasterio.Affine.scale(w.width / a.shape[1], w.height / a.shape[0])
    f = to_grid(a, t, cls)
    cover = to_grid(np.ones_like(a), t) > 0
    for k in cls:
        acc[k] += np.where(cover, f[k], 0)
    n += cover
    print(tile, "done", flush=True)
for k in cls:
    out["wc_" + k] = (acc[k] / np.maximum(n, 1)).astype(np.float32)

# CHIRPS precipitation dropped: server refused requests (429/404); rainfall varies little in this box
np.savez_compressed(f"{A}/features_200m.npz", **out)
print({k: round(float(np.nanmean(v)), 3) for k, v in out.items()})
