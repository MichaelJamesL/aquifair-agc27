"""Linear subsidence rate (vertical-only, + = sinking, mm/yr) on a 200 m grid from the binned
OPERA DISP-S1 granules (az_opera_fetch.py) of the site frame (opera_site.py, env SITE).

Steps: chain ministacks (each granule is relative to its own reference date; the cumulative
offset at a new reference is the previous ministack's displacement at that date), remove a
per-epoch spatial median (DISP-S1 is not tied to a common spatial datum between products), robust
(IRLS Huber) fit of offset + rate + annual sin/cos per cell, LOS -> vertical with the static
up-component. Run in WSL env `alos`.
"""
import sys, glob, json, datetime as dt
import numpy as np
import rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from opera_site import SITE, WSL_ROOT as ROOT

E0, N0, PIX, NX, NY = SITE["grid"]
files = sorted(glob.glob(f"{ROOT}/opera/*.npz"))
G = []
for f in files:
    z = np.load(f)
    G.append(dict(ref=str(z["ref"])[:8], sec=str(z["sec"])[:8], mean=z["mean"].astype(np.float64), cnt=z["cnt"]))
refs = sorted(set(g["ref"] for g in G))
by = {(g["ref"], g["sec"]): g for g in G}

# --- chain ministacks: C[r_k] = C[r_{k-1}] + disp(r_{k-1} -> r_k)
C = {refs[0]: np.zeros((NY, NX))}
for a, b in zip(refs[:-1], refs[1:]):
    if (a, b) not in by:
        raise SystemExit(f"missing chaining granule {a}->{b}")
    C[b] = C[a] + by[(a, b)]["mean"]
ep = {}
for g in G:
    d = C[g["ref"]] + g["mean"]
    good = g["cnt"] >= 20                                  # >= 20 of ~44 good 30 m pixels per cell
    ep.setdefault(g["sec"], []).append(np.where(good, d, np.nan))
WIN = sys.argv[1:3] if len(sys.argv) > 2 else None    # optional YYYYMMDD window for period maps
TAG = sys.argv[3] if len(sys.argv) > 3 else ""
dates = [s for s in sorted(ep) if not WIN or WIN[0] <= s <= WIN[1]]
cube = np.stack([np.nanmean(np.stack(ep[s]), 0) for s in dates])  # duplicates (boundary dates) averaged
t = np.array([(dt.datetime.strptime(s, "%Y%m%d") - dt.datetime(2016, 1, 1)).days / 365.25 for s in dates])
valid_frac = np.isfinite(cube).mean(0)
cells = valid_frac >= 0.8
cube -= np.nanmedian(np.where(cells, cube, np.nan).reshape(len(t), -1), 1)[:, None, None]

# --- robust per-cell fit: d = a + v t + s sin + c cos (IRLS, Huber k = 1.345 sigma)
A = np.c_[np.ones_like(t), t - t.mean(), np.sin(2 * np.pi * t), np.cos(2 * np.pi * t)]
Y = cube.reshape(len(t), -1)[:, cells.ravel()]
W = np.isfinite(Y).astype(float)
Y0 = np.nan_to_num(Y)
coef = np.zeros((4, Y.shape[1]))
for it in range(6):
    for j in range(0, Y.shape[1], 20000):
        w = W[:, j:j + 20000]
        AtWA = np.einsum("ti,tn,tk->nik", A, w, A)
        AtWy = np.einsum("ti,tn->ni", A, w * Y0[:, j:j + 20000])
        coef[:, j:j + 20000] = np.linalg.solve(AtWA + 1e-9 * np.eye(4), AtWy[..., None])[..., 0].T
    r = (Y0 - A @ coef) * (W > 0)
    s = 1.4826 * np.median(np.abs(np.where(W > 0, r, np.nan)), 0, keepdims=True) if False else \
        1.4826 * np.nanmedian(np.abs(np.where(np.isfinite(Y), r, np.nan)), 0, keepdims=True)
    u = np.abs(r) / np.maximum(1.345 * s, 1e-6)
    W = np.isfinite(Y) * np.where(u <= 1, 1.0, 1.0 / np.maximum(u, 1e-6))
v_los = np.full(NY * NX, np.nan)
amp = np.full(NY * NX, np.nan)
rms = np.full(NY * NX, np.nan)
v_los[cells.ravel()] = coef[1] * 1000                       # m/yr -> mm/yr, + = towards satellite
amp[cells.ravel()] = np.hypot(coef[2], coef[3]) * 1000
rms[cells.ravel()] = 1000 * 1.4826 * np.nanmedian(np.abs(np.where(np.isfinite(Y), Y0 - A @ coef, np.nan)), 0)


