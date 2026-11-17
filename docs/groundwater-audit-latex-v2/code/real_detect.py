"""Detection limit on the real Semarang map: plant 5 cones of one fixed volume, refit, repeat.
Runs with and without the surrogate-noise penalty floor.

Usage: python real_detect.py STACKDIR BACKGROUND OUT.json
"""
import sys, json, time
import numpy as np
from scipy import ndimage
import synth as S
import real_lib as R

stackdir, bg, outp = sys.argv[1:4]
grid = R.Grid(428000.0, 9220000.0, 32749)
MIN_DT = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--min-dt=")), 0))
if "--robust-floor" in sys.argv:
    R.use_robust_floor()
rm = R.rate_map(stackdir, min_dt=MIN_DT)
_D0, _c0 = grid.block_mean(rm["sub"], rm["transform"])
clay = R.background(bg, R.grid_hgt(rm, grid), _D0, _c0 >= 1, grid)
sc, D = R.model_input(rm, grid, clay)
mask = sc["mask"]
rng = np.random.default_rng(7)
mp = np.flatnonzero(ndimage.binary_erosion(mask, iterations=5).ravel())
t0 = time.time()
base = {fl: S.fit_sparse(sc, params=(1500.,), seed=0, floor=fl)["sources"] for fl in (True, False)}
out = dict(background=bg, min_dt=MIN_DT, robust_floor="--robust-floor" in sys.argv, levels={})
for q in (100.0, 200.0, 400.0, 800.0):
    rows = {True: [], False: []}
    for t in range(3):
        pts = []
        while len(pts) < 5:
            j = rng.choice(mp)
            p = np.array([S.XX.ravel()[j], S.YY.ravel()[j]])
            if all(np.hypot(*(p - o)) > 2500 for o in pts):
                pts.append(p)
        pts = np.array(pts)
        add = sum(q * S.kern(np.hypot(S.XX - x, S.YY - y), "k0", 1500.0) for x, y in pts)
        sci = dict(sc, d=np.where(mask, sc["d"] + add, 0.0))
        for fl in (True, False):
            est = S.fit_sparse(sci, params=(1500.,), seed=t, floor=fl)["sources"]
            pr = S.match(pts, est)
            b = base[fl]
            extra = sum(1 for j in range(len(est)) if j not in {jj for _, jj in pr} and
                        (len(b) == 0 or np.hypot(b[:, 0] - est[j, 0], b[:, 1] - est[j, 1]).min() > 1000))
            rows[fl].append(dict(recall=len(pr) / 5, new_false=extra))
    peak = float(q * S.kern(np.array(S.R0), "k0", 1500.0))
    out["levels"][q] = {("floor" if fl else "nofloor"): dict(
        recall=float(np.mean([r["recall"] for r in rows[fl]])),
        new_false_per_trial=float(np.mean([r["new_false"] for r in rows[fl]]))) for fl in (True, False)}
    out["levels"][q]["peak_mm_yr"] = peak
    print(q, json.dumps(out["levels"][q]), f"{time.time() - t0:.0f}s", flush=True)
json.dump(out, open(outp, "w"), indent=1)
