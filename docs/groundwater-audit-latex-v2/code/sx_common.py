"""Shared helpers for the subsidence-cause experiments sx_X??.py (see sx_prereg.md). Runs on the DGX Spark:
data in $SX_DATA (default ~/sx_data, holds bundle.npz from sx_bundle.py), results in $SX_DATA/out.
Grid arrays are (NY, NX) with row 0 at the SOUTH edge (as in synth.py)."""
import json
import os
import numpy as np
import rasterio
from rasterio.warp import reproject, transform_bounds, Resampling
from rasterio.windows import from_bounds
from rasterio.transform import from_origin
from pyproj import Transformer
from scipy import ndimage, stats

DATA = os.environ.get("SX_DATA", os.path.expanduser("~/sx_data"))
OUT = f"{DATA}/out"
os.makedirs(OUT, exist_ok=True)
B = dict(np.load(f"{DATA}/bundle.npz"))
NY, NX, PIX = int(B["NY"]), int(B["NX"]), float(B["PIX"])
E0, N0, EPSG = float(B["E0"]), float(B["N0"]), int(B["epsg"])
CRS = f"EPSG:{EPSG}"
DST_TF = from_origin(E0, N0 + NY * PIX, PIX, PIX)            # north-up; flip to row 0 = south
IY, IX = np.mgrid[0:NY, 0:NX]
XX, YY = (IX + 0.5) * PIX, (IY + 0.5) * PIX                     # metres from the SW corner
LON, LAT = Transformer.from_crs(EPSG, 4326, always_xy=True).transform(XX + E0, YY + N0)
FW = Transformer.from_crs(4326, EPSG, always_xy=True)

T = B["D_da1822"].astype(float)
H = B["H"].astype(float)
BUILT = B["wc_built"].astype(float)
WATER = B["wc_water"] >= 0.5
LAND = np.isfinite(T) & ~WATER
lab, _ = ndimage.label(WATER)
SEA = np.isin(lab, np.unique(lab[-1][WATER[-1]]))              # water connected to the northern edge
DCOAST = ndimage.distance_transform_edt(~SEA) * PIX
RNG = np.random.default_rng(20261119)
BLOCK = (IY // 10) * (NX // 10 + 1) + IX // 10                 # 2 km blocks


def bbox_ll(pad=3000.0):
    lo0, la0 = FW.transform(E0, N0, direction="INVERSE")
    lo1, la1 = FW.transform(E0 + NX * PIX, N0 + NY * PIX, direction="INVERSE")
    d = pad / 111000.0
    return lo0 - d, la0 - d, lo1 + d, la1 + d


def to_grid(src, band=1, resampling=Resampling.average, nodata=None, fn=None):
    """Any raster (path or URL, any CRS) -> model grid (row 0 = south). fn maps the read window first
    (e.g. a class -> 0/1 mask, for area fractions)."""
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="5",
                      GDAL_HTTP_RETRY_DELAY="3"), rasterio.open(src) as s:
        b = transform_bounds("EPSG:4326", s.crs, *bbox_ll(), densify_pts=21)
        w = from_bounds(*b, s.transform).round_offsets().round_lengths()
        a = s.read(band, window=w, boundless=True, fill_value=s.nodata if s.nodata is not None else 0
                   ).astype("float32")
        nd = nodata if nodata is not None else s.nodata
        if nd is not None:
            a[a == nd] = np.nan
        if fn is not None:
            a = np.where(np.isfinite(a), fn(a), np.nan).astype("float32")
        dst = np.full((NY, NX), np.nan, "float32")
        reproject(a, dst, src_transform=s.window_transform(w), src_crs=s.crs, src_nodata=np.nan,
                  dst_transform=DST_TF, dst_crs=CRS, dst_nodata=np.nan, resampling=resampling)
    return np.flipud(dst).astype(float)


def array_to_grid(a, transform, crs, resampling=Resampling.average):
    dst = np.full((NY, NX), np.nan, "float32")
    reproject(np.asarray(a, "float32"), dst, src_transform=transform, src_crs=crs, src_nodata=np.nan,
              dst_transform=DST_TF, dst_crs=CRS, dst_nodata=np.nan, resampling=resampling)
    return np.flipud(dst).astype(float)


