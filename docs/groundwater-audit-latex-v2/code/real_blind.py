"""Blind, realistic planted-field test of the local matched-filter detector (Semarang real map).

Three separate steps so the detector never sees the answer key:
  python real_blind.py gen    DIR [--n 60]   # random scenarios (seed from os.urandom), key -> DIR/key.json
  python real_blind.py detect DIR            # reads only DIR/maps.npz -> DIR/detections.json
  python real_blind.py score  DIR            # compares detections with key

Realism vs the earlier test:
  - volumes log-normal (median 150, 30-1500 thousand m^3/yr), widths B log-uniform 0.7-3 km
  - elliptical cones (aspect 1-2.5, random orientation; area preserved)
  - 35 % of fields are clusters of 2-4 wells within 300-800 m (truth = field total at centroid)
  - placement weighted to plausible pumping land: built-up (WorldCover) and OSM industrial,
    coastal plain; some anywhere; fields may overlap (>= 1 km apart)
Detector unchanged: K0 B=1.5 km + local quadratic, 2 km disc, threshold 60, 1 km peak spacing.
shortcut: planted in the stacked rate map (stacking is linear, so a field with time-varying
pumping contributes its mean rate); the transformer front-end is not part of this test.
"""
import sys, os, json
import numpy as np
from scipy import ndimage
from scipy.signal import fftconvolve
import synth as S
import real_lib as R
import real_goal_maps as GM

cmd, DIR = sys.argv[1], sys.argv[2]
os.makedirs(DIR, exist_ok=True)
D, mask, H, info = GM.load("da", "1822")
Dz = np.nan_to_num(D)
ROOT = GM.ROOT


def cone(x, y, q, B, aspect, th):
    """Elliptical K0 cone (area-preserving stretch) on the model grid, mm/yr."""
    u = (S.XX - x) * np.cos(th) + (S.YY - y) * np.sin(th)
    v = -(S.XX - x) * np.sin(th) + (S.YY - y) * np.cos(th)
    a = np.sqrt(aspect)
    return q * S.kern(np.hypot(u / a, v * a), "k0", B)


if cmd == "gen":
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 60
    rng = np.random.default_rng(int.from_bytes(os.urandom(8), "little"))
    wc = np.load(f"{ROOT}/worldcover_grid.npz")
    ind, _ = R.osm_layers(f"{ROOT}/osm.json", GM.grid)
    inner = ndimage.binary_erosion(mask, iterations=3)
    # plausibility weight: built-up fraction, industrial land, low ground; plus a floor (anywhere)
    w = (0.2 + wc["built"] + 2.0 * ind + 1.0 * (H < 20)) * inner
    p = (w / w.sum()).ravel()
    maps, key = [], []
    for s in range(n):
        fields = []
        while len(fields) < rng.integers(4, 9):
            j = rng.choice(p.size, p=p)
            x, y = S.XX.ravel()[j], S.YY.ravel()[j]
            if any(np.hypot(x - f["x"], y - f["y"]) < 1000 for f in fields):
                continue
            q = float(np.clip(np.exp(rng.normal(np.log(150), 0.8)), 30, 1500))
            B = float(np.exp(rng.uniform(np.log(700), np.log(3000))))
            nw = int(rng.integers(2, 5)) if rng.random() < 0.35 else 1
            share = rng.dirichlet(np.ones(nw))
            ang = rng.uniform(0, 2 * np.pi, nw)
            rad = rng.uniform(300, 800, nw) if nw > 1 else np.zeros(1)
            wells = [(x + r * np.cos(a), y + r * np.sin(a), q * sh) for r, a, sh in zip(rad, ang, share)]
            cx = sum(wx * wq for wx, _, wq in wells) / q
            cy = sum(wy * wq for _, wy, wq in wells) / q
            fields.append(dict(x=float(cx), y=float(cy), q=q, B=B, n_wells=nw,
                               aspect=float(rng.uniform(1, 2.5)), theta=float(rng.uniform(0, np.pi)), wells=wells))
        add = sum(cone(wx, wy, wq, f["B"], f["aspect"], f["theta"]) for f in fields for wx, wy, wq in f["wells"])
        maps.append(np.where(mask, Dz + add, 0.0).astype(np.float32))
        key.append([{k: v for k, v in f.items() if k != "wells"} for f in fields])
    np.savez_compressed(f"{DIR}/maps.npz", maps=np.array(maps))
    json.dump(key, open(f"{DIR}/key.json", "w"))
    print(f"generated {n} scenarios, {sum(len(k) for k in key)} fields (key not printed)")

