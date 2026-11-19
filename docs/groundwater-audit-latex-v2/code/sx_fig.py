"""Summary figure for the subsidence-cause experiments (experiments/14): sinking map with observation-well head decline,
soft-sediment thickness, new ground, and sinking vs thickness / head decline. Local: SX_DATA=<realdata>/semarang/sx."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sx_common as C

O = C.OUT
thk = np.load(f"{O}/feat_L3.npz")["lo2022_soft_thickness"]
x2 = np.load(f"{O}/feat_X02.npz")
x3 = np.load(f"{O}/feat_X03.npz")
L4 = json.load(open(f"{O}/L4.json"))
L3 = json.load(open(f"{O}/L3.json"))
ext = [0, 24, 0, 16]
land = lambda a: np.where(C.LAND, a, np.nan)
fig, ax = plt.subplots(2, 3, figsize=(18, 10))
im = ax[0, 0].imshow(land(C.T), origin="lower", extent=ext, cmap="RdYlBu_r", vmin=-10, vmax=120)
plt.colorbar(im, ax=ax[0, 0], label="mm/yr")
WLL = {"O1": (110.35995, -6.98886), "O2": (110.39005, -6.96244), "O3": (110.40163, -6.96693), "O4": (110.42466, -6.97980),
       "O5": (110.43009, -6.99474), "O6": (110.45530, -6.95920)}
for r in L4["wells"]:
    E, N = C.FW.transform(*WLL[r["well"]])
    ax[0, 0].plot((E - C.E0) / 1000, (N - C.N0) / 1000, "k*", ms=11)
    ax[0, 0].annotate(f'{r["well"]}: head drop {r["head_decline_m"]:.0f} m', ((E - C.E0) / 1000 + 0.3, (N - C.N0) / 1000 + 0.2), fontsize=8)
ax[0, 0].set_title("(a) Sinking 2018-22; head drop 1990-2010 at wells")
im = ax[0, 1].imshow(land(thk), origin="lower", extent=ext, cmap="viridis")
plt.colorbar(im, ax=ax[0, 1], label="m")
for h in L3["boreholes"]:
    E, N = C.FW.transform(h["lon"], h["lat"])
    ax[0, 1].plot((E - C.E0) / 1000, (N - C.N0) / 1000, "r^", ms=6)
ax[0, 1].set_title("(b) Soft sediment thickness (Lo et al. Fig. 5 boreholes)")
age = x2["conv_age"]
im = ax[0, 2].imshow(land(2020 - age), origin="lower", extent=ext, cmap="plasma", vmin=1990, vmax=2020)
plt.colorbar(im, ax=ax[0, 2], label="year turned into built/bare (Landsat)")
ax[0, 2].set_title("(c) New ground: year turned built/bare (Landsat)")
m = C.LAND & np.isfinite(thk)
cf = x2["conv_frac"]
sc = ax[1, 0].scatter(thk[m], C.T[m], c=cf[m], s=4, cmap="magma_r", vmin=0, vmax=1)
plt.colorbar(sc, ax=ax[1, 0], label="share of cell converted since 1988")
ax[1, 0].set_xlabel("soft sediment thickness (m)"); ax[1, 0].set_ylabel("sinking 2018-22 (mm/yr)")
ax[1, 0].set_title("(d) Sinking vs soft thickness")
hd = [r["head_decline_m"] for r in L4["wells"]]
ax[1, 1].scatter(hd, [r["sinking_1822"] for r in L4["wells"]], c="k", label="Sentinel-1 2018-22")
ax[1, 1].scatter(hd, [r["sinking_alos"] for r in L4["wells"]], facecolors="none", edgecolors="b", label="ALOS 2006-10")
xx = np.linspace(0, 32, 10)
ax[1, 1].plot(xx, xx / 20 * 100, "g--", label="0.1 m sinking per m head drop")
for r in L4["wells"]:
    ax[1, 1].annotate(r["well"], (r["head_decline_m"] + 0.4, r["sinking_1822"] + 2), fontsize=9)
ax[1, 1].set_xlabel("head decline 1990-2010 (m)"); ax[1, 1].set_ylabel("sinking (mm/yr)"); ax[1, 1].legend(fontsize=8)
ax[1, 1].set_title("(e) 6 observation wells (exploratory)")
gr = x3["built_growth"]
ax[1, 2].scatter(gr[C.LAND], C.geo_resid()[C.LAND], s=3, alpha=0.4)
ax[1, 2].axhline(0, color="k", lw=0.5)
ax[1, 2].set_xlabel("built-up growth 2000-2020 (GHSL, share of cell)"); ax[1, 2].set_ylabel("sinking minus geography baseline (mm/yr)")
ax[1, 2].set_title("(f) Built-up growth vs sinking beyond geography")
for a in ax[0]:
    a.set_xlabel("km east"); a.set_ylabel("km north")
for a in ax.ravel():
    a.title.set_fontsize(10)
plt.tight_layout()
plt.savefig(f"{O}/sx_summary.png", dpi=100)
print("saved", f"{O}/sx_summary.png")