def en_to_cell(E, N):
    ix = ((np.asarray(E) - E0) // PIX).astype(int)
    iy = ((np.asarray(N) - N0) // PIX).astype(int)
    ok = (ix >= 0) & (ix < NX) & (iy >= 0) & (iy < NY)
    return iy[ok], ix[ok]


def ll_to_cell(lon, lat):
    return en_to_cell(*FW.transform(np.asarray(lon, float), np.asarray(lat, float)))


def rho(x, y, m=None):
    m = np.isfinite(x) & np.isfinite(y) & (True if m is None else m)
    if m.sum() < 10 or np.nanstd(x[m]) == 0:
        return np.nan
    return float(stats.spearmanr(x[m], y[m])[0])


def shifts(n, min_km=2.0, rng=RNG):
    out = []
    while len(out) < n:
        dy, dx = int(rng.integers(NY)), int(rng.integers(NX))
        if np.hypot(min(dy, NY - dy), min(dx, NX - dx)) * PIX >= min_km * 1000:
            out.append((dy, dx))
    return out


def shift_p(stat, field, obs, n=999, sign=1.0):
    """stat(shifted_field) -> number; field may be a tuple of arrays shifted together."""
    fs = field if isinstance(field, tuple) else (field,)
    null = []
    for dy, dx in shifts(n):
        v = stat(*[np.roll(f, (dy, dx), (0, 1)) for f in fs])
        if np.isfinite(v):
            null.append(v)
    null = np.array(null)
    p = (1 + np.sum(sign * null >= sign * obs)) / (1 + len(null))
    return float(p), dict(null_mean=float(np.mean(null)), null_p95=float(np.percentile(null, 95)),
                          null_p05=float(np.percentile(null, 5)), n=len(null))


def geo_resid(t=None):
    """T minus the mean T in bins of distance-to-coast decile x elevation quintile (land cells)."""
    t = T if t is None else t
    m = LAND & np.isfinite(t)
    qc = np.digitize(DCOAST, np.percentile(DCOAST[m], np.arange(10, 100, 10)))
    qh = np.digitize(H, np.percentile(H[m], [20, 40, 60, 80]))
    key = qc * 5 + qh
    out = np.full(t.shape, np.nan)
    for k in np.unique(key[m]):
        s = m & (key == k)
        out[s] = t[s] - t[s].mean()
    return out


def strata():
    m = LAND
    qb = np.digitize(BUILT, np.percentile(BUILT[m], [20, 40, 60, 80]))
    qc = np.digitize(DCOAST, np.percentile(DCOAST[m], [20, 40, 60, 80]))
    return qb * 5 + qc


def matched_p(sel, n=10000, t=None, sign=1.0, pool=None):
    """Mean T over selected land cells vs random cells (from `pool`, default all land) in the same strata."""
    t = T if t is None else t
    m = LAND & np.isfinite(t)
    sel = sel & m
    pool = m if pool is None else (pool & m)
    st = strata()
    sel = sel & np.isin(st, np.unique(st[pool]))
    pools = {k: np.flatnonzero(pool.ravel() & (st.ravel() == k)) for k in np.unique(st[sel])}
    cnt = {k: int((st[sel] == k).sum()) for k in pools}
    tv = t.ravel()
    null = np.zeros(n)
    for i in range(n):
        idx = np.concatenate([RNG.choice(pools[k], cnt[k]) for k in pools])
        null[i] = tv[idx].mean()
    obs = float(t[sel].mean())
    p = (1 + np.sum(sign * null >= sign * obs)) / (1 + n)
    return obs, float(p), float(null.mean())


def block_cv_r2(X, y, groups=None, reps=5, model=None, seed=0):
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.metrics import r2_score
    groups = BLOCK[LAND] if groups is None else groups
    rs = []
    for r in range(reps):
        rng = np.random.default_rng(seed + r)
        ug = np.unique(groups)
        fold = dict(zip(ug, rng.permutation(len(ug)) % 5))
        f = np.array([fold[g] for g in groups])
        pred = np.zeros(len(y))
        for k in range(5):
            mdl = model() if model else HistGradientBoostingRegressor(max_iter=200, random_state=r)
            mdl.fit(X[f != k], y[f != k])
            pred[f == k] = mdl.predict(X[f == k])
        rs.append(r2_score(y, pred))
    return float(np.mean(rs))


def save(name, result, feats=None, groups=None):
    """result -> out/<name>.json; feats {name: (NY,NX) array} -> out/feat_<name>.npz for X13."""
    json.dump(result, open(f"{OUT}/{name}.json", "w"), indent=1, default=float)
    if feats:
        np.savez_compressed(f"{OUT}/feat_{name}.npz", **{k: np.asarray(v, float) for k, v in feats.items()},
                            _groups=json.dumps(groups or {}))
    print(json.dumps(result, indent=1, default=float)[:3000], flush=True)


def driver_test(name, X, sign=1.0, n=999):
    """Standard driver statistics: rho with T and with the geography residual, both with shift nulls."""
    m = LAND & np.isfinite(X)
    r = rho(X, T, m)
    pr, nr = shift_p(lambda x: rho(x, T, LAND), X, r, n, sign)
    g = geo_resid()
    rg = rho(X, g, m)
    pg, ng = shift_p(lambda x: rho(x, g, LAND), X, rg, n, sign)
    return dict(name=name, n_cells=int(m.sum()), rho=r, p_shift=pr, null=nr, rho_partial=rg,
                p_shift_partial=pg, null_partial=ng,
                linked=bool(sign * r >= 0.2 and pr < 0.05), adds_beyond_geography=bool(pg < 0.05 and sign * rg > 0))


if __name__ == "__main__":                                        # self-check
    assert H[:10].mean() > H[-10:].mean(), "row 0 must be south (hills)"
    assert SEA[-1].any() and not SEA[0].any()
    assert 4000 < LAND.sum() < 9600
    p, _ = shift_p(lambda x: rho(x, T, LAND), DCOAST, rho(DCOAST, T, LAND), 99, -1)
    print("land", LAND.sum(), "rho(dcoast,T)", rho(DCOAST, T, LAND), "p", p, "bbox", bbox_ll())
