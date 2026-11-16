import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import synth as S
INK, MUTED, GRID = "#10232b", "#52514e", "#e3e7ea"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
SEQ = LinearSegmentedColormap.from_list("seq", ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"])
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK, "axes.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 8.5,
                     "axes.titleweight": "bold", "axes.titlelocation": "left", "pdf.fonttype": 42})
R = json.load(open("results.json")); SUM = json.load(open("summary.json"))
ex = np.load("example.npz")
EXT = [0, S.NX * S.PIX / 1000, 0, S.NY * S.PIX / 1000]

# ---------------- Figure 1: example scenario ----------------
fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.45), constrained_layout=True)
d = np.ma.masked_where(~ex["mask"], ex["d"])
cm = SEQ.copy(); cm.set_bad("#dfe3e6")
im = ax[0].imshow(d, origin="lower", extent=EXT, cmap=cm, vmin=0, vmax=np.percentile(ex["d"], 99.8))
ax[0].set_title("a  Simulated map")
cb = fig.colorbar(im, ax=ax[0], shrink=0.75, pad=0.02); cb.set_label("sinking rate (mm/yr)"); cb.outline.set_visible(False)
qs = ex["qsmooth"].reshape(S.NCY, S.NCX)
im2 = ax[1].imshow(qs, origin="lower", extent=EXT, cmap=SEQ, vmin=0, vmax=qs.max())
ax[1].scatter(ex["smooth_src"][:, 0] / 1000, ex["smooth_src"][:, 1] / 1000, s=9, marker="x", color=ORANGE, linewidths=0.8)
ax[1].set_title(f"b  Smooth: {len(ex['smooth_src'])} peaks")
ax[2].contour(S.XX / 1000, S.YY / 1000, ex["v_src"], levels=[5, 15, 30], colors=GRID, linewidths=0.6)
sc = lambda q: 6 + q * 0.55
ax[2].scatter(ex["pts"][:, 0] / 1000, ex["pts"][:, 1] / 1000, s=sc(ex["q"]), facecolors="none", edgecolors=INK, linewidths=0.9, zorder=3)
ax[2].scatter(ex["est"][:, 0] / 1000, ex["est"][:, 1] / 1000, s=sc(ex["est"][:, 2]), color=BLUE, alpha=0.75, linewidths=0, zorder=2)
ax[2].set_title(f"c  Sparse: {len(ex['est'])} sources")
ax[2].set_xlim(EXT[:2]); ax[2].set_ylim(EXT[2:]); ax[2].set_aspect("equal")
ax[2].text(0.4, 0.5, "ring = true source\ndot = recovered\nsize = volume", fontsize=6.5, color=MUTED, va="bottom")
for a in ax:
    a.set_xlabel("east (km)"); a.tick_params(length=2)
ax[0].set_ylabel("north (km)")
ax[1].text(0.4, 0.5, "x = picked peak", fontsize=6.5, color=ORANGE, va="bottom")
fig.savefig("../tex/fig/example.pdf"); fig.savefig("example.png", dpi=170)

# ---------------- Figure 2: volumes ----------------
fig, ax = plt.subplots(1, 2, figsize=(7.0, 3.0), constrained_layout=True, sharex=True, sharey=True)
for a, key, col, ttl in [(ax[0], "cal", BLUE, "a  Cone width known"), (ax[1], "cv", ORANGE, "b  Cone width chosen by cross-validation")]:
    mm = [x for e in R["E1"] for x in e[key]["matched"]]
    qt = np.array([x["q_true"] for x in mm]); qe = np.array([x["q_est"] for x in mm])
    lo = np.array([x["lo"] for x in mm]); hi = np.array([x["hi"] for x in mm])
    a.plot([30, 900], [30, 900], color=MUTED, lw=0.8, zorder=1)
    a.plot([30, 900], [30 * 1.25, 900 * 1.25], color=GRID, lw=0.8, zorder=0); a.plot([30, 900], [30 * 0.75, 900 * 0.75], color=GRID, lw=0.8, zorder=0)
    a.vlines(qt, np.maximum(lo, 12), hi, color=col, lw=0.5, alpha=0.35, zorder=2)
    a.scatter(qt, qe, s=9, color=col, edgecolors="white", linewidths=0.4, zorder=3)
    a.set_xscale("log"); a.set_yscale("log"); a.set_xlim(35, 450); a.set_ylim(12, 1100)
    a.set_title(ttl); a.set_xlabel("true volume (thousand m$^3$/yr)")
    a.grid(True, color=GRID, lw=0.4); a.set_axisbelow(True)
    a.set_xticks([50, 100, 200, 400]); a.set_xticks([], minor=True); a.set_xticklabels(["50", "100", "200", "400"])
    a.set_yticks([25, 50, 100, 200, 400, 800]); a.set_yticks([], minor=True); a.set_yticklabels(["25", "50", "100", "200", "400", "800"])
