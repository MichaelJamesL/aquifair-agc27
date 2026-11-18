"""Hypothesis tests on real Semarang data.

Usage: python real_experiments.py STACKDIR BACKGROUND OUT.json [--no-inject]
  BACKGROUND: lowground | dtb | flat | hgtbins
  H1 (can it see cones on real background?): inject known K0 cones into the real map, refit.
  H2 (old truth?): score sources against 1992-2007 wells AND current OSM industrial land / wells.
  H3 (background model?): compare backgrounds by residual spread, injection recovery, truth hits.
"""
import sys, json, time
import numpy as np
from scipy import ndimage
import synth as S
import real_lib as R

stackdir, bg, outp = sys.argv[1], sys.argv[2], sys.argv[3]
inject = "--no-inject" not in sys.argv
ROOT = "../../../realdata/semarang"
grid = R.Grid(428000.0, 9220000.0, 32749)
rng = np.random.default_rng(1)
t0 = time.time()

rm = R.rate_map(stackdir)
clay = R.background(bg, rm, grid)

sc, D = R.model_input(rm, grid, clay)
mask = sc["mask"]
wells_prod, wells_all = R.pangaea_wells(f"{ROOT}/pangaea.tab", grid)
ind, osm_wells = R.osm_layers(f"{ROOT}/osm.json", grid)
osm_wells = osm_wells[(osm_wells[:, 0] > 0) & (osm_wells[:, 0] < S.NX * S.PIX) &
                      (osm_wells[:, 1] > 0) & (osm_wells[:, 1] < S.NY * S.PIX)]
res = dict(stack=stackdir, background=bg, n_pairs=int(len(rm["pairs"])),
           period=f"{rm['pairs'][0][:8]}-{rm['pairs'][-1][9:]}", mask_frac=float(mask.mean()),
           industrial_frac_of_mask=float(ind[mask].mean()), n_wells_prod=int(len(wells_prod)),
           n_osm_wells=int(len(osm_wells)), fits={})


def truth(src):
    out = dict(wells_1km=R.location_test(src, mask, D, lambda p: R.dist_to_points(p, wells_prod), 1000, rng),
               industrial_500m=R.location_test(src, mask, D, lambda p: R.dist_to_raster(p, ind), 500, rng))
    if len(osm_wells) >= 3:
        out["osm_wells_1km"] = R.location_test(src, mask, D, lambda p: R.dist_to_points(p, osm_wells), 1000, rng)
    return out


base = {}
CVP = tuple(float(v) for v in next((a.split("=")[1] for a in sys.argv if a.startswith("--params=")), "1000,1500,2000,2500").split(","))
for label, params in (("cv", CVP), ("B1500", (1500.,))):
    fit = S.fit_sparse(sc, params=params, seed=0)
    base[label] = fit
    src = fit["sources"]
    res["fits"][label] = dict(B=fit["param"], n_src=int(len(src)), resid_sd=R.resid_sd(sc, fit),
                              total_vol=float(src[:, 2].sum()) if len(src) else 0.0,
                              sources=src.round(1).tolist(), truth=truth(src))
    print(label, json.dumps({k: v for k, v in res["fits"][label].items() if k != "sources"}),
          f"{time.time() - t0:.0f}s", flush=True)
json.dump(res, open(outp, "w"), indent=1)

if inject:
    # H1: plant 5 known cones (B = 1.5 km, 100-400 thousand m3/yr) into the real map and refit.
    mp = np.flatnonzero((ndimage.binary_erosion(mask, iterations=5)).ravel())
    bg_src = base["B1500"]["sources"]
    trials = []
    for t in range(6):
        pts = []
        while len(pts) < 5:
            j = rng.choice(mp)
            p = np.array([S.XX.ravel()[j], S.YY.ravel()[j]])
            if all(np.hypot(*(p - q)) > 2500 for q in pts):
                pts.append(p)
        pts = np.array(pts)
        q = np.exp(rng.uniform(np.log(100), np.log(400), 5))
        add = sum(qj * S.kern(np.hypot(S.XX - x, S.YY - y), "k0", 1500.0) for (x, y), qj in zip(pts, q))
        sci = dict(sc, d=np.where(mask, sc["d"] + add, 0.0))
        if bg.startswith("median"):                      # the filter must see the planted cones
            sci["clay_obs"] = R.median_bg(sci["d"], mask, float(bg[6:] or 3))
        fit = S.fit_sparse(sci, params=(1500.,), seed=t)
        est = fit["sources"]
        pairs = S.match(pts, est)  # 1 km tolerance, as in the synthetic study
        # volume of a matched source = estimate minus what the no-injection fit already put there
        rel = []
        for i, j in pairs:
            prior = bg_src[np.hypot(bg_src[:, 0] - est[j, 0], bg_src[:, 1] - est[j, 1]) <= 1000, 2].sum() \
                if len(bg_src) else 0.0
            rel.append(float((est[j, 2] - prior - q[i]) / q[i]))
        matched_est = {j for _, j in pairs}
        new_false = 0
        for j in range(len(est)):
            if j in matched_est:
                continue
            if len(bg_src) == 0 or np.hypot(bg_src[:, 0] - est[j, 0], bg_src[:, 1] - est[j, 1]).min() > 1000:
                new_false += 1
        trials.append(dict(recall=len(pairs) / 5, vol_rel_err=rel, new_false=new_false, n_est=int(len(est))))
        print("inject", t, trials[-1], f"{time.time() - t0:.0f}s", flush=True)
    allrel = [abs(v) for tr in trials for v in tr["vol_rel_err"]]
    res["inject"] = dict(trials=trials, recall=float(np.mean([tr["recall"] for tr in trials])),
                         median_abs_vol_err=float(np.median(allrel)) if allrel else None,
                         new_false_per_trial=float(np.mean([tr["new_false"] for tr in trials])))
    print("inject summary", json.dumps({k: v for k, v in res["inject"].items() if k != "trials"}), flush=True)
json.dump(res, open(outp, "w"), indent=1)
print("done", f"{time.time() - t0:.0f}s")