elif cmd == "detect":
    import real_mf as MF
    det = MF.Detector(mask, H, Dz)
    maps = np.load(f"{DIR}/maps.npz")["maps"]
    out = dict(base=det.detect(Dz).tolist(), scenarios=[det.detect(m).tolist() for m in maps])
    json.dump(out, open(f"{DIR}/detections.json", "w"))
    print(f"detections written for {len(maps)} scenarios; base map has {len(out['base'])}")

elif cmd == "score":
    key = json.load(open(f"{DIR}/key.json"))
    det = json.load(open(f"{DIR}/detections.json"))
    base = np.array(det["base"]).reshape(-1, 3)
    rows, fal = [], []
    for fields, est in zip(key, det["scenarios"]):
        est = np.array(est).reshape(-1, 3)
        pts = np.array([[f["x"], f["y"]] for f in fields])
        pr = dict(S.match(pts, est))
        got = set(pr.values())
        for i, f in enumerate(fields):
            j = pr.get(i)
            rows.append(dict(f, found=j is not None, qhat=float(est[j, 2]) if j is not None else None,
                             loc_err=float(np.hypot(*(pts[i] - est[j, :2]))) if j is not None else None,
                             plain=bool(H[int(f["y"] // S.PIX), int(f["x"] // S.PIX)] < 20)))
        fal.append(sum(1 for j in range(len(est)) if j not in got and
                       (len(base) == 0 or np.hypot(*(base[:, :2] - est[j, :2]).T).min() > 1000)))

    def summ(sel):
        r = [x for x in rows if sel(x)]
        f = [x for x in r if x["found"]]
        e = [(x["qhat"] - x["q"]) / x["q"] for x in f]
        return dict(n=len(r), recall=round(len(f) / max(len(r), 1), 3),
                    med_abs_vol_err=round(float(np.median(np.abs(e))), 3) if e else None,
                    med_vol_err=round(float(np.median(e)), 3) if e else None,
                    med_loc_err_m=round(float(np.median([x["loc_err"] for x in f])), 0) if f else None)

    res = dict(n_scenarios=len(key), n_fields=len(rows), base_detections=len(base),
               false_per_scenario=round(float(np.mean(fal)), 2),
               fields_per_scenario=round(len(rows) / len(key), 2), all=summ(lambda x: True),
               plain=summ(lambda x: x["plain"]), hills=summ(lambda x: not x["plain"]),
               single_well=summ(lambda x: x["n_wells"] == 1), cluster=summ(lambda x: x["n_wells"] > 1),
               by_volume={f"{a}-{b}": summ(lambda x, a=a, b=b: a <= x["q"] < b)
                          for a, b in ((30, 60), (60, 100), (100, 200), (200, 400), (400, 1600))},
               by_width={f"{a}-{b}": summ(lambda x, a=a, b=b: a <= x["B"] < b)
                         for a, b in ((700, 1000), (1000, 1500), (1500, 2000), (2000, 3001))},
               vol_100_400_width_1000_2000=summ(lambda x: 100 <= x["q"] < 400 and 1000 <= x["B"] < 2000))
    json.dump(dict(res, rows=rows), open(f"{DIR}/score.json", "w"), indent=1)
    print(json.dumps(res, indent=1))
