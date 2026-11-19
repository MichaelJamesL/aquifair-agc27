"""Registered-well location test, exactly as pre-registered in sem_wells_prereg.md.

Truth: deep (registry) wells digitized from Lo et al. 2022 Fig. 12 (sem_wells_digitize.py).
T-A (map): mean 3x3 sinking rate at the well cells vs (a) uniform land cells, (b) cells from the
same built-up quintile, (c) the whole well pattern shifted >= 2 km (wrapped). PASS: p < 0.05 vs b and c.
T-B (bowls): share of detected bowls with a well within 1 km vs (a) random bowls, (b) built-matched
bowls, (c) shifted wells. PASS: p < 0.05 vs b and c. Also reported: ALOS 2006-10, T-B at 500 m / 2 km,
and 200 repeats with every well jittered by the georeference RMS. Post hoc (labelled, not judged):
the same tests with all draws restricted to the Fig. 12 model domain (black outline on the map).
Writes exp/registry_wells_test.json and registry_wells/registry_wells_map.png."""
import json
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
import synth as S
import real_goal_maps as GM

ROOT = GM.ROOT
NDRAW, NJIT, SHIFT_MIN, TOLS = 10000, 200, 2000.0, (500.0, 1000.0, 2000.0)
WX, WY = S.NX * S.PIX, S.NY * S.PIX
lc = np.load(f"{ROOT}/worldcover_grid.npz")
water, built = lc["water"], lc["built"]
csv = np.genfromtxt(f"{ROOT}/registry_wells/fig12_wells.csv", delimiter=",", names=True)
geo = json.load(open(f"{ROOT}/registry_wells/fig12_georef.json"))
W0 = np.c_[csv["E"] - GM.grid.E0, csv["N"] - GM.grid.N0]

# pattern-shift offsets: whole cells, wrapped (minimum-image) length >= 2 km
oy, ox = np.mgrid[:S.NY, :S.NX]
olen = S.PIX * np.hypot(np.minimum(ox, S.NX - ox), np.minimum(oy, S.NY - oy))
OFF = np.c_[ox[olen >= SHIFT_MIN], oy[olen >= SHIFT_MIN]] * float(S.PIX)


def pval(null, obs):
    null = null[np.isfinite(null)]
    return float((1 + (null >= obs - 1e-9).sum()) / (1 + len(null)))


def lin(p):
    """Cell index (row-major) of points in grid metres, and whether they are inside the grid."""
    ix, iy = np.floor(p[..., 0] / S.PIX).astype(int), np.floor(p[..., 1] / S.PIX).astype(int)
    ins = (ix >= 0) & (ix < S.NX) & (iy >= 0) & (iy < S.NY)
    return iy.clip(0, S.NY - 1) * S.NX + ix.clip(0, S.NX - 1), ins


class Map:
    def __init__(s, D, mask):
        s.land = (mask & (water < 0.5)).ravel()
        Dz = np.where(s.land.reshape(S.NY, S.NX), np.nan_to_num(D), 0.0)
        k = np.ones((3, 3))
        s.loc3 = (ndimage.convolve(Dz, k, mode="constant") /
                  np.maximum(ndimage.convolve(s.land.reshape(S.NY, S.NX) * 1.0, k, mode="constant"), 1)).ravel()
        s.cells = np.flatnonzero(s.land)
        b = built.ravel()[s.cells]
        rank = np.empty(len(b), int)
        rank[np.lexsort((s.cells, b))] = np.arange(len(b))          # ties broken by cell index
        s.quint = np.full(S.NX * S.NY, -1)
        s.quint[s.cells] = 5 * rank // len(b)
        s.qcells = [s.cells[s.quint[s.cells] == q] for q in range(5)]
        s.cxy = np.c_[S.XX.ravel(), S.YY.ravel()]

    def keep(s, p):
        l, ins = lin(p)
        return ins & s.land[l]

    def draws(s, lobs, rng):
        """(a) uniform and (b) built-quintile-matched land cells, each (NDRAW, len(lobs))."""
        a = rng.choice(s.cells, (NDRAW, len(lobs)))
        b = np.stack([rng.choice(s.qcells[s.quint[l]], NDRAW) for l in lobs], 1)
        return a, b

    def shifted(s, wells, rng):
        """(NDRAW, k, 2) shifted well positions and their on-land flags."""
        off = OFF[rng.integers(len(OFF), size=NDRAW)]
        P = (wells[None] + off[:, None]) % np.array([WX, WY])
        return P, s.keep(P)


