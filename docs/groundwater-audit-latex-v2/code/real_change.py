"""Invert the CHANGE in subsidence rate (late minus early period) for sources of pumping change.

Usage: python real_change.py STACKDIR TSFILE SPLIT_YEAR OUT.json
Geology (clay thickness, fault step) scales compaction but does not change between periods, so it
largely cancels in the rate difference; what is left is where pumping went up or down.
Two non-negative fits: +dRate (pumping increased) and -dRate (pumping decreased).
"""
import sys, json
import numpy as np
import synth as S
import real_lib as R

stackdir, tsfile, split, outp = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
ROOT = "C:/Kuliah/hackathon/agc-26/realdata/semarang"
grid = R.Grid(428000.0, 9220000.0, 32749)
z = np.load(f"{stackdir}/stack.npz")
ts = np.load(f"{stackdir}/{tsfile}")
t = np.array([(np.datetime64(f"{e[:4]}-{e[4:6]}-{e[6:]}") - np.datetime64("2018-01-01")).astype(int)
              for e in ts["epochs"]]) / 365.25 + 2018.0
cum = -ts["cum"] / z["U"]                                  # vertical subsidence, mm, + = sinking


def rate(sel):
    tt = t[sel] - t[sel].mean()
    c = cum[sel]
    return (tt[:, None, None] * (c - c.mean(0))).sum(0) / (tt ** 2).sum()


dr = rate(t >= split) - rate(t < split)
dD, cnt = grid.block_mean(np.where(np.isfinite(dr), dr, np.nan), z["transform"])
mask = cnt >= 1
clay = np.zeros((S.NY, S.NX))                              # geology cancels: cosine background only
wells, _ = R.pangaea_wells(f"{ROOT}/pangaea.tab", grid)
ind, _ = R.osm_layers(f"{ROOT}/osm.json", grid)
rng = np.random.default_rng(5)
Dabs = np.abs(np.nan_to_num(dD))
res = dict(split=split, change_sd=float(np.nanstd(dD[mask])), fits={})
for sign, name in ((1.0, "increase"), (-1.0, "decrease")):
    sc = R.model_input_grid(sign * np.nan_to_num(dD), mask, clay)
    fit = S.fit_sparse(sc, params=(1500., 2500., 3500., 5000.), seed=0)
    src = fit["sources"]
    res["fits"][name] = dict(B=fit["param"], n_src=int(len(src)), sources=src.round(1).tolist(),
                             wells_1km=R.location_test(src, mask, Dabs, lambda p: R.dist_to_points(p, wells), 1000, rng),
                             industrial_500m=R.location_test(src, mask, Dabs, lambda p: R.dist_to_raster(p, ind), 500, rng))
    print(name, json.dumps({k: v for k, v in res["fits"][name].items() if k != "sources"}), flush=True)
json.dump(res, open(outp, "w"), indent=1)
