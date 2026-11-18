"""Detection limit on the real Semarang map: plant 5 cones of one fixed volume, refit, repeat.
Runs with and without the surrogate-noise penalty floor.

Usage: python real_detect.py STACKDIR BACKGROUND OUT.json [Q1,Q2,..] [--btrue=1500] [--fitb=1500]
                              [--robust-floor] [--min-days=0]
"""
import sys, json, time
import numpy as np
from scipy import ndimage
import synth as S
import real_lib as R

stackdir, bg, outp = sys.argv[1:4]
opt = {a.split("=")[0]: (a.split("=") + [""])[1] for a in sys.argv[4:] if a.startswith("--")}
pos = [a for a in sys.argv[4:] if not a.startswith("--")]
BT = float(opt.get("--btrue", 1500))                    # width of the planted cones
FITB = tuple(float(v) for v in opt.get("--fitb", "1500").split(","))
if "--robust-floor" in opt:
    R.use_robust_floor()
grid = R.Grid(428000.0, 9220000.0, 32749)
rm = R.rate_map(stackdir, min_days=float(opt.get("--min-days", 0)))
clay = R.background(bg, rm, grid)
sc, D = R.model_input(rm, grid, clay)
mask = sc["mask"]
rng = np.random.default_rng(7)
mp = np.flatnonzero(ndimage.binary_erosion(mask, iterations=5).ravel())
t0 = time.time()
base = {fl: S.fit_sparse(sc, params=FITB, seed=0, floor=fl)["sources"] for fl in (True, False)}
out = dict(background=bg, btrue=BT, fitb=FITB, opts=opt, levels={})
for q in tuple(float(v) for v in (pos[0] if pos else "100,200,400,800").split(",")):
    rows = {True: [], False: []}
    for t in range(3):
        pts = []
        while len(pts) < 5:
            j = rng.choice(mp)
            p = np.array([S.XX.ravel()[j], S.YY.ravel()[j]])
            if all(np.hypot(*(p - o)) > 2500 for o in pts):
                pts.append(p)
        pts = np.array(pts)
        add = sum(q * S.kern(np.hypot(S.XX - x, S.YY - y), "k0", BT) for x, y in pts)
        sci = dict(sc, d=np.where(mask, sc["d"] + add, 0.0))
        if bg.startswith("median"):                      # the filter must see the planted cones
            sci["clay_obs"] = R.median_bg(sci["d"], mask, float(bg[6:] or 3))
        for fl in (True, False):
            est = S.fit_sparse(sci, params=FITB, seed=t, floor=fl)["sources"]
            pr = S.match(pts, est)
            b = base[fl]
            extra = sum(1 for j in range(len(est)) if j not in {jj for _, jj in pr} and
                        (len(b) == 0 or np.hypot(b[:, 0] - est[j, 0], b[:, 1] - est[j, 1]).min() > 1000))
            rows[fl].append(dict(recall=len(pr) / 5, new_false=extra,
                                 vol_err=[float((est[j, 2] - q) / q) for _, j in pr]))
    peak = float(q * S.kern(np.array(S.R0), "k0", BT))
    out["levels"][q] = {("floor" if fl else "nofloor"): dict(
        recall=float(np.mean([r["recall"] for r in rows[fl]])),
        new_false_per_trial=float(np.mean([r["new_false"] for r in rows[fl]])),
        median_vol_err=float(np.median([v for r in rows[fl] for v in r["vol_err"]] or [np.nan])),
        median_abs_vol_err=float(np.median([abs(v) for r in rows[fl] for v in r["vol_err"]] or [np.nan])))
        for fl in (True, False)}
    out["levels"][q]["peak_mm_yr"] = peak
    print(q, json.dumps(out["levels"][q]), f"{time.time() - t0:.0f}s", flush=True)
json.dump(out, open(outp, "w"), indent=1)
