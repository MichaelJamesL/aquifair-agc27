"""Shared pieces for the real-data runs: rate map from a LiCSAR stack, model-grid resampling,
background layers, truth layers and location scoring."""
import json
import numpy as np
from scipy import ndimage
from pyproj import Transformer
from matplotlib.path import Path
import rasterio
from rasterio.windows import from_bounds
import synth as S

LAM = 0.055465763                       # Sentinel-1 C-band wavelength, m


def rate_map(stackdir, cc_min=0.15, robust=False, gacos=False, drop_bad=False, gacos_sign=-1.0, min_dt=0):
    """LOS phase stacking -> vertical subsidence (mm/yr, + = sinking) on the native lon/lat grid.
    gacos: subtract the GACOS slant-delay difference of each pair (LiCSAR epochs/*.sltd.geo.tif).
    drop_bad: drop pairs whose reference-area scatter is an outlier (unwrapping/atmosphere failures).
    shortcut: stacking (linear rate), not a full SBAS time series."""
    z = np.load(f"{stackdir}/stack.npz")
    pairs, unw, cc = z["pairs"], z["unw"].copy(), z["cc"]
    dt = np.array([(np.datetime64(f"{p[9:13]}-{p[13:15]}-{p[15:]}") -
                    np.datetime64(f"{p[:4]}-{p[4:6]}-{p[6:8]}")).astype(int) for p in pairs]) / 365.25
    hgt, U, land = z["hgt"], z["U"], z["landmask"]
    valid = np.isfinite(unw) & (unw != 0) & (cc >= cc_min * 255)
    valid[dt * 365.25 < min_dt - 0.5] = False   # short pairs carry phase bias ("fading signal")
    E = None
    if gacos:
        g = np.load(f"{stackdir}/gacos.npz")
        E, U = g["E"], g["U"]
        ei = {e: k for k, e in enumerate(g["epochs"])}
        sl = g["sltd"]
        for k, p in enumerate(pairs):
            a, b = p.split("_")
            if a in ei and b in ei:
                unw[k] = unw[k] + gacos_sign * (sl[ei[b]] - sl[ei[a]])
            else:
                valid[k] = False                 # no correction available: drop the pair
    ref = (hgt > 60) & (land > 0)            # stable hills south of the coastal plain
    los = np.zeros_like(unw)
    rsd = np.full(len(pairs), np.nan)
    for k in range(len(pairs)):
        r = valid[k] & ref
        if r.sum() < 50:
            valid[k] = False
            continue
        m = np.median(unw[k][r])
        rsd[k] = np.median(np.abs(unw[k][r] - m))
        los[k] = np.where(valid[k], unw[k] - m, 0.0)
    if drop_bad:
        ok_p = np.isfinite(rsd)
        med, mad = np.median(rsd[ok_p]), np.median(np.abs(rsd[ok_p] - np.median(rsd[ok_p])))
        bad = ~ok_p | (rsd > med + 3 * 1.4826 * mad)
        valid[bad] = False
        los[bad] = 0.0
    los_mm = los * (-LAM / (4 * np.pi) * 1000)           # LiCSBAS convention: + = towards satellite
    v_los = los_mm.sum(0) / np.maximum((valid * dt[:, None, None]).sum(0), 1e-9)
    used = valid.any((1, 2))                 # coverage over pairs actually used (min_dt, drop_bad)
    ok = (valid[used].mean(0) >= 0.5) & (land > 0)
    if robust:
        # per-pair rates; median resists unwrapping jumps. Drop the noisiest 15 % of pixels by
        # the robust scatter (MAD) of those rates.
        r = np.where(valid, los_mm / dt[:, None, None], np.nan)
        v_los = np.nanmedian(r, 0)
        mad = np.nanmedian(np.abs(r - v_los), 0) / np.sqrt(np.maximum(valid.sum(0), 1))
        ok &= mad <= np.nanpercentile(mad[ok], 85)
    sub = -v_los / U
    return dict(sub=np.where(ok, sub, np.nan), v_los=np.where(ok, v_los, np.nan), U=U, E=E, hgt=hgt,
                transform=z["transform"], pairs=pairs, n_used=int(valid.any((1, 2)).sum()))


