"""Cross-site pumping-volume transfer test (design: xsite_prereg.md). Arizona <-> Houston, 4 km blocks.
Writes realdata/xsite_model.json and prints the score table.
Usage: python xs_model.py
"""
import json
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import nnls
from sklearn.linear_model import Ridge
from pyproj import Transformer

R0 = "C:/Kuliah/hackathon/agc-26/realdata"
BLK = 4000.0
AF = 1.23348                                     # thousand m3 per acre-foot


def blocks(site):
    """-> DataFrame per 4 km block (thousand m3/yr) + block id map; truth Q added by the site loader."""
    z = np.load(f"{R0}/{site}/opera_rate_200m.npz", allow_pickle=True)
    D, mask = z["D"].astype(float), z["mask"].astype(bool) & np.isfinite(z["D"])
    E0, N0, PIX = float(z["E0"]), float(z["N0"]), float(z["PIX"])
    NY, NX = D.shape
    if site == "houston":                       # tie to GNSS (prereg addendum 1)
        g = json.load(open(f"{R0}/houston/gnss.json"))["features"]
        g = pd.DataFrame([x["attributes"] for x in g]).dropna(subset=["Rate2024"])
        E, N = Transformer.from_crs(4326, int(z["epsg"]), always_xy=True).transform(g.Long.values, g.Lat.values)
        ix, iy = ((E - E0) // PIX).astype(int), ((N - N0) // PIX).astype(int)
        YY, XX = np.mgrid[:NY, :NX]
        ins = np.array([np.nanmedian(np.where(mask & (np.hypot(YY - b, XX - a) <= 10), D, np.nan))
                        if 0 <= a < NX and 0 <= b < NY else np.nan for a, b in zip(ix, iy)])
        d = g.Rate2024.values * 10 - ins
        shift = float(np.nanmedian(d))
        ok = np.isfinite(ins)
        print(f"houston GNSS tie: {ok.sum()} stations, shift {shift:+.1f} mm/yr, "
              f"rho(GNSS, InSAR) {stats.spearmanr(g.Rate2024.values[ok], ins[ok])[0]:.2f}")
        D = D + shift
    F = np.load(f"{R0}/{site}/features_200m.npz")
    ET = np.nan_to_num(np.load(f"{R0}/{site}/et_200m.npz")["et_mm"].astype(float))
    clay = np.load(f"{R0}/{site}/clay_200m.npz")["clay_m"].astype(float)
    BL = int(BLK // PIX)
    nbx = (NX - 1) // BL + 1
    bid = ((np.arange(NY)[:, None] // BL) * nbx + np.arange(NX)[None, :] // BL)
    nb = bid.max() + 1
    S = lambda a: np.bincount(bid.ravel(), np.asarray(a, float).ravel(), minlength=nb)
    ckm2 = PIX * PIX / 1e6
    nval = S(mask)
    ncell = S(np.ones_like(D))
    f = pd.DataFrame(dict(
        sub_vol=S(np.clip(D, 0, None) * mask) / np.maximum(nval, 1) * ncell * ckm2,   # mean x block area
        sub_mean=S(D * mask) / np.maximum(nval, 1),
        valid_frac=nval / ncell,
        clay=S(np.nan_to_num(clay)) / np.maximum(S(np.isfinite(clay)), 1),
        clay_frac=S(np.isfinite(clay)) / ncell,
        built_km2=S(F["wc_built"]) * ckm2, crop_km2=S(F["wc_crop"]) * ckm2,
        irr=S(F["wc_crop"] * ET) * ckm2, area_km2=ncell * ckm2))
    geo = dict(E0=E0, N0=N0, PIX=PIX, NX=NX, NY=NY, BL=BL, nbx=nbx, nb=nb, epsg=int(z["epsg"]))
    return f, geo


def block_of(geo, E, N):
    ix, iy = ((E - geo["E0"]) // geo["PIX"]).astype(int), ((N - geo["N0"]) // geo["PIX"]).astype(int)
    ok = (ix >= 0) & (ix < geo["NX"]) & (iy >= 0) & (iy < geo["NY"])
    return np.where(ok, (iy // geo["BL"]) * geo["nbx"] + ix // geo["BL"], -1)


def arizona():
    f, geo = blocks("arizona")
    w = pd.read_csv(f"{R0}/arizona/pump_all.csv", dtype={"REGISTRY_ID": str})
    w["q"] = w[[str(y) for y in range(2016, 2021)]].fillna(0).mean(1) * AF
    w = w[w.q > 0]
    b = block_of(geo, w.UTM_X_METERS.values, w.UTM_Y_METERS.values)
    f["Q"] = np.bincount(b[b >= 0], w.q.values[b >= 0], minlength=geo["nb"])
    # truth exists only where ADWR wells were exported (3 sub-basins): blocks within 8 km of a pumped well
    wx, wy = w.UTM_X_METERS.values, w.UTM_Y_METERS.values
    cx = ((np.arange(geo["nb"]) % geo["nbx"]) + .5) * geo["BL"] * geo["PIX"] + geo["E0"]
    cy = ((np.arange(geo["nb"]) // geo["nbx"]) + .5) * geo["BL"] * geo["PIX"] + geo["N0"]
    near = np.array([np.min(np.hypot(wx - x, wy - y)) < 8000 for x, y in zip(cx, cy)])
    return f[near].assign(site="arizona")


def houston():
    f, geo = blocks("houston")
    q, p = np.zeros((350, 380)), None
    for line in open(f"{R0}/houston/gulf/source_data/gulf2023_2021-06-15.wel"):
        if line.startswith("BEGIN PERIOD"):
            p = int(line.split()[2])
            continue
        s = line.split()
        if p and 232 <= p <= 267 and len(s) == 4:   # monthly periods Jan 2016 - Dec 2018 (267 = Dec 2018)
            q[int(s[1]) - 1, int(s[2]) - 1] -= float(s[3]) / 36
    q *= 365.25 / 1000                                  # m3/d -> thousand m3/yr
    r, c = np.nonzero(q > 0)
    x, y = -134045 + (c + .5) * 1000, 920285 - (r + .5) * 1000          # Albers cell centres
    lon, lat = Transformer.from_crs(5070, 4326, always_xy=True).transform(x, y)
    E, N = Transformer.from_crs(4326, geo["epsg"], always_xy=True).transform(lon, lat)
    b = block_of(geo, E, N)
    f["Q"] = np.bincount(b[b >= 0], q[r, c][b >= 0], minlength=geo["nb"])
    return f.assign(site="houston")


def score(t, p, lo=None, hi=None):
    ok = t > 0
    lr = np.log10(np.maximum(p[ok], 1) / t[ok])
    o = dict(n=int(len(t)), spearman=float(stats.spearmanr(p, t)[0]), med_abs_log10=float(np.median(np.abs(lr))),
             within_x3=float(np.mean(np.abs(lr) <= np.log10(3))), total_err=float(p.sum() / t.sum() - 1))
    if lo is not None:
        o["coverage80"] = float(np.mean((t >= lo) & (t <= hi)))
    return o


L = lambda a: np.log10(np.maximum(np.asarray(a, float), 1.0))
COLS = ["sub_vol", "clay", "built_km2", "irr"]


def fit_predict(tr, te, m, oracle=False):
    tq = tr[tr.Q > 0]
    if m == "M0":
        p = te.area_km2.values * tr.Q.sum() / tr.area_km2.sum()
        res = L(tq.Q) - L(tq.area_km2 * tr.Q.sum() / tr.area_km2.sum())
    elif m == "M1":
        X = tr[["built_km2", "irr"]].values
        coef, _ = nnls(X, tr.Q.values)
        p = te[["built_km2", "irr"]].values @ coef
        res = L(tq.Q) - L(tq[["built_km2", "irr"]].values @ coef)
    elif m == "M2":
        ref = te[te.Q > 0] if oracle else tq
        r = np.median(ref.sub_vol / ref.Q)
        p = te.sub_vol.values / r
        res = L(tq.Q) - L(tq.sub_vol / r)
    elif m == "M3":
        ref = te[te.Q > 0] if oracle else tq
        c1, c0 = np.polyfit(L(ref.clay), L(ref.sub_vol) - L(ref.Q), 1)
        pr = lambda d: 10 ** (L(d.sub_vol) - c0 - c1 * L(d.clay))
        p = pr(te)
        res = L(tq.Q) - L(pr(tq))
    elif m == "M4":
        mu, sd = L(tr[COLS]).mean(0), L(tr[COLS]).std(0) + 1e-9
        mdl = Ridge(alpha=1.0).fit((L(tr[COLS]) - mu) / sd, np.log10(tr.Q + 10))
        pr = lambda d: np.clip(10 ** mdl.predict((L(d[COLS]) - mu) / sd) - 10, 0, None)
        p = pr(te)
        res = L(tq.Q) - L(pr(tq))
    lo, hi = np.percentile(res, [10, 90])
    p = np.asarray(p, float)
    return p, p * 10 ** lo, p * 10 ** hi


def keep(f):
    return f[(f.valid_frac >= 0.25) & (f.clay_frac >= 0.5) & (f.clay > 0) &
             ((f.Q > 0) | (f.sub_mean > 5) | (f.crop_km2 > 1) | (f.built_km2 > 2))].copy()


if __name__ == "__main__":
    sites = {"arizona": keep(arizona()), "houston": keep(houston())}
    out = dict(units={k: int(len(v)) for k, v in sites.items()},
               totals_Mm3={k: round(float(v.Q.sum() / 1e3), 1) for k, v in sites.items()},
               ratio_sub_over_Q={k: round(float(np.median(v[v.Q > 0].sub_vol / v[v.Q > 0].Q)), 4) for k, v in sites.items()},
               within_site_spearman_sub_Q={k: round(float(stats.spearmanr(v.sub_vol, v.Q)[0]), 2) for k, v in sites.items()},
               within_site_spearman_clayratio={k: round(float(stats.spearmanr(v[v.Q > 0].clay, v[v.Q > 0].sub_vol / v[v.Q > 0].Q)[0]), 2)
                                               for k, v in sites.items()},
               transfer={}, oracle={})
    for a, b in (("arizona", "houston"), ("houston", "arizona")):
        tr, te = sites[a], sites[b]
        out["transfer"][f"{a}->{b}"] = {m: score(te.Q.values, *fit_predict(tr, te, m)) for m in ("M0", "M1", "M2", "M3", "M4")}
        out["oracle"][f"{a}->{b}"] = {m: score(te.Q.values, *fit_predict(tr, te, m, oracle=True)) for m in ("M2", "M3")}
    ok = {}
    for m in ("M0", "M1", "M2", "M3", "M4"):
        ok[m] = all(d[m]["spearman"] > 0.3 and d[m]["med_abs_log10"] <= 0.5 and -0.5 <= d[m]["total_err"] <= 1.0
                    for d in out["transfer"].values())
    out["transfers"] = ok
    out["clay_helps"] = all(d["M3"]["med_abs_log10"] < d["M2"]["med_abs_log10"] for d in out["transfer"].values())
    json.dump(out, open(f"{R0}/xsite_model.json", "w"), indent=1)
    for k in ("units", "totals_Mm3", "ratio_sub_over_Q", "within_site_spearman_sub_Q", "within_site_spearman_clayratio", "transfers", "clay_helps"):
        print(k, out[k])
    rows = [dict(split=s, model=m, **{k: round(v, 2) for k, v in d.items()}) for s, dd in out["transfer"].items() for m, d in dd.items()]
    rows += [dict(split=s + " ORACLE", model=m, **{k: round(v, 2) for k, v in d.items()}) for s, dd in out["oracle"].items() for m, d in dd.items()]
    print(pd.DataFrame(rows).to_string(index=False))
