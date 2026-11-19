"""X02: age of new ground. Landsat C2 L2 1988-2024 annual composites -> year each 30 m pixel turned from water or
vegetation into built/bare for good -> sinking vs years since conversion (sx_prereg.md)."""
import os
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import planetary_computer as pc
import pystac_client
import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.transform import from_origin
import sx_common as C

R30 = 30.0
W, Hh = int(C.NX * C.PIX / R30), int(C.NY * C.PIX / R30)
TF30 = from_origin(C.E0, C.N0 + C.NY * C.PIX, R30, R30)
YEARS = list(range(1988, 2025))
cache = f"{C.DATA}/landsat_annual.npz"


def read(item):
    item = pc.sign(item)
    out = {}
    try:
        for b in ("green", "red", "nir08", "swir16", "qa_pixel"):
            with rasterio.open(item.assets[b].href) as s, WarpedVRT(s, crs=C.CRS, transform=TF30, width=W, height=Hh,
                                                                     resampling=Resampling.nearest) as v:
                out[b] = v.read(1)
    except Exception as e:
        print("skip", item.id, str(e)[:80], flush=True)
        return None
    qa = out.pop("qa_pixel").astype(np.uint16)
    ok = (qa & 0b11111) == 0                                        # no fill, dilated cloud, cirrus, cloud, shadow
    sr = {k: np.where(ok & (v > 0), v * 0.0000275 - 0.2, np.nan) for k, v in out.items()}
    with np.errstate(all="ignore"):
        mndwi = (sr["green"] - sr["swir16"]) / (sr["green"] + sr["swir16"])
        ndvi = (sr["nir08"] - sr["red"]) / (sr["nir08"] + sr["red"])
    return int(item.properties["datetime"][:4]), mndwi.astype("f4"), ndvi.astype("f4")


if not os.path.exists(cache):
    cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
    items = list(cat.search(collections=["landsat-c2-l2"], bbox=C.bbox_ll(0), datetime="1988-01-01/2024-12-31",
                            query={"eo:cloud_cover": {"lt": 70}}).items())
    print("items", len(items), flush=True)
    acc = {y: [[], []] for y in YEARS}
    with ThreadPoolExecutor(16) as ex:
        for k, r in enumerate(ex.map(read, items)):
            if r is not None and r[0] in acc:
                acc[r[0]][0].append(r[1]); acc[r[0]][1].append(r[2])
            if k % 50 == 0:
                print("read", k, flush=True)
    MW = np.full((len(YEARS), Hh, W), np.nan, "f4"); NV = MW.copy(); NOBS = np.zeros((len(YEARS), Hh, W), "i2")
    for i, y in enumerate(YEARS):
        if acc[y][0]:
            a, b = np.stack(acc[y][0]), np.stack(acc[y][1])
            MW[i] = np.nanmedian(a, 0); NV[i] = np.nanmedian(b, 0); NOBS[i] = np.isfinite(a).sum(0)
        acc[y] = None
    np.savez_compressed(cache, MW=MW, NV=NV, NOBS=NOBS, years=YEARS)
z = np.load(cache)
MW, NV, NOBS = z["MW"], z["NV"], z["NOBS"]
# classes: 0 water, 1 vegetation, 2 built/bare, -1 no data (years with < 2 clear looks)
cls = np.where(MW > 0.0, 0, np.where(NV > 0.4, 1, 2)).astype("i1")
cls[(NOBS < 2) | ~np.isfinite(MW) | ~np.isfinite(NV)] = -1
for i in range(1, len(YEARS)):                                     # forward-fill missing years
    cls[i] = np.where(cls[i] < 0, cls[i - 1], cls[i])
nat = (cls == 0) | (cls == 1)
yi = np.arange(len(YEARS))[:, None, None]
last_nat = np.where(nat, yi, -1).max(0)                             # last year still water / vegetation
valid_years = (cls >= 0).sum(0)
first_obs = np.where(cls >= 0, yi, 99).min(0)
conv = (last_nat >= first_obs) & (last_nat <= len(YEARS) - 4)       # converted and built/bare >= 3 yr since
conv_year = np.where(conv, np.array(YEARS)[np.clip(last_nat + 1, 0, len(YEARS) - 1)], np.nan)
old_built = (last_nat < 0) & (valid_years >= 10)                    # built/bare in every observed year
from_water = conv & (np.where(cls == 0, yi, -1).max(0) >= np.maximum(last_nat - 2, 0))
tf, crs = TF30, C.CRS
frac_conv = C.array_to_grid(conv.astype("f4"), tf, crs)
frac_old = C.array_to_grid(old_built.astype("f4"), tf, crs)
frac_from_water = C.array_to_grid(from_water.astype("f4"), tf, crs)
cy = C.array_to_grid(conv_year.astype("f4"), tf, crs)               # mean conversion year of converted pixels
age = 2020.0 - cy                                                   # years before the middle of 2018-22
# tests (sx_prereg.md X02)
m = C.LAND & (frac_conv >= 0.3) & np.isfinite(age)
r = C.rho(age, C.T, m)
pa, na = C.shift_p(lambda a, f: C.rho(a, C.T, C.LAND & (f >= 0.3) & np.isfinite(a)), (age, frac_conv), r, 999, -1)
conv_sel = C.LAND & (frac_conv >= 0.5)
obs, pm, nm = C.matched_p(conv_sel, pool=C.LAND & (frac_old >= 0.5))
by_decade = {f"{d}s": dict(n=int((m & (cy >= d) & (cy < d + 10)).sum()),
                           mean_T=float(np.nanmean(C.T[m & (cy >= d) & (cy < d + 10)])) if (m & (cy >= d) & (cy < d + 10)).any() else None)
             for d in (1980, 1990, 2000, 2010, 2020)}
res = dict(n_converted_cells=int(m.sum()), rho_age_T=r, p_shift=pa, null=na,
           converted_vs_old_built=dict(mean_T_converted=obs, matched_old_built_mean=nm, p=pm),
           by_conversion_decade=by_decade, years_with_data=int((NOBS.max((1, 2)) > 0).sum()),
           PASS_age=bool(r <= -0.2 and pa < 0.05), PASS_converted_vs_old=bool(pm < 0.05 and obs > nm),
           frac_conv=C.driver_test("converted_fraction", frac_conv, +1),
           frac_from_water=C.driver_test("converted_from_water_fraction", frac_from_water, +1))
C.save("X02", res, dict(conv_frac=frac_conv, conv_age=np.where(frac_conv >= 0.3, age, np.nan), old_built_frac=frac_old,
                        conv_from_water=frac_from_water),
       dict(conv_frac="load", conv_age="load", old_built_frac="load", conv_from_water="load"))
