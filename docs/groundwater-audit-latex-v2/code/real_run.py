"""Run the sparse audit on a real LiCSAR stack and check source locations against known deep wells.

Usage: python real_run.py STACKDIR WELLS.tab E0 N0 EPSG
  STACKDIR/stack.npz from real_fetch.py; WELLS.tab = PANGAEA text export; (E0, N0) = SW corner of
  the 24 x 16 km model grid in the given UTM EPSG. Writes STACKDIR/real_result.json and real_map.png.
"""
import sys, json
import numpy as np
from pyproj import Transformer
import synth as S

stackdir, wellfile, E0, N0, epsg = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
LAM = 0.055465763                       # Sentinel-1 C-band wavelength, m
z = np.load(f"{stackdir}/stack.npz")
pairs = z["pairs"]
unw, cc = z["unw"], z["cc"]
dt = np.array([(np.datetime64(f"{p[9:13]}-{p[13:15]}-{p[15:]}") - np.datetime64(f"{p[:4]}-{p[4:6]}-{p[6:8]}")).astype(int)
               for p in pairs]) / 365.25
hgt, U, land = z["hgt"], z["U"], z["landmask"]
a, b, c, d_, e, f = z["transform"]

# 1. LOS velocity by phase stacking: v = sum(phase) / sum(dt) over valid pairs, each pair referenced
#    to the median of high ground (> 60 m, the stable hills south of the coastal plain).
#    shortcut: no GACOS / no SBAS time series; stacking ~400 short pairs averages atmosphere down.
valid = np.isfinite(unw) & (unw != 0) & (cc >= 0.15 * 255)   # 0.3 keeps only ~16 % of pixels here
ref = (hgt > 60) & (land > 0)
los = np.where(valid, unw, 0.0)
for k in range(len(pairs)):
    r = valid[k] & ref
    if r.sum() < 50:
        valid[k] = False
        continue
    los[k] = np.where(valid[k], unw[k] - np.median(unw[k][r]), 0.0)
los_mm = los * (-LAM / (4 * np.pi) * 1000)           # LiCSBAS convention: + = towards satellite
n = valid.sum(0)
sum_dt = (valid * dt[:, None, None]).sum(0)
v_los = np.where(n > 0, los_mm.sum(0) / np.maximum(sum_dt, 1e-9), np.nan)
frac = n / len(pairs)
v_up = v_los / np.where(U > 0.1, U, np.nan)            # assume vertical motion only
sub = -v_up                                            # subsidence rate, mm/yr, + = sinking

