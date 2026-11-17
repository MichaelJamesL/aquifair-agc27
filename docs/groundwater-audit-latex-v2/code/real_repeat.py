"""No-truth checks of the local matched-filter detector on Semarang.

(1) Repeatability: run the detector on independent rate maps (different years, different tracks)
    and count how many detections of map A reappear within 1 km in map B, against a null that
    shifts A's detection pattern toroidally (keeps its clustering). Volume agreement of matches.
(2) Plausibility: are detections on low ground / the clay side of the fault edge / built-up land
    more than toroidally shifted patterns are?
Usage: python real_repeat.py   -> realdata/semarang/exp/repeat.json
"""
import json
import numpy as np
import synth as S
import real_lib as R
import real_goal_maps as GM
import real_mf as MF

ROOT = GM.ROOT
g = GM.grid
rng = np.random.default_rng(5)
NDRAW = 1000


def grid_map(stacks):
    rm = GM.track_map(stacks)
    D, c = g.block_mean(rm["sub"], rm["transform"])
    return np.where(c >= 1, D, np.nan), c >= 1, rm


maps = {}
for name, st in (("desc_2014_17", ["t076_1517"]), ("desc_2018_22", ["t076"]),
                 ("desc_2023_26", ["t076_2326"]), ("asc_2018_22", ["t127"])):
    maps[name] = grid_map(st)
H = R.grid_hgt(maps["desc_2018_22"][2], g)
det = {}
for name, (D, m, _) in maps.items():
    d = MF.Detector(m, H, np.nan_to_num(D)).detect(np.nan_to_num(D))
    det[name] = d
    print(name, "detections", len(d), "mask", round(float(m.mean()), 3), flush=True)


def cell(p):
    return (p[:, 1] // S.PIX).astype(int).clip(0, S.NY - 1), (p[:, 0] // S.PIX).astype(int).clip(0, S.NX - 1)


def hit_frac(a, b, tol=1000.0):
    if len(a) == 0 or len(b) == 0:
        return 0.0, []
    d = np.hypot(a[:, None, 0] - b[None, :, 0], a[:, None, 1] - b[None, :, 1])
    j = d.argmin(1)
    ok = d[np.arange(len(a)), j] <= tol
    return float(ok.mean()), [(i, int(j[i])) for i in np.flatnonzero(ok)]


def toroidal(a, common):
    """Shift the whole detection pattern by a random (dx, dy) with wrap-around; keep points that land
    on common-mask cells."""
    W, Hh = S.NX * S.PIX, S.NY * S.PIX
    dx, dy = rng.uniform(0, W), rng.uniform(0, Hh)
    s = np.c_[(a[:, 0] + dx) % W, (a[:, 1] + dy) % Hh, a[:, 2]]
    iy, ix = cell(s)
    return s[common[iy, ix]]


res = dict(pairs={}, plausibility={})
for A, B in (("desc_2014_17", "desc_2018_22"), ("desc_2018_22", "desc_2023_26"),
             ("desc_2014_17", "desc_2023_26"), ("desc_2018_22", "asc_2018_22")):
    common = maps[A][1] & maps[B][1]
    a, b = det[A], det[B]
    a = a[common[cell(a)]] if len(a) else a
    b = b[common[cell(b)]] if len(b) else b
    obs, pr = hit_frac(a, b)
    null = []
    for _ in range(NDRAW):
        s = toroidal(a, common)
        if len(s):
            null.append(hit_frac(s, b)[0])
    null = np.array(null)
    lr = [abs(np.log(a[i, 2] / b[j, 2])) for i, j in pr if a[i, 2] > 0 and b[j, 2] > 0]
    res["pairs"][f"{A}_vs_{B}"] = dict(nA=int(len(a)), nB=int(len(b)), repeat=round(obs, 3),
                                       null_mean=round(float(null.mean()), 3),
                                       null_p95=round(float(np.percentile(null, 95)), 3),
                                       p=round(float((null >= obs).mean()), 4),
                                       median_abs_log_vol_ratio=round(float(np.median(lr)), 3) if lr else None,
                                       median_vol_ratio_factor=round(float(np.exp(np.median(lr))), 2) if lr else None)
    print(A, B, res["pairs"][f"{A}_vs_{B}"], flush=True)

# plausibility on the two-track 2018-22 map (the map used for the main results)
D2, m2, H2, _ = GM.load("da", "1822")
d2 = MF.Detector(m2, H2, np.nan_to_num(D2)).detect(np.nan_to_num(D2))
wc = np.load(f"{ROOT}/worldcover_grid.npz")
clay = R.background("edge", H2, np.nan_to_num(D2), m2, g)       # sigmoid step: ~1 on the subsiding plain side
layers = dict(low_ground_H_lt_10=(H2 < 10).astype(float), clay_side=(clay > 0.5).astype(float),
              built_frac=wc["built"], tree_frac=wc["tree"], crop_frac=wc["crop"], water_frac=wc["water"])
iy, ix = cell(d2)
for nm, L in layers.items():
    obs = float(L[iy, ix].mean())
    null = []
    for _ in range(NDRAW):
        s = toroidal(d2, m2)
        if len(s):
            jy, jx = cell(s)
            null.append(L[jy, jx].mean())
    null = np.array(null)
    res["plausibility"][nm] = dict(n=int(len(d2)), detections=round(obs, 3), null_mean=round(float(null.mean()), 3),
                                   mask_mean=round(float(L[m2].mean()), 3),
                                   p_greater=round(float((null >= obs).mean()), 4),
                                   p_less=round(float((null <= obs).mean()), 4))
    print("plaus", nm, res["plausibility"][nm], flush=True)
json.dump(res, open(f"{ROOT}/exp/repeat.json", "w"), indent=1)
print("done")
