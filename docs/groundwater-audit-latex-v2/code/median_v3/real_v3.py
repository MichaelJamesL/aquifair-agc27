"""v3 real-data pipeline: median-filter background estimated jointly with the cones, CV penalty
(no surrogate floor) and bootstrap stability selection. Tests: planted cones (recall, false
detections, volume error) at two cone widths, and truth (PANGAEA wells, OSM industrial land).

Usage: python real_v3.py STACKDIR OUT.json [--km=2] [--min-days=0] [--trials=3] [--qs=100,200,400]
"""
import sys, json, time
import numpy as np
from scipy import ndimage
import synth as S
import real_lib as R

stackdir, outp = sys.argv[1:3]
opt = {a.split("=")[0]: (a.split("=") + [""])[1] for a in sys.argv[3:] if a.startswith("--")}
KM = float(opt.get("--km", 2))
TRIALS = int(opt.get("--trials", 3))
QS = tuple(float(v) for v in opt.get("--qs", "100,200,400").split(","))
PARAMS = tuple(float(v) for v in opt.get("--params", "700,1500,3500").split(","))
ROOT = "../../../realdata/semarang"
grid = R.Grid(428000.0, 9220000.0, 32749)
rng = np.random.default_rng(11)
t0 = time.time()


def fit_v3(d, mask, seed=0, iters=2, n_boot=20):
    """Alternate: background = median(d - cones), cones = lasso on d - background. Then stability."""
    sc = dict(d=np.where(mask, d, 0.0), mask=mask, clay_obs=R.median_bg(d, mask, KM))
    fit = S.fit_sparse(sc, params=PARAMS, seed=seed, floor=False)
    for _ in range(iters):
        model = (S.Kfull("k0", fit["param"]) @ fit["qgrid"]).reshape(S.NY, S.NX)
        sc["clay_obs"] = R.median_bg(d - model, mask, KM)
        f2 = S.fit_sparse(sc, params=(fit["param"],), seed=seed, floor=False)
        f2["param"] = fit["param"]
        fit = f2
    _, stab = S.bootstrap(sc, fit, seed=seed, n_boot=n_boot)
    return fit, stab, sc


MD = float(opt.get("--min-days", 0))
if "--two-track" in opt:                     # stackdir = "DESC,ASC"
    rms = [R.rate_map(sd, gacos=True, min_days=MD) for sd in stackdir.split(",")]
    rm = rms[0]
    H, _ = grid.block_mean(np.where(np.isfinite(rm["sub"]), rm["hgt"], np.nan), rm["transform"])
    D, mask, info = R.combine_tracks(rms, grid, H)
    D = np.nan_to_num(D)
else:
    rm = R.rate_map(stackdir, min_days=MD)
    D, cnt = grid.block_mean(rm["sub"], rm["transform"])
    mask = cnt >= 1
    H, _ = grid.block_mean(np.where(np.isfinite(rm["sub"]), rm["hgt"], np.nan), rm["transform"])
    info = {}
res = dict(stack=stackdir, km=KM, opts=opt, mask_frac=float(mask.mean()), tracks=info,
           stable_noise=R.stable_noise(D, H, mask))
print("rate map", json.dumps({k: res[k] for k in ("mask_frac", "tracks", "stable_noise")}), flush=True)

# ---- truth ----------------------------------------------------------------------------------
fit, stab, sc = fit_v3(D, mask)
src = fit["sources"]
wells_prod, _ = R.pangaea_wells(f"{ROOT}/pangaea.tab", grid)
ind, _ = R.osm_layers(f"{ROOT}/osm.json", grid)
res["resid_sd"] = R.resid_sd(sc, fit)


def truth(s):
    return dict(wells_1km=R.location_test(s, mask, D, lambda p: R.dist_to_points(p, wells_prod), 1000, rng),
                industrial_500m=R.location_test(s, mask, D, lambda p: R.dist_to_raster(p, ind), 500, rng))


st = src[stab >= 0.8] if len(src) else src
res["truth"] = dict(B=fit["param"], n_src=int(len(src)), n_stable=int(len(st)),
                    sources=[[*map(float, s), float(b)] for s, b in zip(src, stab)],
                    all=truth(src), stable=truth(st))
print("truth", json.dumps({k: v for k, v in res["truth"].items() if k != "sources"}),
      f"{time.time() - t0:.0f}s", flush=True)
json.dump(res, open(outp, "w"), indent=1)

# ---- planted cones --------------------------------------------------------------------------
mp = np.flatnonzero(ndimage.binary_erosion(mask, iterations=5).ravel())
base_st = st
res["inject"] = {}
for bt in (1500.0, 3500.0):
    for q in QS:
        rows = []
        for t in range(TRIALS):
            pts = []
            while len(pts) < 5:
                j = rng.choice(mp)
                p = np.array([S.XX.ravel()[j], S.YY.ravel()[j]])
                if all(np.hypot(*(p - o)) > max(2500, 1.5 * bt) for o in pts):
                    pts.append(p)
            pts = np.array(pts)
            add = sum(q * S.kern(np.hypot(S.XX - x, S.YY - y), "k0", bt) for x, y in pts)
            f, sb, _ = fit_v3(np.where(mask, D + add, 0.0), mask, seed=t)
            est = f["sources"]
            est_st = est[sb >= 0.8] if len(est) else est
            row = {}
            for name, e in (("all", est), ("stable", est_st)):
                pr = S.match(pts, e, tol=max(1000, 0.7 * bt))
                mj = {j for _, j in pr}
                new_false = sum(1 for j in range(len(e)) if j not in mj and
                                (len(base_st) == 0 or np.hypot(base_st[:, 0] - e[j, 0], base_st[:, 1] - e[j, 1]).min() > 1000))
                row[name] = dict(recall=len(pr) / 5, new_false=new_false,
                                 vol_err=[float((e[j, 2] - q) / q) for _, j in pr],
                                 ratio=[float(e[j, 2] / q) for _, j in pr])
            rows.append(row)
        agg = {}
        for name in ("all", "stable"):
            ve = [v for r in rows for v in r[name]["vol_err"]]
            agg[name + "_ratios"] = [[v for v in r[name]["ratio"]] for r in rows]   # per trial
            agg[name] = dict(recall=float(np.mean([r[name]["recall"] for r in rows])),
                             new_false_per_trial=float(np.mean([r[name]["new_false"] for r in rows])),
                             median_vol_err=float(np.median(ve)) if ve else None,
                             median_abs_vol_err=float(np.median(np.abs(ve))) if ve else None)
        res["inject"][f"B{bt:.0f}_q{q:.0f}"] = agg
        print(f"inject B={bt:.0f} q={q:.0f}", json.dumps({k: v for k, v in agg.items() if "ratios" not in k}), f"{time.time() - t0:.0f}s", flush=True)
        json.dump(res, open(outp, "w"), indent=1)
print("done", f"{time.time() - t0:.0f}s")
