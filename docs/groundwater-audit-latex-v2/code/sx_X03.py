"""X03: age and volume of buildings (load). GHSL R2023A BUILT-S 1975-2020 (5-yearly), BUILT-V 2020, BUILT-H 2018,
100 m Mollweide tiles downloaded on the Spark (sx_prereg.md)."""
import glob
import os
import urllib.request
import zipfile
import numpy as np
from pyproj import Transformer
import sx_common as C

G = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL"
D = f"{C.DATA}/ghsl"
os.makedirs(D, exist_ok=True)
x, y = Transformer.from_crs(4326, "ESRI:54009", always_xy=True).transform(110.44, -6.99)
R0, C0 = int((9000000 - y) // 1e6) + 1, int((x + 18041000) // 1e6) + 1


def get(prod, name):
    """Download + unzip one tile; try the computed tile first, then its neighbours."""
    for r, c in [(R0, C0), (R0, C0 - 1), (R0, C0 + 1), (R0 - 1, C0), (R0 + 1, C0)]:
        tif = f"{D}/{name}_V1_0_R{r}_C{c}.tif"
        if os.path.exists(tif):
            return tif
        u = f"{G}/{prod}/{name}/V1-0/tiles/{name}_V1_0_R{r}_C{c}.zip"
        try:
            zf = f"{D}/tmp_{name}_{r}_{c}.zip"
            urllib.request.urlretrieve(u, zf)
            with zipfile.ZipFile(zf) as z:
                z.extractall(D)
            os.remove(zf)
            got = glob.glob(f"{D}/{name}_V1_0_R{r}_C{c}*.tif")
            g = C.to_grid(got[0], nodata=65535)
            if np.isfinite(g).mean() > 0.9:
                return got[0]
        except Exception as e:
            print("miss", u, str(e)[:60], flush=True)
    raise RuntimeError(name)


EP = list(range(1975, 2025, 5))
frac = {}
for e in EP:
    frac[e] = C.to_grid(get("GHS_BUILT_S_GLOBE_R2023A", f"GHS_BUILT_S_E{e}_GLOBE_R2023A_54009_100"), nodata=65535) / 1e4
vol = C.to_grid(get("GHS_BUILT_V_GLOBE_R2023A", "GHS_BUILT_V_E2020_GLOBE_R2023A_54009_100"), nodata=4294967295) / 1e4
hgt = C.to_grid(get("GHS_BUILT_H_GLOBE_R2023A", "GHS_BUILT_H_AGBH_E2018_GLOBE_R2023A_54009_100"), nodata=-32768)
F = np.stack([frac[e] for e in EP])
first = np.where((F >= 0.2).any(0), np.array(EP)[np.argmax(F >= 0.2, 0)], np.nan)
age = 2020.0 - first                                                 # 0 = became >= 20 % built in 2016-20
growth = frac[2020] - frac[2000]
m = C.LAND & np.isfinite(age)
r = C.rho(age, C.T, m)
pa, na = C.shift_p(lambda a: C.rho(a, C.T, C.LAND & np.isfinite(a)), age, r, 999, -1)
vd = C.driver_test("built_volume_m3_per_m2", vol, +1)
by_epoch = {int(e): dict(n=int((m & (first == e)).sum()), mean_T=float(C.T[m & (first == e)].mean()))
            for e in EP if (m & (first == e)).sum() >= 5}
res = dict(tile=f"R{R0}_C{C0}", n_built_cells=int(m.sum()), rho_age_T=r, p_shift_age=pa, null_age=na,
           by_first_epoch=by_epoch, PASS_age=bool(r <= -0.2 and pa < 0.05),
           volume=vd, PASS_volume=bool(vd["rho_partial"] >= 0.2 and vd["p_shift_partial"] < 0.05),
           height=C.driver_test("mean_building_height_m", hgt, +1),
           growth_2000_2020=C.driver_test("built_growth_2000_2020", growth, +1),
           built_2020=C.driver_test("built_fraction_2020", frac[2020], +1))
C.save("X03", res, dict(built_age=age, built_volume=vol, built_height=hgt, built_growth=growth, built_1990=frac[1990]),
       dict(built_age="load", built_volume="load", built_height="load", built_growth="load", built_1990="load"))