def test_A(m, wells, rng):
    L = m.loc3
    obs = float(L[lin(wells)[0]].mean())
    a, b = m.draws(lin(wells)[0], rng)
    P, ok = m.shifted(wells, rng)
    c = np.where(ok.any(1), (L[lin(P)[0]] * ok).sum(1) / np.maximum(ok.sum(1), 1), np.nan)
    nulls = dict(uniform=L[a].mean(1), built=L[b].mean(1), shift=c)
    out = dict(n=int(len(wells)), obs_mean_rate=obs, median_rate_at_wells=float(np.median(L[lin(wells)[0]])))
    for k, v in nulls.items():
        out[f"null_{k}"] = float(np.nanmean(v))
        out[f"p_{k}"] = pval(v, obs)
    out["shift_mean_wells_kept"] = float(ok.sum(1).mean())
    out["pass"] = bool(out["p_built"] < 0.05 and out["p_shift"] < 0.05)
    return out


def test_B(m, wells, bowls, rng):
    dmap = cKDTree(wells).query(m.cxy)[0]                         # every cell centre -> nearest well
    dobs = cKDTree(wells).query(bowls)[0]
    a, b = m.draws(lin(bowls)[0], rng)
    P, ok = m.shifted(wells, rng)
    dsh = np.empty((NDRAW, len(bowls)))
    for i in range(0, NDRAW, 500):                                # chunks keep memory small
        d = np.hypot(bowls[None, :, None, 0] - P[i:i + 500, None, :, 0], bowls[None, :, None, 1] - P[i:i + 500, None, :, 1])
        dsh[i:i + 500] = np.where(ok[i:i + 500, None, :], d, np.inf).min(2)
    out = dict(n_bowls=int(len(bowls)), n_wells=int(len(wells)))
    for tol in TOLS:
        r = dict(obs_share=float((dobs <= tol).mean()))
        for k, v in dict(uniform=(dmap[a] <= tol).mean(1), built=(dmap[b] <= tol).mean(1), shift=(dsh <= tol).mean(1)).items():
            r[f"null_{k}"] = float(v.mean())
            r[f"p_{k}"] = pval(v, r["obs_share"])
        r["pass"] = bool(r["p_built"] < 0.05 and r["p_shift"] < 0.05)
        out[f"{int(tol)}m"] = r
    return out


def verdict(pa, pb):
    if pa and pb:
        return "InSAR sinking identifies areas with registered pumping in Semarang (location only, no volumes)"
    if pa:
        return "map-level association, bowls not supported"
    return "sinking areas cannot be labelled pumping areas"


def run(D, mask, bowls_all, rng):
    m = Map(D, mask)
    ins = lin(W0)[1]
    kw = m.keep(W0)
    kb = m.keep(bowls_all)
    wells, bowls = W0[kw], bowls_all[kb]
    A, B = test_A(m, wells, rng), test_B(m, wells, bowls, rng)
    qw = np.bincount(m.quint[lin(wells)[0]], minlength=5)
    return m, kw, kb, dict(wells_in_grid=int(ins.sum()), wells_kept=int(kw.sum()),
                           wells_dropped_nonland=int((ins & ~kw).sum()), wells_per_built_quintile=qw.tolist(),
                           land_cells=int(len(m.cells)), land_median_rate=float(np.nanmedian(np.asarray(D).ravel()[m.cells])),
                           bowls_detected=int(len(bowls_all)), bowls_kept=int(kb.sum()),
                           T_A=A, T_B=B, verdict=verdict(A["pass"], B["1000m"]["pass"]))