def vertical_from_two(rms, grid):
    """Ascending + descending LOS rates -> vertical and east rates on the model grid.
    Per cell: v_los_i = U_i * v_up + E_i * v_east (north term ignored: tiny for near-polar orbits).
    Returns subsidence (+ = sinking), east rate, and the cell mask where both tracks are valid."""
    L, Ug, Eg, ok = [], [], [], np.ones((S.NY, S.NX), bool)
    for rm in rms:
        v, c = grid.block_mean(rm["v_los"], rm["transform"])
        u, _ = grid.block_mean(np.where(np.isfinite(rm["v_los"]), rm["U"], np.nan), rm["transform"])
        e, _ = grid.block_mean(np.where(np.isfinite(rm["v_los"]), rm["E"], np.nan), rm["transform"])
        L.append(v); Ug.append(u); Eg.append(e); ok &= c >= 1
    det = Ug[0] * Eg[1] - Ug[1] * Eg[0]
    up = (L[0] * Eg[1] - L[1] * Eg[0]) / np.where(ok, det, 1)
    east = (Ug[0] * L[1] - Ug[1] * L[0]) / np.where(ok, det, 1)
    return np.where(ok, -up, np.nan), np.where(ok, east, np.nan), ok


def combine_tracks(rms, grid, H, k=3.0):
    """Cross-track QC instead of an E-W solve (which amplifies outliers): average the two
    vertical-only estimates weighted by their stable-ground noise, and drop cells where the tracks
    disagree by more than k robust sigmas of the difference (one of them is wrong there)."""
    Ds, ws, ok = [], [], np.ones((S.NY, S.NX), bool)
    for rm in rms:
        D, c = grid.block_mean(rm["sub"], rm["transform"])
        _, s = stable_noise(D, H, c >= 1)
        Ds.append(D); ws.append(1 / s ** 2); ok &= c >= 1
    diff = Ds[1] - Ds[0]
    med = np.nanmedian(diff[ok])
    sig = 1.4826 * np.nanmedian(np.abs(diff[ok] - med))
    agree = ok & (np.abs(diff - med) <= k * sig)
    D = (ws[0] * Ds[0] + ws[1] * Ds[1]) / (ws[0] + ws[1])
    return np.where(agree, D, np.nan), agree, dict(diff_sigma=float(sig), dropped=float(1 - agree.sum() / ok.sum()))


def model_input_grid(D, mask, clay):
    return dict(d=np.where(mask, D, 0.0), mask=mask, clay_obs=clay)


def stable_noise(D, H, mask):
    """Spread (mm/yr) of the rate on high ground (> 30 m) after removing a plane and a height term."""
    st = mask & (H > 30)
    A = np.c_[np.ones(st.sum()), S.XX[st], S.YY[st], H[st]]
    r = D[st] - A @ np.linalg.lstsq(A, D[st], rcond=None)[0]
    return float(r.std()), float(np.subtract(*np.percentile(r, [75, 25]))) / 1.349


