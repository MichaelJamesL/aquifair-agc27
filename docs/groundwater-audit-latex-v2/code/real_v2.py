"""Evaluate an improved rate map: SBAS velocity (optionally GACOS), one or two viewing geometries.

Usage: python real_v2.py OUT.json TS1 [TS2]
  TSi = STACKDIR:tsfile, e.g. .../t076:ts_gacos.npz . Two tracks -> vertical/east decomposition;
  one track -> LOS / U (vertical-only assumption).
Reports: stable-ground noise, detection limit (planted cones, floor on), truth hit rates.
"""
import sys, json, time
import numpy as np
from scipy import ndimage
import synth as S
import real_lib as R

ROOT = "C:/Kuliah/hackathon/agc-26/realdata/semarang"
outp, specs = sys.argv[1], [a for a in sys.argv[2:] if not a.startswith("--")]
grid = R.Grid(428000.0, 9220000.0, 32749)
t0 = time.time()

rms = []
for sp in specs:
    sd, tf = sp.rsplit(":", 1)
    if tf == "stack24":
        # stacking of pairs >= 24 days (cleanest rate on stable ground); GACOS applied, look vectors kept
        rms.append(R.rate_map(sd, gacos=True, min_dt=24))
        continue
    z = np.load(f"{sd}/stack.npz")
    ts = np.load(f"{sd}/{tf}")
    look = np.load(f"{sd}/gacos.npz") if "gacos" in tf else None
    U = look["U"] if look is not None else z["U"]
    E = look["E"] if look is not None else None
    ok = np.isfinite(ts["vel"]) & (z["landmask"] > 0) & (ts["rms"] <= np.nanpercentile(ts["rms"], 90))
    rms.append(dict(v_los=np.where(ok, ts["vel"], np.nan), U=U, E=E, hgt=z["hgt"],
                    sub=np.where(ok, -ts["vel"] / U, np.nan), transform=z["transform"]))

H = R.grid_hgt(rms[0], grid)
east = None
if len(rms) == 2:
    D, mask, qc = R.combine_tracks(rms, grid, H)
    print("cross-track QC", qc, flush=True)
else:
    D, c = grid.block_mean(rms[0]["sub"], rms[0]["transform"])
    mask, east = c >= 1, None
D = np.where(mask, D, np.nan)
noise_sd, noise_iqr = R.stable_noise(D, H, mask)
res = dict(inputs=specs, flags=[a for a in sys.argv if a.startswith("--")], mask_frac=float(mask.mean()), stable_sd=noise_sd, stable_iqr_sd=noise_iqr,
           p99=float(np.nanpercentile(D, 99)),
           east_sd=float(np.nanstd(east)) if east is not None else None)
print(json.dumps(res), flush=True)

if "--robust-floor" in sys.argv:
    R.use_robust_floor()
MULT = "--mult" in sys.argv
if MULT:
    # multiplicative clay: plateau = c * regional head decline (clay column), cones = c * q K0
    step, info = R.fit_edge(np.nan_to_num(D), mask, np.zeros((S.NY, S.NX)))
    cfac = 0.15 + 0.85 * step.reshape(S.NY, S.NX)
    print("clay factor from edge fit:", info, flush=True)
    R.use_clay_weighted_kernel(cfac)
    clay = cfac
else:
    cfac = np.ones((S.NY, S.NX))
    clay = R.background("edge", H, np.nan_to_num(D), mask, grid)
sc = R.model_input_grid(np.nan_to_num(D), mask, clay)
Dz = np.nan_to_num(D)
wells_prod, _ = R.pangaea_wells(f"{ROOT}/pangaea.tab", grid)
ind, _ = R.osm_layers(f"{ROOT}/osm.json", grid)
rng = np.random.default_rng(3)

# truth tests
res["fits"] = {}
for label, params in (("cv", (1500., 2500., 3500., 5000.)), ("B1500", (1500.,))):
    fit = S.fit_sparse(sc, params=params, seed=0)
    src = fit["sources"]
    res["fits"][label] = dict(B=fit["param"], n_src=int(len(src)), resid_sd=R.resid_sd(sc, fit),
                              sources=src.round(1).tolist(),
                              wells_1km=R.location_test(src, mask, Dz, lambda p: R.dist_to_points(p, wells_prod), 1000, rng),
                              industrial_500m=R.location_test(src, mask, Dz, lambda p: R.dist_to_raster(p, ind), 500, rng))
    print(label, json.dumps({k: v for k, v in res["fits"][label].items() if k != "sources"}),
          f"{time.time() - t0:.0f}s", flush=True)
json.dump(res, open(outp, "w"), indent=1)

# detection limit: 5 planted cones per trial, B = 1.5 km, penalty floor on
mp = np.flatnonzero(ndimage.binary_erosion(mask, iterations=5).ravel())
base = res["fits"]["B1500"]["sources"]
base = np.array(base).reshape(-1, 3)
res["detect"] = {}
for q in (100.0, 200.0, 400.0):
    rec, fal, vols = [], [], []
    for t in range(3):
        pts = []
        while len(pts) < 5:
            j = rng.choice(mp)
            p = np.array([S.XX.ravel()[j], S.YY.ravel()[j]])
            if all(np.hypot(*(p - o)) > 2500 for o in pts):
                pts.append(p)
        pts = np.array(pts)
        add = cfac * sum(q * S.kern(np.hypot(S.XX - x, S.YY - y), "k0", 1500.0) for x, y in pts)
        est = S.fit_sparse(dict(sc, d=np.where(mask, sc["d"] + add, 0.0)), params=(1500.,), seed=t)["sources"]
        pr = S.match(pts, est)
        rec.append(len(pr) / 5)
        vols.extend(float((est[j, 2] - q) / q) for _, j in pr)
        fal.append(sum(1 for j in range(len(est)) if j not in {jj for _, jj in pr} and
                       (len(base) == 0 or np.hypot(base[:, 0] - est[j, 0], base[:, 1] - est[j, 1]).min() > 1000)))
    res["detect"][q] = dict(recall=float(np.mean(rec)), new_false=float(np.mean(fal)),
                           median_vol_err=float(np.median(vols)) if vols else None,
                           median_abs_vol_err=float(np.median(np.abs(vols))) if vols else None)
    print("detect", q, res["detect"][q], f"{time.time() - t0:.0f}s", flush=True)
json.dump(res, open(outp, "w"), indent=1)
print("done")