# ---- self-check of the null machinery ------------------------------------------------------
assert (olen[(OFF[:, 1] // S.PIX).astype(int), (OFF[:, 0] // S.PIX).astype(int)] >= SHIFT_MIN).all()
assert pval(np.array([0.0, 1.0, 2.0]), 2.0) == 0.5 and pval(np.zeros(9), 1.0) == 0.1

rng = np.random.default_rng(2026)
D1, mask1, _, _ = GM.load("da", "1822")
b1 = np.array(json.load(open(f"{ROOT}/exp/cfar_final.json"))["truth"]["sources"])[:, :2]
za = np.load(f"{ROOT}/alos/alos_rate_grid.npz")
ba = np.array(json.load(open(f"{ROOT}/exp/alos_result.json"))["detections"]["sources"])[:, :2]
m1, kw1, kb1, s1 = run(D1, mask1, b1, rng)
assert max(len(q) for q in m1.qcells) - min(len(q) for q in m1.qcells) <= 1
ma, kwa, kba, al = run(za["D"], za["mask"], ba, rng)

# ---- digitizing-error sensitivity (Sentinel-1 2018-22, the judged map) -----------------------
sig = geo["georef_rms_for_jitter_m"] / np.sqrt(2)                 # per axis, so the radial RMS = georef RMS
jr = np.random.default_rng(7)
rows = []
for t in range(NJIT):
    Wj = W0 + jr.normal(0, sig, W0.shape)
    w = Wj[m1.keep(Wj)]
    A, B = test_A(m1, w, jr), test_B(m1, w, b1[kb1], jr)
    rows.append((A["pass"], B["1000m"]["pass"], A["p_built"], A["p_shift"], B["1000m"]["p_built"], B["1000m"]["p_shift"]))
J = np.array(rows, float)
jit = dict(radial_rms_m=geo["georef_rms_for_jitter_m"], repeats=NJIT, share_pass_A=float(J[:, 0].mean()),
           share_pass_B=float(J[:, 1].mean()), share_pass_both=float((J[:, 0] * J[:, 1]).mean()),
           median_p=dict(A_built=float(np.median(J[:, 2])), A_shift=float(np.median(J[:, 3])),
                         B_built=float(np.median(J[:, 4])), B_shift=float(np.median(J[:, 5]))))

# ---- post hoc, NOT pre-registered: nulls restricted to the Fig. 12 model domain ----------------
# Fig. 12 only shows wells inside the Lo et al. model domain (it ends near grid x = 17 km), so the
# pre-registered nulls also draw from areas where no well could have been plotted.
fa = np.asarray(Image.open(f"{ROOT}/registry_wells/fig12.png")).astype(int)
paint = ndimage.binary_closing((fa.min(2) <= 235) & (fa.max(2) >= 60), np.ones((5, 5)))   # hatched zones: not sea, not text
lab, _ = ndimage.label(paint)
dom_px = ndimage.binary_fill_holes(lab == np.argmax(np.bincount(lab.ravel())[1:]) + 1)
glon, glat = GM.grid.inv.transform(S.XX + GM.grid.E0, S.YY + GM.grid.N0)
cl, ca = geo["affine_lon"], geo["affine_lat"]                     # cross terms ~1e-13: invert per axis
gpx, gpy = np.round((glon - cl[2]) / cl[0]).astype(int), np.round((glat - ca[2]) / ca[1]).astype(int)
inf = (gpx >= 0) & (gpx < fa.shape[1]) & (gpy >= 0) & (gpy < fa.shape[0])
domain = np.zeros((S.NY, S.NX), bool)
domain[inf] = dom_px[gpy[inf], gpx[inf]]
lw0, in0 = lin(W0)
assert domain.ravel()[lw0[in0]].mean() > 0.9                     # the wells lie in the domain
pr = np.random.default_rng(99)
post = dict(note="post hoc, not pre-registered; nulls and bowls restricted to the Fig. 12 model domain",
            domain_cells=int(domain.sum()),
            s1_2018_22=run(D1, mask1 & domain, b1, pr)[3], alos_2006_10=run(za["D"], za["mask"] & domain, ba, pr)[3])

out = dict(design="sem_wells_prereg.md", truth="Lo et al. 2022 Fig. 12 deep wells (ESDM registry), digitized",
           n_digitized=int(len(W0)), georef=dict(tick_rms_m=geo["tick_rms_m"], coastline=geo["coastline_check"],
                                                  east_river=geo["east_river_check"]),
           draws=NDRAW, s1_2018_22=s1, alos_2006_10=al, jitter_s1=jit, post_hoc_domain=post)
json.dump(out, open(f"{ROOT}/exp/registry_wells_test.json", "w"), indent=1)

# ---- map ----------------------------------------------------------------------------------
fig, ax = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
ext = [0, WX / 1e3, 0, WY / 1e3]
for a_, D, m, kw, bw, kb, r, t in ((ax[0], D1, m1, kw1, b1, kb1, s1, "Sentinel-1 2018-22"),
                                   (ax[1], za["D"], ma, kwa, ba, kba, al, "ALOS-1 2006-10")):
    im = a_.imshow(np.where(m.land.reshape(S.NY, S.NX), D, np.nan), origin="lower", extent=ext, cmap="RdYlBu_r", vmin=-20, vmax=120)
    a_.plot(W0[kw, 0] / 1e3, W0[kw, 1] / 1e3, "o", mfc="lime", mec="k", ms=4, label=f"registry wells kept ({kw.sum()})")
    a_.plot(W0[~kw, 0] / 1e3, W0[~kw, 1] / 1e3, "o", mfc="none", mec="k", ms=4, label="wells dropped")
    a_.plot(bw[kb, 0] / 1e3, bw[kb, 1] / 1e3, "mx", ms=6, mew=1.5, label=f"detected bowls ({kb.sum()})")
    for x, y in bw[kb]:
        a_.add_patch(plt.Circle((x / 1e3, y / 1e3), 1.0, fill=False, ec="m", lw=0.5))
    A, B = r["T_A"], r["T_B"]["1000m"]
    a_.set_title(f"{t}: T-A p(built)={A['p_built']:.3f} p(shift)={A['p_shift']:.3f}; "
                 f"T-B p(built)={B['p_built']:.3f} p(shift)={B['p_shift']:.3f}", fontsize=9)
    a_.contour(S.XX[0] / 1e3, S.YY[:, 0] / 1e3, domain, [0.5], colors="k", linewidths=0.6)
    a_.set_xlim(0, WX / 1e3); a_.set_ylim(0, WY / 1e3); a_.set_xlabel("km east of grid origin"); a_.set_ylabel("km north")
ax[0].legend(loc="lower left", fontsize=7)
fig.colorbar(im, ax=ax, shrink=0.8, label="vertical rate (mm/yr, + sinking)")
fig.savefig(f"{ROOT}/registry_wells/registry_wells_map.png", dpi=130)

brief = lambda r: dict(kept=r["wells_kept"], bowls=r["bowls_kept"], T_A={k: r["T_A"][k] for k in ("obs_mean_rate", "null_uniform", "null_built", "null_shift", "p_uniform", "p_built", "p_shift", "pass")},
                       T_B={t: {k: v for k, v in r["T_B"][t].items()} for t in ("500m", "1000m", "2000m")}, verdict=r["verdict"])
print(json.dumps(dict(s1=brief(s1), alos=brief(al), jitter=jit, post_hoc_domain=dict(cells=post["domain_cells"],
                 s1=brief(post["s1_2018_22"]), alos=brief(post["alos_2006_10"]))), indent=1))
