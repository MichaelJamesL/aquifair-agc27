"""X19 (stage 2, descriptive): do SHARP changes in the sinking rate follow boundaries of new ground or buildings
(loading signature) more than chance? Statistic: mean |grad T| on the boundary cells of a driver field (top 10 %
of |grad driver| on land) minus mean |grad T| on land; shift null 999."""
import numpy as np
import sx_common as C

F = {}
for f, keys in ((f"{C.OUT}/feat_X02.npz", ("conv_frac", "conv_from_water")), (f"{C.OUT}/feat_X03.npz", ("built_age", "built_1990", "built_growth")),
                (f"{C.OUT}/feat_X01.npz", ("reclaimed_frac",)), (f"{C.OUT}/feat_L3.npz", ("lo2022_soft_thickness",)),
                (f"{C.OUT}/feat_X05.npz", ("elevation_m",))):
    try:
        z = np.load(f)
        F.update({k: z[k] for k in keys})
    except FileNotFoundError:
        print("missing", f)
F["wc_built_2021"] = C.B["wc_built"].astype(float)
gy, gx = np.gradient(np.where(C.LAND, C.T, np.nan), C.PIX / 1000, C.PIX / 1000)
GT = np.hypot(gx, gy)
base = np.nanmean(GT[C.LAND])


def edge(x):
    x = np.where(np.isfinite(x), x, np.nanmedian(x))
    a, b = np.gradient(x)
    g = np.hypot(a, b)
    return C.LAND & (g >= np.nanpercentile(g[C.LAND], 90))


def stat(x):
    e = edge(x) & np.isfinite(GT)
    return np.nanmean(GT[e]) - base if e.sum() >= 20 else np.nan


res = {"mean_grad_T_land": base}
for k, x in F.items():
    o = stat(x)
    p, n = C.shift_p(stat, x, o)
    res[k] = dict(excess_grad=o, p_shift=p, null=n, sharp_edges_follow=bool(p < 0.05 and o > 0))
C.save("X19", res)