# --- static layers to the 200 m grid
def binned(path, band=1):
    with rasterio.open(path) as s:
        x0, y0 = s.transform.c, s.transform.f
        win = rasterio.windows.from_bounds(E0, N0, E0 + NX * PIX, N0 + NY * PIX, s.transform).round_offsets().round_lengths()
        a = s.read(band, window=win).astype(float)
        tr = s.window_transform(win)
    nd = np.isnan(a) | (a == 0) if band != 0 else np.isnan(a)
    X = tr.c + tr.a * (np.arange(a.shape[1]) + .5)
    Yc = tr.f + tr.e * (np.arange(a.shape[0]) + .5)
    ix = ((X - E0) // PIX).astype(int)[None, :].repeat(a.shape[0], 0)
    iy = ((Yc - N0) // PIX).astype(int)[:, None].repeat(a.shape[1], 1)
    ok = ~nd & (ix >= 0) & (ix < NX) & (iy >= 0) & (iy < NY)
    lin = iy[ok] * NX + ix[ok]
    c = np.bincount(lin, minlength=NX * NY)
    return (np.bincount(lin, a[ok], minlength=NX * NY) / np.maximum(c, 1)).reshape(NY, NX)


st = f"{ROOT}/opera_static/OPERA_L3_DISP-S1-STATIC_{SITE['frame']}_{SITE['static_date']}_S1A_v1.0_"
U = binned(st + "line_of_sight_enu.tif", 3)
H = binned(st + "dem.tif", 1)
sub = np.where(cells & (U > 0.3), -v_los.reshape(NY, NX) / np.where(U > 0.3, U, 1), np.nan)
mask = np.isfinite(sub)
np.savez_compressed(f"{ROOT}/opera_rate_200m{TAG}.npz", D=np.nan_to_num(sub).astype(np.float32), mask=mask,
                    v_los=v_los.reshape(NY, NX).astype(np.float32), U=U.astype(np.float32), H=H.astype(np.float32),
                    seasonal_amp_los=amp.reshape(NY, NX).astype(np.float32), rms_los=rms.reshape(NY, NX).astype(np.float32),
                    E0=E0, N0=N0, PIX=PIX, NX=NX, NY=NY, epsg=SITE["epsg"], frame=SITE["frame"], track=SITE["track"], direction=SITE["direction"],
                    period=f"{dates[0]}-{dates[-1]}", n_epochs=len(dates), dates=np.array(dates))
fig, ax = plt.subplots(figsize=(8, 8.5))
im = ax.imshow(np.where(mask, sub, np.nan), origin="lower", cmap="turbo", vmin=-10, vmax=np.nanpercentile(sub, 99.9),
               extent=[E0, E0 + NX * PIX, N0, N0 + NY * PIX])
plt.colorbar(im, label="subsidence mm/yr (vertical-only, + sinking)")
ax.set_title(f"OPERA DISP-S1 {SITE['frame']} (T{SITE['track']}) {dates[0]}-{dates[-1]}, {len(dates)} epochs")
fig.savefig(f"{ROOT}/opera_rate_200m{TAG}.png", dpi=110, bbox_inches="tight")
from pyproj import Transformer
inv = Transformer.from_crs(SITE["epsg"], 4326, always_xy=True)
q = np.where(mask, sub, -np.inf)
top = np.argsort(q.ravel())[::-1]
peaks, used = [], np.zeros(NY * NX, bool)
for k in top:
    if len(peaks) >= 8:
        break
    iy, ix = divmod(k, NX)
    if any(np.hypot(iy - a, ix - b) < 25 for a, b, *_ in peaks):
        continue
    lo, la = inv.transform(E0 + (ix + .5) * PIX, N0 + (iy + .5) * PIX)
    peaks.append((iy, ix, float(sub[iy, ix]), round(lo, 3), round(la, 3)))
print(json.dumps(dict(epochs=len(dates), period=[dates[0], dates[-1]], refs=len(refs), valid_cells=int(mask.sum()),
                      frac_valid=round(float(mask.mean()), 3),
                      rate_pct=[round(float(x), 1) for x in np.nanpercentile(sub, [1, 5, 50, 95, 99, 99.9])],
                      max=round(float(np.nanmax(sub)), 1), U_range=[round(float(np.nanmin(U[mask])), 3), round(float(np.nanmax(U[mask])), 3)],
                      median_rms_los_mm=round(float(np.nanmedian(rms)), 1), median_seasonal_amp_los_mm=round(float(np.nanmedian(amp)), 1),
                      peaks_mm_yr_lon_lat=[p[2:] for p in peaks]), indent=1))
