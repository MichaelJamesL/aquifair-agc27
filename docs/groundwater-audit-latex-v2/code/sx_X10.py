"""X10: independent elevation loss 2000 -> ~2012: Copernicus DEM (TanDEM-X 2011-15) minus NASADEM (SRTM, Feb 2000),
plane removed on stable high ground, vs the 2018-22 InSAR rate (sx_prereg.md)."""
import numpy as np
import planetary_computer as pc
import pystac_client
import rasterio
from rasterio.merge import merge
import sx_common as C

cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)


def mosaic(coll):
    its = list(cat.search(collections=[coll], bbox=C.bbox_ll(4000)).items())
    srcs = [rasterio.open((i.assets.get("elevation") or i.assets["data"]).href) for i in its]
    a, tf = merge(srcs, bounds=C.bbox_ll(4000), nodata=np.nan, dtype="float32")
    return C.array_to_grid(a[0], tf, srcs[0].crs), [i.id for i in its]


cop, ic = mosaic("cop-dem-glo-30")
nas, inn = mosaic("nasadem")
dz = cop - nas
stable = C.LAND & (C.H > 30) & (C.B["wc_tree"] > 0.5)
if stable.sum() < 30:
    stable = C.LAND & (C.H > 30)
A = lambda s: np.c_[np.ones(s.sum()), C.XX[s] / 1000, C.YY[s] / 1000]
coef = np.linalg.lstsq(A(stable), dz[stable], rcond=None)[0]
dz = dz - (coef[0] + coef[1] * C.XX / 1000 + coef[2] * C.YY / 1000)
nat = C.LAND & ((C.B["wc_tree"] + C.B["wc_crop"] + C.B["wc_grass"] + C.B["wc_wetland"] + C.B["wc_mangrove"]) > 0.5)
r_nat = C.rho(dz, C.T, nat)
p_nat, n_nat = C.shift_p(lambda d: C.rho(d, C.T, nat), dz, r_nat, 999, -1)
r_all = C.rho(dz, C.T, C.LAND)
p_all, _ = C.shift_p(lambda d: C.rho(d, C.T, C.LAND), dz, r_all, 999, -1)
fit = lambda s: np.polyfit(C.T[s & np.isfinite(dz)], dz[s & np.isfinite(dz)], 1).tolist()
res = dict(items_cop=ic, items_nasadem=inn, plane_removed=coef.tolist(), n_stable=int(stable.sum()),
           n_nonbuilt=int(nat.sum()), rho_nonbuilt=r_nat, p_shift_nonbuilt=p_nat, null_nonbuilt=n_nat,
           rho_all_land=r_all, p_shift_all=p_all,
           slope_dz_per_T_nonbuilt=fit(nat), slope_dz_per_T_all=fit(C.LAND),
           note="slope ~ -(years 2000->~2012) x (rate 2000-12 / rate 2018-22); -12 means same rate",
           PASS=bool(r_nat <= -0.2 and p_nat < 0.05),
           dz_pct_fast=np.nanpercentile(dz[C.LAND & (C.T > 60)], [10, 50, 90]).tolist(),
           dz_pct_stable=np.nanpercentile(dz[stable], [10, 50, 90]).tolist())
C.save("X10", res, dict(dem_change_2000_2012=dz), dict(dem_change_2000_2012="observation"))
