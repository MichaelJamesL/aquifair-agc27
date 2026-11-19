"""X01: land reclaimed from sea or ponds (JRC Global Surface Water 1984-2021) vs sinking (sx_prereg.md)."""
import json
import urllib.request
import numpy as np
import sx_common as C

BASE = "https://storage.googleapis.com/global-surface-water/downloads2021"


def url(layer):
    name = f"{layer}_110E_0Nv1_4_2021.tif"                     # tile 110-120E, 0-10S
    try:
        urllib.request.urlopen(urllib.request.Request(f"{BASE}/{layer}/{name}", method="HEAD"), timeout=60)
        return f"/vsicurl/{BASE}/{layer}/{name}"
    except Exception:
        q = f"https://storage.googleapis.com/storage/v1/b/global-surface-water/o?prefix=downloads2021/{layer}/{layer}_110E"
        it = json.load(urllib.request.urlopen(q, timeout=60))["items"]
        return f"/vsicurl/https://storage.googleapis.com/global-surface-water/{it[0]['name']}"


tr = url("transitions")
lost = C.to_grid(tr, fn=lambda a: np.isin(a, [3, 6]).astype("f4"))          # lost permanent / seasonal water
ever = C.to_grid(tr, fn=lambda a: ((a >= 1) & (a <= 10)).astype("f4"))
occ = C.to_grid(url("occurrence"), nodata=255)
sel = C.LAND & (lost >= 0.25)


def diff(f):
    s = C.LAND & (f >= 0.25)
    return C.T[s].mean() - C.T[C.LAND].mean() if s.sum() >= 5 else np.nan


obs_m, p_m, null_m = C.matched_p(sel)
d = diff(lost)
p_s, ns = C.shift_p(diff, lost, d)
res = dict(n_cells=int(sel.sum()), mean_T_reclaimed=obs_m, matched_null_mean=null_m, excess_vs_matched=obs_m - null_m,
           p_matched=p_m, excess_vs_all_land=d, p_shift=p_s, shift_null=ns,
           PASS=bool(obs_m - null_m >= 10 and p_m < 0.05 and p_s < 0.05),
           lost_fraction=C.driver_test("lost_water_fraction", lost, +1),
           occurrence=C.driver_test("water_occurrence_pct", occ, +1),
           ever_water=C.driver_test("ever_water_fraction", ever, +1))
C.save("X01", res, dict(reclaimed_frac=lost, water_occurrence=occ), dict(reclaimed_frac="load", water_occurrence="load"))
