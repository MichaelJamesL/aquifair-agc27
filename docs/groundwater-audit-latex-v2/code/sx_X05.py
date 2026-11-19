"""X05: soft-soil thickness / young alluvium proxies vs sinking. Copernicus DEM 30 m (AWS open data), SoilGrids 2.0,
ISRIC depth to bedrock, borehole clay thickness (sx_prereg.md)."""
import numpy as np
import rasterio
from rasterio.merge import merge
from scipy import ndimage
import sx_common as C

COP = "/vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{t}_DEM/Copernicus_DSM_COG_10_{t}_DEM.tif"
with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
    srcs = [rasterio.open(COP.format(t=t)) for t in ("S07_00_E110_00", "S08_00_E110_00")]
    dem, tf = merge(srcs, bounds=C.bbox_ll(6000), nodata=np.nan, dtype="float32")
    crs = srcs[0].crs
dem = dem[0]
dy = abs(tf.e) * 111320.0
dx = tf.a * 111320.0 * np.cos(np.deg2rad(7.0))
gy, gx = np.gradient(dem, dy, dx)
slope = np.degrees(np.arctan(np.hypot(gx, gy)))
hill = (dem > 15) & (ndimage.uniform_filter(slope, 5) > 2)              # foot of the southern hills
hill = ndimage.binary_opening(hill, iterations=2)
d_hill = ndimage.distance_transform_edt(~hill, sampling=(dy, dx))
elev = C.array_to_grid(dem, tf, crs)
dhill = C.array_to_grid(d_hill.astype("f4"), tf, crs)
slp = C.array_to_grid(slope.astype("f4"), tf, crs)
SG = "/vsicurl/https://files.isric.org/soilgrids/latest/data/{p}/{p}_{d}_mean.vrt"
soil = {}
for p, sign in (("clay", +1), ("sand", -1), ("soc", +1), ("bdod", -1), ("silt", +1)):
    for d in ("30-60cm", "100-200cm"):
        try:
            soil[f"{p}_{d}"] = (C.to_grid(SG.format(p=p, d=d), nodata=-32768), sign)
        except Exception as e:
            print("soilgrids miss", p, d, str(e)[:80], flush=True)
try:
    soil["depth_to_bedrock"] = (C.to_grid("/vsicurl/https://files.isric.org/soilgrids/former/2017-03-10/data/"
                                          "BDTICM_M_250m_ll.tif", nodata=-99999), +1)
except Exception as e:
    print("bdticm miss", str(e)[:80], flush=True)
clay_bh = C.B["clay_m"].astype(float)
drivers = {"elevation_m": (elev, -1), "dist_from_hill_foot_m": (dhill, +1), "slope_deg": (slp, -1),
           "dist_to_coast_m": (C.DCOAST, -1), "borehole_clay_m": (clay_bh, +1), **soil}
tests = {k: C.driver_test(k, v, s) for k, (v, s) in drivers.items()}
m = C.LAND
Xf = np.c_[[drivers[k][0][m] for k in drivers]].T
r2 = C.block_cv_r2(Xf, C.T[m])
r2_simple = C.block_cv_r2(np.c_[elev[m], dhill[m], C.DCOAST[m]], C.T[m])
best = max(tests.values(), key=lambda t: abs(t["rho"]) if np.isfinite(t["rho"]) else 0)
res = dict(cv_r2_all_geology=r2, cv_r2_elev_hill_coast=r2_simple, best_single=best["name"], best_rho=best["rho"],
           best_p=best["p_shift"], PASS=bool(r2 >= 0.3 and abs(best["rho"]) >= 0.3 and best["p_shift"] < 0.05),
           tests=tests)
C.save("X05", res, {k: v for k, (v, s) in drivers.items()}, {k: "soil" for k in drivers})
