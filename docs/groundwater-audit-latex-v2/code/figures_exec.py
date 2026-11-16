# Executive-summary figure: from the radar map to the audit list (simulated example, seed 103)
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import synth as S
INK, MUTED, GRID = "#10232b", "#52514e", "#e3e7ea"
BLUE = "#2a78d6"
SEQ = LinearSegmentedColormap.from_list("seq", ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"])
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK, "axes.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 8.5,
                     "axes.titleweight": "bold", "axes.titlelocation": "left", "pdf.fonttype": 42})
ex = np.load("example.npz")
EXT = [0, S.NX * S.PIX / 1000, 0, S.NY * S.PIX / 1000]
est, ci, stab = ex["est"], ex["ci"], ex["stab"]
order = np.argsort(-est[:, 2]); rank = {j: i + 1 for i, j in enumerate(order)}

fig, ax = plt.subplots(1, 3, figsize=(6.55, 2.25), constrained_layout=True, gridspec_kw={"width_ratios": [1.12, 1.0, 0.95]})
d = np.ma.masked_where(~ex["mask"], ex["d"]); cm = SEQ.copy(); cm.set_bad("#dfe3e6")
im = ax[0].imshow(d, origin="lower", extent=EXT, cmap=cm, vmin=0, vmax=np.percentile(ex["d"], 99.8))
ax[0].set_title("Input: the sinking map")
cb = fig.colorbar(im, ax=ax[0], shrink=0.8, pad=0.02); cb.set_label("mm/yr"); cb.outline.set_visible(False); cb.ax.tick_params(length=2)
ax[1].contour(S.XX / 1000, S.YY / 1000, ex["v_src"], levels=[5, 15, 30], colors=GRID, linewidths=0.6)
sc = lambda q: 10 + q * 0.6
ax[1].scatter(ex["pts"][:, 0] / 1000, ex["pts"][:, 1] / 1000, s=sc(ex["q"]), facecolors="none", edgecolors=INK, linewidths=0.8, zorder=3)
ax[1].scatter(est[:, 0] / 1000, est[:, 1] / 1000, s=sc(est[:, 2]), color=BLUE, alpha=0.8, linewidths=0, zorder=2)
for j in range(len(est)):
    ax[1].annotate(str(rank[j]), (est[j, 0] / 1000, est[j, 1] / 1000), xytext=(5, 5), textcoords="offset points", fontsize=7, fontweight="bold", color=INK)
ax[1].set_title("Output: sources located")
ax[1].set_xlim(EXT[:2]); ax[1].set_ylim(EXT[2:]); ax[1].set_aspect("equal")
ax[1].text(0.5, 0.5, "dot = found, ring = truth", fontsize=6.2, color=MUTED, va="bottom")
for a in ax[:2]:
    a.set_xlabel("east (km)"); a.tick_params(length=2)
ax[0].set_ylabel("north (km)")
y = np.arange(len(order))[::-1]
q = est[order, 2]; lo = ci[order, 0]; hi = ci[order, 2]
ax[2].barh(y, q, height=0.62, color=BLUE)
ax[2].hlines(y, lo, hi, color=INK, lw=0.9)
for yy, qq, hh, ss in zip(y, q, hi, stab[order]):
    ax[2].text(max(qq, hh) + 8, yy, f"{qq:.0f}", va="center", fontsize=6.8)
ax[2].set_yticks(y); ax[2].set_yticklabels([str(i + 1) for i in range(len(order))]); ax[2].tick_params(length=0, axis="y"); ax[2].tick_params(length=2, axis="x")
ax[2].set_xlim(0, 360); ax[2].set_xlabel("thousand m$^3$ per year")
ax[2].text(355, 0.0, "line = 90 % range", fontsize=6.2, color=MUTED, ha="right", va="center")
ax[2].set_ylabel("rank"); ax[2].set_title("Output: the audit list")
ax[2].spines["left"].set_visible(False)
fig.savefig("../tex/fig/exec_solution.pdf"); fig.savefig("exec_solution.png", dpi=200)
print(order, q.round(0), lo.round(0), hi.round(0))
