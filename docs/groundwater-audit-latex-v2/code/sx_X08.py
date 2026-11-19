"""X08: change of sinking over time (ALOS 2006-10, 2014-17, 2018-22, 2023-26) and response to the drop in registered
abstraction (27.7 Mm3 in 2018 -> 10.4 in 2022) at the registered wells (sx_prereg.md). Stage 2 (re-run after X02/X03):
rate ratio vs age of the ground."""
import os
import numpy as np
from scipy import ndimage
import sx_common as C

B = C.B
d15, d18, d23 = (B[f"D_d{k}"].astype(float) for k in ("1517", "1822", "2326"))
alos = B["D_alos"].astype(float)
m = C.LAND
fast = m & (C.T > 30)
per = {k: dict(median_fast=float(np.nanmedian(v[fast])), median_land=float(np.nanmedian(v[m])))
       for k, v in (("alos_2006_10", alos), ("2014_17", d15), ("2018_22", d18), ("2023_26", d23))}
dlt = d23 - d18
W = B["reg_wells_EN"]
WXY = np.c_[W[:, 0] - C.E0, W[:, 1] - C.N0]


def well_mask(xy):
    M = np.zeros((C.NY, C.NX), bool)
    iy, ix = (xy[:, 1] // C.PIX).astype(int), (xy[:, 0] // C.PIX).astype(int)
    ok = (iy >= 0) & (iy < C.NY) & (ix >= 0) & (ix < C.NX)
    M[iy[ok], ix[ok]] = True
    return ndimage.binary_dilation(M, np.ones((3, 3), bool))


WM = well_mask(WXY)
v = m & np.isfinite(dlt)
obs, pm, nm = C.matched_p(WM & v, t=dlt, sign=-1)


def stat(M):
    s = M & v
    return dlt[s].mean() if s.sum() >= 5 else np.nan


ps, ns = C.shift_p(stat, WM, stat(WM), 999, -1)
res = dict(periods=per, change_2326_minus_1822_at_wells=obs, matched_null_mean=nm, p_matched=pm, p_shift=ps,
           shift_null=ns, PASS_pumping_response=bool(pm < 0.05 and ps < 0.05),
           share_fast_slowing_2326_vs_1822=float(np.mean(dlt[fast & np.isfinite(dlt)] < 0)),
           share_fast_slowing_2326_vs_1517=float(np.mean((d23 - d15)[fast & np.isfinite(d23 - d15)] < 0)),
           rho_change_T=C.rho(dlt, C.T, m))
ratio = np.where(np.abs(d15) > 10, d23 / d15, np.nan)
for f, key in ((f"{C.OUT}/feat_X02.npz", "conv_age"), (f"{C.OUT}/feat_X03.npz", "built_age")):
    if os.path.exists(f):
        age = np.load(f)[key]
        r = C.rho(age, ratio, m & (C.T > 20))
        res[f"stage2_rho_{key}_ratio2326_1517"] = r
        res[f"stage2_p_{key}"] = C.shift_p(lambda a: C.rho(a, ratio, m & (C.T > 20)), age, r, 999, +1)[0]
C.save("X08", res, dict(change_2326_1822=dlt, ratio_2326_1517=ratio),
       dict(change_2326_1822="observation", ratio_2326_1517="observation"))
