"""L1: Lo et al. 2022 Fig. 14 (MODFLOW-SUB subsidence from registered pumping, contours -1..-8 m in 2010) digitized and
compared with the InSAR sinking maps (sx_prereg.md, local: the PDF is not on the Spark).
Run on the laptop with SX_DATA=<realdata>/semarang/sx (holds bundle.npz). Writes out/L1.json and QA PNGs."""
import os
import fitz
import numpy as np
from scipy import ndimage
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sx_common as C

PDF = "C:/Kuliah/hackathon/agc-26/docs/groundwater-audit-latex-v2/water-14-00201-v2.pdf"
pm = fitz.open(PDF)[18].get_pixmap(dpi=300)
a = np.frombuffer(pm.samples, np.uint8).reshape(pm.h, pm.w, pm.n)[..., :3].astype(float)
# frame and graticule ticks measured on this 300 dpi render (top/bottom and left/right ticks agree within 2 px)
X0, X1, Y0, Y1 = 330, 2135, 1296, 2555                                  # inside the black frame
LON = lambda x: 110 + 20 / 60 + (x - 640.25) / (1424.0 - 640.25) * (5 / 60)
LAT = lambda y: -(6 + 55 / 60) - (y - 1375.5) / (2160.5 - 1375.5) * (5 / 60)
mx, mn = a.max(2), a.min(2)
sat = (mx > 170) & (mx - mn > 110)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
white = ndimage.binary_dilation(ndimage.binary_opening(a.min(2) > 235, iterations=3), iterations=12)
box = np.zeros(sat.shape, bool)
box[Y0:Y1, X0:X1] = True
lab, n = ndimage.label(white & box)                                     # inset charts + legend = big white boxes
big = np.isin(lab, [k + 1 for k, s in enumerate(ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))) if s > 20000])
big = ndimage.binary_fill_holes(big)
cont = sat & box & ~big & (hue > 22) & (hue < 130)                       # green .. orange contour lines (not red dots)
levels = {1: (95, 130), 2: (80, 95), 3: (68, 80), 4: (55, 68), 5: (40, 55), 6: (22, 40)}
val = np.zeros(sat.shape)
for k, (h0, h1) in sorted(levels.items()):
    m = cont & (hue >= h0) & (hue < h1)
    m = ndimage.binary_closing(m, iterations=10 if k <= 2 else 4)       # outer lines are broken by labels
    reg = ndimage.binary_fill_holes(m)
    val[reg] = np.maximum(val[reg], k)
bowl = ndimage.binary_opening(val >= 1, iterations=2)
lab, nb = ndimage.label(bowl)
sizes = ndimage.sum(np.ones_like(lab), lab, range(1, nb + 1))
keep = [k + 1 for k, s in enumerate(sizes) if s >= 150]                 # >= ~0.02 km2
bowl = np.isin(lab, keep)
print("bowls", len(keep), "areas km2", np.round(np.array(sizes)[np.array(keep) - 1] * 11.7 ** 2 / 1e6, 2))
# georeference every bowl pixel to the model grid
yy, xx = np.nonzero(bowl)
iy, ix = C.ll_to_cell(LON(xx), LAT(yy))
G = np.zeros((C.NY, C.NX)); V = np.zeros((C.NY, C.NX))
np.add.at(G, (iy, ix), 1)
iy2, ix2 = C.ll_to_cell(LON(xx), LAT(yy))
np.maximum.at(V, (iy2, ix2), val[yy, xx])
inb = G >= 30                                                           # >= ~10 % of a 200 m cell inside a bowl
cover = (C.LON >= LON(X0)) & (C.LON <= LON(X1)) & (C.LAT <= LAT(Y0)) & (C.LAT >= LAT(Y1))   # Fig. 14 extent
res = dict(n_bowls=len(keep), bowl_cells=int((inb & C.LAND).sum()), frame_cells=int((cover & C.LAND).sum()))
alos = C.B["D_alos"].astype(float)
for name, t in (("s1_2018_22", C.T), ("alos_2006_10", alos)):
    sel = inb & C.LAND & np.isfinite(t)
    obs, pm_, nm = C.matched_p(sel, t=t, pool=cover)
    st = lambda M: np.nanmean(t[M & C.LAND & cover]) if (M & C.LAND & cover & np.isfinite(t)).sum() >= 5 else np.nan
    ps, ns = C.shift_p(st, inb, st(inb), 999)
    res[name] = dict(mean_in_bowls=obs, matched_mean=nm, p_matched=pm_, p_shift=ps, shift_null=ns,
                     mean_in_frame=float(np.nanmean(t[C.LAND & cover])),
                     rho_level_rate_in_bowls=C.rho(V, t, sel),
                     share_fast_cells_in_bowls=float(np.mean(inb[C.LAND & cover & (t > np.nanpercentile(t[C.LAND & cover], 80))])))
res["PASS_s1"] = bool(res["s1_2018_22"]["p_matched"] < 0.05 and res["s1_2018_22"]["p_shift"] < 0.05)
C.save("L1", res, dict(lo2022_model_bowl=inb.astype(float)), dict(lo2022_model_bowl="pumping"))
fig, ax = plt.subplots(1, 2, figsize=(16, 6))
ax[0].imshow(a[Y0:Y1, X0:X1].astype(np.uint8))
ax[0].contour(bowl[Y0:Y1, X0:X1], [0.5], colors="cyan", linewidths=1)
ax[0].imshow(np.ma.masked_where(~big[Y0:Y1, X0:X1], big[Y0:Y1, X0:X1]), alpha=0.3, cmap="gray")
ax[0].set_title("Fig. 14 bowls (cyan), masked insets (grey)")
im = ax[1].imshow(np.where(C.LAND, C.T, np.nan), origin="lower", cmap="RdYlBu_r", vmin=-20, vmax=120,
                  extent=[0, 24, 0, 16])
ax[1].contour(inb, [0.5], colors="k", extent=[0, 24, 0, 16], origin="lower")
ax[1].contour(cover, [0.5], colors="grey", linestyles="--", extent=[0, 24, 0, 16], origin="lower")
plt.colorbar(im, ax=ax[1], label="sinking 2018-22 (mm/yr)")
ax[1].set_title("Model bowls (black) on InSAR sinking; dashed = Fig. 14 extent")
plt.savefig(f"{C.OUT}/L1_fig14.png", dpi=110, bbox_inches="tight")