# 2. Resample to the 200 m UTM model grid by block mean.
ny, nx = sub.shape
lon = a * (np.arange(nx) + 0.5) + c
lat = e * (np.arange(ny) + 0.5) + f
LON, LAT = np.meshgrid(lon, lat)
fw = Transformer.from_crs(4326, epsg, always_xy=True)
E, N = fw.transform(LON, LAT)
ix = ((E - E0) // S.PIX).astype(int)
iy = ((N - N0) // S.PIX).astype(int)
ok = (ix >= 0) & (ix < S.NX) & (iy >= 0) & (iy < S.NY) & np.isfinite(sub) & (frac >= 0.5) & (land > 0)
lin = iy[ok] * S.NX + ix[ok]
cnt = np.bincount(lin, minlength=S.NX * S.NY)
D = (np.bincount(lin, sub[ok], minlength=S.NX * S.NY) / np.maximum(cnt, 1)).reshape(S.NY, S.NX)
H = (np.bincount(lin, hgt[ok], minlength=S.NX * S.NY) / np.maximum(cnt, 1)).reshape(S.NY, S.NX)
mask = (cnt >= 2).reshape(S.NY, S.NX)
clay_obs = np.clip((20.0 - H) / 20.0, 0, 1.3)          # shortcut: low ground ~ thick soft clay; swap in a clay map
sc = dict(d=np.where(mask, D, 0.0), mask=mask, clay_obs=clay_obs)

# 3. Known deep wells (truth for locations only).
rows = [l.rstrip("\n").split("\t") for l in open(wellfile, encoding="utf-8")]
i0 = [k for k, l in enumerate(rows) if l[0] == "*/"][0]
W = rows[i0 + 2:]
we, wn = fw.transform([float(r[4]) for r in W], [float(r[3]) for r in W])
wx, wy = np.array(we) - E0, np.array(wn) - N0
obs = np.array(["obs" in r[1].lower() or r[0].startswith("SP_") for r in W])
inside = (wx > 0) & (wx < S.NX * S.PIX) & (wy > 0) & (wy < S.NY * S.PIX)
wells_all = np.c_[wx, wy][inside]
wells_prod = np.c_[wx, wy][inside & ~obs]


def near_rate(src, wells, tol=1000.0):
    if len(src) == 0:
        return float("nan")
    dmin = np.hypot(src[:, None, 0] - wells[None, :, 0], src[:, None, 1] - wells[None, :, 1]).min(1)
    return float((dmin <= tol).mean())


rng = np.random.default_rng(0)
mpix = np.flatnonzero(mask.ravel())


def null_rate(k, wells, n=5000):
    """Hit rate of k sources dropped at random coherent land pixels."""
    if k == 0:
        return np.array([np.nan])
    pick = rng.choice(mpix, (n, k))
    pts = np.stack([S.XX.ravel()[pick], S.YY.ravel()[pick]], -1)
    dmin = np.hypot(pts[..., None, 0] - wells[:, 0], pts[..., None, 1] - wells[:, 1]).min(-1)
    return (dmin <= 1000).mean(1)


def null_weighted(k, wells, n=5000):
    """Harder null: random sources drawn with probability proportional to the subsidence rate,
    i.e. 'just point at where it sinks most'."""
    p = np.clip(D.ravel()[mpix], 0, None)
    pick = rng.choice(mpix, (n, k), p=p / p.sum())
    pts = np.stack([S.XX.ravel()[pick], S.YY.ravel()[pick]], -1)
    dmin = np.hypot(pts[..., None, 0] - wells[:, 0], pts[..., None, 1] - wells[:, 1]).min(-1)
    return (dmin <= 1000).mean(1)


def evaluate(src):
    out = {}
    for name, wl in (("prod", wells_prod), ("all", wells_all)):
        hr = near_rate(src, wl)
        nr, nw = null_rate(len(src), wl), null_weighted(len(src), wl)
        out[name] = dict(hit=hr, null_uniform=float(np.mean(nr)), p_uniform=float((nr >= hr).mean()),
                         null_rate_weighted=float(np.mean(nw)), p_weighted=float((nw >= hr).mean()))
    return out


res = dict(n_pairs=int(len(pairs)), mask_frac=float(mask.mean()),
           peak_subsidence_p99=float(np.percentile(D[mask], 99)), median_subsidence=float(np.median(D[mask])),
           n_wells_all=int(len(wells_all)), n_wells_prod=int(len(wells_prod)), runs={})
print({k: v for k, v in res.items() if k != "runs"}, flush=True)

for label, params in (("cv", (1000., 1250., 1500., 1750., 2000., 2500.)), ("B1000", (1000.,)),
                      ("B1500", (1500.,)), ("B2000", (2000.,))):
    fit = S.fit_sparse(sc, params=params, seed=0)
    ci, stab = S.bootstrap(sc, fit, seed=0, n_boot=40)
    src = fit["sources"]
    Zf = S.Zmat(clay_obs)
    pred = S.Kfull("k0", fit["param"]) @ fit["qgrid"]
    idx = mpix
    beta = np.linalg.lstsq(Zf[idx], D.ravel()[idx] - pred[idx], rcond=None)[0]
    rsd = float(np.std(D.ravel()[idx] - pred[idx] - Zf[idx] @ beta))
    st = src[stab >= 0.8] if len(src) else src
    res["runs"][label] = dict(B=fit["param"], n_src=int(len(src)), n_stable=int(len(st)), resid_sd=rsd,
                              total_vol=float(src[:, 2].sum()) if len(src) else 0.0,
                              sources=[dict(x=float(s[0] + E0), y=float(s[1] + N0), vol=float(s[2]),
                                            ci5=float(c5), ci95=float(c95), stab=float(sb))
                                       for s, (c5, _, c95), sb in zip(src, ci, stab)],
                              eval_all=evaluate(src), eval_stable=evaluate(st))
    print(label, json.dumps({k: v for k, v in res["runs"][label].items() if k != "sources"}), flush=True)

bw = S.fit_bowls(sc)["sources"]
res["bowls"] = dict(n_src=int(len(bw)), eval=evaluate(bw))
print("bowls", json.dumps(res["bowls"]), flush=True)
json.dump(res, open(f"{stackdir}/real_result.json", "w"), indent=1)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(10, 7))
im = ax.imshow(np.where(mask, D, np.nan), origin="lower", cmap="RdYlBu_r",
               extent=[0, S.NX * S.PIX / 1e3, 0, S.NY * S.PIX / 1e3], vmin=-10, vmax=100)
plt.colorbar(im, label="subsidence, mm/yr (vertical, from LOS)")
ax.plot(wells_prod[:, 0] / 1e3, wells_prod[:, 1] / 1e3, "k^", ms=6, label="production deep wells (PANGAEA)")
ax.plot(wells_all[~np.isin(wells_all[:, 0], wells_prod[:, 0]), 0] / 1e3,
        wells_all[~np.isin(wells_all[:, 0], wells_prod[:, 0]), 1] / 1e3, "kv", mfc="none", ms=6, label="observation wells")
s = np.array([[q["x"] - E0, q["y"] - N0, q["stab"]] for q in res["runs"]["cv"]["sources"]]).reshape(-1, 3)
ax.scatter(s[:, 0] / 1e3, s[:, 1] / 1e3, s=120, facecolors="none", edgecolors=np.where(s[:, 2] >= 0.8, "m", "grey"),
           linewidths=2, label="sparse sources (magenta = stability>=0.8)")
ax.set_xlabel(f"km east of E{E0:.0f}"); ax.set_ylabel(f"km north of N{N0:.0f}")
ax.legend(loc="lower right", fontsize=8)
ax.set_title(f"Real Sentinel-1 LiCSAR stack, {pairs[0][:8]}-{pairs[-1][9:]}, {len(pairs)} pairs")
fig.savefig(f"{stackdir}/real_map.png", dpi=130, bbox_inches="tight")
print("done")