ax[0].set_ylabel("estimated volume (thousand m$^3$/yr)")
ax[0].text(160, 200, "perfect", fontsize=6.5, color=MUTED, rotation=33, ha="center", va="bottom")
ax[0].text(330, 215, "±25 %", fontsize=6.5, color=MUTED, rotation=33, ha="center", va="top")
ax[0].text(40, 780, "bars: 90 % range", fontsize=6.5, color=MUTED)
fig.savefig("../tex/fig/volumes.pdf"); fig.savefig("volumes.png", dpi=170)

# ---------------- Figure 3: limits ----------------
fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.35), constrained_layout=True)
e2 = SUM["e2"]; sd = [e2[k]["sd"] for k in e2]
ax[0].plot(sd, [100 * e2[k]["recall"] for k in e2], color=BLUE, lw=1.6, marker="o", ms=4, mec="white", mew=0.6)
ax[0].plot(sd, [100 * e2[k]["precision"] for k in e2], color=ORANGE, lw=1.6, marker="o", ms=4, mec="white", mew=0.6)
ax[0].text(5.0, 97, "recall: sources found", color=INK, ha="center", fontsize=7)
ax[0].text(5.6, 48, "precision: detections\nthat are real", color=INK, ha="center", fontsize=7)
ax[0].set_ylim(0, 105); ax[0].set_xlim(0, 9.2); ax[0].set_xlabel("noise in the rate map (mm/yr)"); ax[0].set_ylabel("% of sources")
ax[0].set_title("a  Noise")
e3 = SUM["e3"]; sep = [float(k) * 1.5 for k in e3]
ax[1].plot(sep, [100 * e3[k]["res"] for k in e3], color=BLUE, lw=1.6, marker="o", ms=4, mec="white", mew=0.6)
ax[1].axvline(1.5, color=MUTED, lw=0.6, ls=(0, (3, 3))); ax[1].text(1.58, 4, "cone width B", fontsize=6.5, color=MUTED)
ax[1].set_ylim(0, 105); ax[1].set_xlim(0, 4.8); ax[1].set_xlabel("distance between two sources (km)"); ax[1].set_ylabel("% of trials told apart")
ax[1].set_title("b  Resolution")
e4 = SUM["e4"]; ks = [k for k in e4 if k.startswith("k0")]; bw = [float(k.split("_")[1]) / 1000 for k in ks]
ax[2].axhline(1.0, color=MUTED, lw=0.6); ax[2].axvline(1.5, color=MUTED, lw=0.6, ls=(0, (3, 3)))
ax[2].plot(bw, [e4[k]["tot_med"] for k in ks], color=BLUE, lw=1.6, marker="o", ms=4, mec="white", mew=0.6)
ax[2].text(1.56, 0.12, "true B", fontsize=6.5, color=MUTED); ax[2].text(0.72, 1.04, "correct total", fontsize=6.5, color=MUTED)
ax[2].set_ylim(0, 2.3); ax[2].set_xlim(0.6, 2.65); ax[2].set_xlabel("assumed cone width B (km)"); ax[2].set_ylabel("estimated / true total volume")
ax[2].set_title("c  Cone width")
for a in ax:
    a.grid(True, axis="y", color=GRID, lw=0.4); a.set_axisbelow(True); a.tick_params(length=2)
fig.savefig("../tex/fig/limits.pdf"); fig.savefig("limits.png", dpi=170)
print("ok", len(ex["pts"]), len(ex["est"]), len(ex["smooth_src"]), len(ex["bowls"]))