class Grid:
    """24 x 16 km model grid of synth.py with its SW corner at (E0, N0) in UTM `epsg`."""

    def __init__(self, E0, N0, epsg):
        self.E0, self.N0, self.epsg = E0, N0, epsg
        self.fw = Transformer.from_crs(4326, epsg, always_xy=True)
        self.inv = Transformer.from_crs(epsg, 4326, always_xy=True)

    def lonlat_bounds(self, pad=500.0):
        lo0, la0 = self.inv.transform(self.E0 - pad, self.N0 - pad)
        lo1, la1 = self.inv.transform(self.E0 + S.NX * S.PIX + pad, self.N0 + S.NY * S.PIX + pad)
        return lo0, la0, lo1, la1

    def block_mean(self, arr, transform):
        """Average a native lon/lat raster (NaN = no data) into model-grid cells."""
        a, b, c, d, e, f = transform
        ny, nx = arr.shape
        LON, LAT = np.meshgrid(a * (np.arange(nx) + 0.5) + c, e * (np.arange(ny) + 0.5) + f)
        E, N = self.fw.transform(LON, LAT)
        ix = ((E - self.E0) // S.PIX).astype(int)
        iy = ((N - self.N0) // S.PIX).astype(int)
        ok = (ix >= 0) & (ix < S.NX) & (iy >= 0) & (iy < S.NY) & np.isfinite(arr)
        lin = iy[ok] * S.NX + ix[ok]
        cnt = np.bincount(lin, minlength=S.NX * S.NY)
        m = np.bincount(lin, arr[ok], minlength=S.NX * S.NY) / np.maximum(cnt, 1)
        return m.reshape(S.NY, S.NX), cnt.reshape(S.NY, S.NX)

    def sample(self, url, scale=1.0, nodata=None):
        """Nearest-neighbour sample of a (remote) lon/lat GeoTIFF at model-grid centres."""
        lon, lat = self.inv.transform(S.XX + self.E0, S.YY + self.N0)
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"), rasterio.open(url) as s:
            w = from_bounds(*self.lonlat_bounds(2000), s.transform).round_offsets().round_lengths()
            a = s.read(1, window=w).astype(float)
            t = s.window_transform(w)
        if nodata is not None:
            a[a == nodata] = np.nan
        col = ((lon - t.c) / t.a).astype(int).clip(0, a.shape[1] - 1)
        row = ((lat - t.f) / t.e).astype(int).clip(0, a.shape[0] - 1)
        return a[row, col] * scale

    def to_xy(self, lon, lat):
        E, N = self.fw.transform(np.asarray(lon, float), np.asarray(lat, float))
        return np.c_[np.asarray(E) - self.E0, np.asarray(N) - self.N0]


def model_input(rm, grid, clay):
    D, cnt = grid.block_mean(rm["sub"], rm["transform"])
    mask = cnt >= 1
    return dict(d=np.where(mask, D, 0.0), mask=mask, clay_obs=clay), D


# ---- truth layers -------------------------------------------------------------------------------

def pangaea_wells(path, grid):
    rows = [l.rstrip("\n").split("\t") for l in open(path, encoding="utf-8")]
    i0 = [k for k, l in enumerate(rows) if l[0] == "*/"][0]
    W = rows[i0 + 2:]
    xy = grid.to_xy([float(r[4]) for r in W], [float(r[3]) for r in W])
    obs = np.array(["obs" in r[1].lower() or r[0].startswith("SP_") for r in W])
    inside = (xy[:, 0] > 0) & (xy[:, 0] < S.NX * S.PIX) & (xy[:, 1] > 0) & (xy[:, 1] < S.NY * S.PIX)
    return xy[inside & ~obs], xy[inside]


def osm_layers(path, grid):
    """Industrial land as a model-grid boolean raster, plus mapped water wells as points."""
    el = json.load(open(path, encoding="utf-8"))["elements"]
    ind = np.zeros((S.NY, S.NX), bool)
    pts = np.c_[S.XX.ravel(), S.YY.ravel()]
    wells = []
    for e in el:
        tags = e.get("tags", {})
        if tags.get("man_made") == "water_well":
            if "lat" in e:
                wells.append((e["lon"], e["lat"]))
            elif "geometry" in e:
                g = e["geometry"]
                wells.append((np.mean([p["lon"] for p in g]), np.mean([p["lat"] for p in g])))
            continue
        rings = [e["geometry"]] if "geometry" in e else [m["geometry"] for m in e.get("members", [])
                                                         if m.get("role") == "outer" and "geometry" in m]
        for g in rings:
            if len(g) < 3:
                continue
            xy = grid.to_xy([p["lon"] for p in g], [p["lat"] for p in g])
            ind |= Path(xy).contains_points(pts).reshape(S.NY, S.NX)
            ij = (xy // S.PIX).astype(int)                     # tiny polygons: mark their vertices
            ok = (ij[:, 0] >= 0) & (ij[:, 0] < S.NX) & (ij[:, 1] >= 0) & (ij[:, 1] < S.NY)
            ind[ij[ok, 1], ij[ok, 0]] = True
    w = grid.to_xy(*zip(*wells)) if wells else np.zeros((0, 2))
    return ind, w


# ---- scoring ------------------------------------------------------------------------------------

def dist_to_points(src, pts):
    return np.hypot(src[:, None, 0] - pts[None, :, 0], src[:, None, 1] - pts[None, :, 1]).min(1)


def dist_to_raster(src, raster):
    dist = ndimage.distance_transform_edt(~raster) * S.PIX
    ix = (src[:, 0] // S.PIX).astype(int).clip(0, S.NX - 1)
    iy = (src[:, 1] // S.PIX).astype(int).clip(0, S.NY - 1)
    return dist[iy, ix]


def location_test(src, mask, D, dist_fn, tol, rng, n=4000):
    """Hit rate of sources vs two nulls: uniform over coherent land, and drawn in proportion to
    the subsidence rate ('point where it sinks most'). Returns hit, null means and p-values."""
    k = len(src)
    if k == 0:
        return dict(n=0)
    hit = float((dist_fn(src) <= tol).mean())
    mp = np.flatnonzero(mask.ravel())
    pw = np.clip(D.ravel()[mp], 0, None)
    out = dict(n=k, hit=hit)
    for name, p in (("uniform", None), ("rate", pw / pw.sum())):
        pick = rng.choice(mp, n * k, p=p)
        pts = np.c_[S.XX.ravel()[pick], S.YY.ravel()[pick]]
        h = (dist_fn(pts) <= tol).reshape(n, k).mean(1)
        out[f"null_{name}"] = float(h.mean())
        out[f"p_{name}"] = float((h >= hit).mean())
    return out


def resid_sd(sc, fit):
    idx = np.flatnonzero(sc["mask"].ravel())
    Z = S.Zmat(sc["clay_obs"])[idx]
    d = sc["d"].ravel()[idx] - (S.Kfull("k0", fit["param"]) @ fit["qgrid"])[idx]
    beta = np.linalg.lstsq(Z, d, rcond=None)[0]
    return float(np.std(d - Z @ beta))


def grid_hgt(rm, grid):
    return grid.block_mean(np.where(np.isfinite(rm["sub"]), rm["hgt"], np.nan), rm["transform"])[0]


def fit_edge(D, mask, clay):
    """Grid-search one sigmoid step across a straight line (fault / clay-plain edge) that best
    explains D together with the smooth background. Returns the step column (0..1) and params."""
    D0 = np.where(mask, D, 0.0)
    idx0 = np.flatnonzero(mask.ravel())
    Z0 = S.Zmat(clay)[idx0]
    best = (np.inf, None, None)
    for th in np.deg2rad(np.arange(0, 180, 5)):
        s = (S.XX * np.cos(th) + S.YY * np.sin(th)).ravel()
        for s0 in np.arange(s.min(), s.max(), 500.0):
            for wd in (300.0, 700.0, 1500.0):
                col = 1 / (1 + np.exp(-(s - s0) / wd))
                Z = np.column_stack([Z0, col[idx0]])
                r = D0.ravel()[idx0] - Z @ np.linalg.lstsq(Z, D0.ravel()[idx0], rcond=None)[0]
                if r.std() < best[0]:
                    best = (r.std(), col, (float(np.rad2deg(th)), float(s0), wd))
    return best[1], dict(resid_sd=round(float(best[0]), 2), angle_offset_width=best[2])


def use_clay_weighted_kernel(c):
    """Terzaghi/Helm: compaction = compressibility x clay thickness x head drop, so each cone is
    multiplied by the clay factor c(x) (model grid, 0..1). Patches synth.Kfull (cached)."""
    orig = S.Kfull
    cache = {}
    cr = c.ravel()[:, None]

    def K(fam, p):
        if (fam, p) not in cache:
            cache[(fam, p)] = cr * orig(fam, p)
        return cache[(fam, p)]

    S.Kfull = K


def background(bg, H, D, mask, grid):
    """Background layer(s) for Zmat on the model grid. H = elevation, D = subsidence rate, mask =
    valid cells. Extra columns are added by wrapping S.Zmat (call once per process)."""
    if bg == "lowground":
        clay = np.clip((20.0 - H) / 20.0, 0, 1.3)
    elif bg == "dtb":
        # SoilGrids 2017 absolute depth to bedrock (cm), 250 m: proxy for soft-sediment thickness
        dtb = grid.sample("/vsicurl/https://files.isric.org/soilgrids/former/2017-03-10/data/BDTICM_M_250m_ll.tif",
                                          scale=0.01, nodata=-32768)
        clay = dtb / np.nanmax(dtb)
        clay = np.where(np.isfinite(clay), clay, np.nanmean(clay))
    elif bg == "flat":
        clay = np.zeros((S.NY, S.NX))
    elif bg == "hgtbins":
        # extra background columns: smoothed 'below h metres' indicators, to follow the sharp
        # coastal-plain edge that one linear clay column cannot
        clay = np.clip((20.0 - H) / 20.0, 0, 1.3)
        extra = [ndimage.gaussian_filter((H < h).astype(float), 1.0).ravel() for h in (3, 6, 10, 15)]
        _Z = S.Zmat
        S.Zmat = lambda c: np.column_stack([_Z(c)] + extra)
    elif bg == "edge":
        # one fitted step (sigmoid across a straight line): the edge of the soft-clay plain.
        # Grid search on the background-only fit; the step then becomes an unpenalised Zmat column.
        clay = np.clip((20.0 - H) / 20.0, 0, 1.3)
        edge_col, info = fit_edge(D, mask, clay)
        print("edge fit:", info, flush=True)
        _Z = S.Zmat
        S.Zmat = lambda c: np.column_stack([_Z(c), edge_col])
    else:
        raise ValueError(bg)
    return clay


def use_robust_floor(k=3.0):
    """Replace synth.surrogate_floor by a version that clips the residual at k robust sigmas before
    building surrogates, so local non-pumping motions (fills, landfills, quarries) do not inflate
    the noise spectrum. Same algorithm otherwise."""
    orig = S.surrogate_floor

    def floor(sc, fam, p, qgrid, idx, rng, n_sur=30, pct=95):
        Zf = S.Zmat(sc["clay_obs"])
        A = S.Kfull(fam, p)
        d = sc["d"].ravel()
        beta = np.linalg.lstsq(Zf[idx], d[idx] - A[idx] @ qgrid, rcond=None)[0]
        r = d[idx] - A[idx] @ qgrid - Zf[idx] @ beta
        sig = 1.4826 * np.median(np.abs(r - np.median(r)))
        dc = d.copy()
        dc[idx] = d[idx] - r + np.clip(r, -k * sig, k * sig)
        return orig(dict(sc, d=dc.reshape(S.NY, S.NX)), fam, p, qgrid, idx, rng, n_sur, pct)

    S.surrogate_floor = floor
