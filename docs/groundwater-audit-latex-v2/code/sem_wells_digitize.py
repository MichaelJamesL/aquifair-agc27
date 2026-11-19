"""Digitize the green 'Deep well' dots of Lo et al. 2022 (Water 14:201, CC BY) Fig. 12, page 16
(registry well locations from the Mining and Energy Agency of Central Java).

1. The figure is two embedded rasters (top/bottom halves); they are stacked into fig12.png.
2. Georeference: the 16 graticule ticks outside the black map frame (5 longitude ticks top and
   bottom, 3 latitude ticks left and right) -> affine pixel -> lon/lat fit, residuals in metres.
3. Dots: bright-green connected components inside the frame, outside the legend box and the
   recharge inset; one point per blob (overlapping dots counted once, merged blobs flagged).
4. Independent checks: the Fig. 12 coastline (blue line with sea above it) vs the WorldCover 2021
   coastline on the model grid (median distance, signed N offset per reach), and the eastern river
   vs WorldCover 10 m permanent water (2-D shift search).
Writes realdata/semarang/registry_wells/: fig12.png, fig12_wells.csv, fig12_georef.json,
fig12_qa_dots.png, fig12_qa_coast.png (+ worldcover10m_window.npz cache)."""
import json, os
import fitz
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import synth as S
import real_goal_maps as GM

PDF = "C:/Kuliah/hackathon/agc-26/docs/groundwater-audit-latex-v2/water-14-00201-v2.pdf"   # not in git
OUT = f"{GM.ROOT}/registry_wells"
LON = 110 + np.array([15, 20, 25, 30, 35]) / 60          # tick labels, west -> east
LAT = -(np.array([6 + 55 / 60, 7.0, 7 + 5 / 60]))       # tick labels, north -> south
# shortcut: legend box and recharge inset are fixed pixel boxes of this one figure (x0, y0, x1, y1)
LEGEND, INSET = (1070, 343, 1404, 756), (48, 625, 275, 852)

# ---- 1. figure raster -----------------------------------------------------------------------
doc = fitz.open(PDF)
page = doc[15]
parts = sorted(page.get_image_info(xrefs=True), key=lambda i: i["bbox"][1])
ims = [np.asarray(Image.open(__import__("io").BytesIO(doc.extract_image(p["xref"])["image"])).convert("RGB"))
       for p in parts]
a = np.vstack(ims).astype(int)
Image.fromarray(a.astype(np.uint8)).save(f"{OUT}/fig12.png")
R_, G_, B_ = a[..., 0], a[..., 1], a[..., 2]
dark = a.mean(2) < 100
ny, nx = dark.shape

# ---- 2. frame + ticks -----------------------------------------------------------------------
rows, cols = dark.sum(1), dark.sum(0)
top, bot = int(np.argmax(rows[:ny // 2])), ny // 2 + int(np.argmax(rows[ny // 2:]))
lef, rig = int(np.argmax(cols[:nx // 2])), nx // 2 + int(np.argmax(cols[nx // 2:]))


def ticks(band, lo):
    """Centroids of dark runs in a 1-D darkness profile (mean over a band of rows/cols)."""
    lab, n = ndimage.label(band > 0.5)
    return np.array([lo + ndimage.center_of_mass(band * (lab == k))[0] for k in range(1, n + 1)])


band = lambda r0, r1, c0, c1, ax: dark[r0:r1, c0:c1].mean(ax)
tx_top = ticks(band(top - 7, top - 2, lef + 3, rig - 2, 0), lef + 3)
tx_bot = ticks(band(bot + 3, bot + 8, lef + 3, rig - 2, 0), lef + 3)
ty_lef = ticks(band(top + 3, bot - 2, lef - 7, lef - 2, 1), top + 3)
ty_rig = ticks(band(top + 3, bot - 2, rig + 3, rig + 8, 1), top + 3)
assert len(tx_top) == len(tx_bot) == 5 and len(ty_lef) == len(ty_rig) == 3, (tx_top, tx_bot, ty_lef, ty_rig)



def centre(prof, k):
    """Sub-pixel centre of the 2-3 px frame line peaking at index k."""
    w = prof[k - 2:k + 3] * (prof[k - 2:k + 3] > 0.5 * prof[k])
    return k - 2 + float((w * np.arange(5)).sum() / w.sum())


yt, yb, xl, xr = centre(rows, top), centre(rows, bot), centre(cols, lef), centre(cols, rig)
P_lon = np.r_[np.c_[tx_top, np.full(5, yt)], np.c_[tx_bot, np.full(5, yb)]]
P_lat = np.r_[np.c_[np.full(3, xl), ty_lef], np.c_[np.full(3, xr), ty_rig]]
A1 = lambda P: np.c_[P, np.ones(len(P))]
c_lon = np.linalg.lstsq(A1(P_lon), np.r_[LON, LON], rcond=None)[0]
c_lat = np.linalg.lstsq(A1(P_lat), np.r_[LAT, LAT], rcond=None)[0]
MLON, MLAT = 111320 * np.cos(np.radians(7.0)), 110574.0        # metres per degree at 7 S
res_m = np.r_[(A1(P_lon) @ c_lon - np.r_[LON, LON]) * MLON, (A1(P_lat) @ c_lat - np.r_[LAT, LAT]) * MLAT]
rms_tick = float(np.sqrt(np.mean(res_m ** 2)))
to_ll = lambda px, py: (A1(np.c_[px, py]) @ c_lon, A1(np.c_[px, py]) @ c_lat)
m_per_px = (abs(c_lon[0]) * MLON, abs(c_lat[1]) * MLAT)

# ---- 3. green dots --------------------------------------------------------------------------
YY, XX = np.mgrid[:ny, :nx]
inbox = lambda b: (XX >= b[0]) & (XX <= b[2]) & (YY >= b[1]) & (YY <= b[3])
inside = (XX > lef + 2) & (XX < rig - 2) & (YY > top + 2) & (YY < bot - 2)
green = (G_ - np.maximum(R_, B_) > 80) & (G_ > 120) & (B_ < 80)
lab, n = ndimage.label(green, np.ones((3, 3)))
area = ndimage.sum(green, lab, range(1, n + 1))
cy, cx = np.array(ndimage.center_of_mass(green, lab, range(1, n + 1))).T
ix, iy = cx.round().astype(int), cy.round().astype(int)
legend_dot = inbox(LEGEND)[iy, ix] & (area >= 15)
assert legend_dot.sum() == 1, "legend sample dot not where expected"
keep = inside[iy, ix] & ~inbox(LEGEND)[iy, ix] & ~inbox(INSET)[iy, ix] & (area >= 15) & (area <= 400)
cx, cy, area = cx[keep], cy[keep], area[keep]
single = float(np.median(area))
merged = area > 1.6 * single
n_est = np.maximum(1, np.round(area / single)).astype(int)
lon, lat = to_ll(cx, cy)
E, N = GM.grid.fw.transform(lon, lat)
assert 40 <= len(cx) <= 200, len(cx)
assert rms_tick < 30.0, rms_tick          # < 1 figure pixel (~30 m)

with open(f"{OUT}/fig12_wells.csv", "w") as f:
    f.write("id,px,py,lon,lat,E,N,area_px,n_dots_est\n")
    for k in range(len(cx)):
        f.write(f"{k + 1},{cx[k]:.2f},{cy[k]:.2f},{lon[k]:.6f},{lat[k]:.6f},{E[k]:.1f},{N[k]:.1f},{int(area[k])},{n_est[k]}\n")

fig, ax = plt.subplots(figsize=(14.65, 9.08), dpi=100)
ax.imshow(a.astype(np.uint8)); ax.axis("off")
for k in range(len(cx)):
    ax.add_patch(plt.Circle((cx[k], cy[k]), 7 if not merged[k] else 10, fill=False, color="m" if merged[k] else "k", lw=0.8))
    ax.text(cx[k] + 6, cy[k] - 5, str(k + 1), fontsize=5, color="k")
for b in (LEGEND, INSET):
    ax.add_patch(plt.Rectangle(b[:2], b[2] - b[0], b[3] - b[1], fill=False, ec="c", ls="--"))
ax.plot(np.r_[tx_top, tx_bot], np.r_[np.full(5, yt), np.full(5, yb)], "r+", ms=10)
ax.plot(np.r_[np.full(3, xl), np.full(3, xr)], np.r_[ty_lef, ty_rig], "r+", ms=10)
fig.subplots_adjust(0, 0, 1, 1)
fig.savefig(f"{OUT}/fig12_qa_dots.png")
plt.close(fig)

# ---- 4. independent checks: coastline and the eastern river vs WorldCover ----------------------
blue = (B_ > 150) & (R_ < 100) & (B_ - G_ > 40) & inside & ~inbox(LEGEND)
white = a.min(2) > 235
coast = []
for x in range(lef + 3, rig - 2):
    ys = np.flatnonzero(blue[:, x])
    if len(ys) and white[max(ys[0] - 4, 0):ys[0] - 1, x].all():   # sea (white) right above the topmost blue
        coast.append((x, ys[0] + 2.0))                            # centre of the ~4 px line
coast = np.array(coast)
clon, clat = to_ll(coast[:, 0], coast[:, 1])
cE, cN = GM.grid.fw.transform(clon, clat)
cx_, cy_ = cE - GM.grid.E0, cN - GM.grid.N0
ing = (cx_ > 0) & (cx_ < S.NX * S.PIX) & (cy_ > 0) & (cy_ < S.NY * S.PIX)
cx_, cy_ = cx_[ing], cy_[ing]
water = np.load(f"{GM.ROOT}/worldcover_grid.npz")["water"]
# WorldCover 2021 coastline: per grid column, top edge of the northernmost land cell (water < 0.5)
col = (cx_ // S.PIX).astype(int)
dN = cy_ - np.array([(np.flatnonzero(water[:, c] < 0.5).max() + 1) * S.PIX for c in col])
cs = plt.contour(S.XX[0], S.YY[:, 0], water, levels=[0.5])
seg = np.vstack([np.vstack([np.linspace(s[i], s[i + 1], 11) for i in range(len(s) - 1)])
                 for s in cs.allsegs[0] if len(s) > 1])
plt.close("all")
dist_coast = cKDTree(seg).query(np.c_[cx_, cy_])[0]
reach = {"west (x < 7.5 km)": cx_ < 7500, "harbour (7.5-9.8 km)": (cx_ >= 7500) & (cx_ < 9800), "east (x >= 9.8 km)": cx_ >= 9800}
coast_res = dict(n_points=int(ing.sum()), lon_range=[float(clon[ing].min()), float(clon[ing].max())],
                 median_dist_to_worldcover_coast_m=float(np.median(dist_coast)),
                 median_dN_fig_minus_worldcover_m={k: float(np.median(dN[m])) for k, m in reach.items()})

# Eastern river (engineered canal, wide enough to be WorldCover 'permanent water' at 10 m): 2-D shift
# search of the Fig. 12 river pixels against the 10 m water mask, +-1 km in 25 m steps
WC10 = f"{OUT}/worldcover10m_window.npz"
if not os.path.exists(WC10):
    import rasterio
    from rasterio.windows import from_bounds
    URL = "/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S09E108_Map.tif"
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"), rasterio.open(URL) as s:
        w = from_bounds(110.20, -7.25, 110.62, -6.88, s.transform).round_offsets().round_lengths()
        np.savez_compressed(WC10, wc=s.read(1, window=w), transform=np.array(s.window_transform(w))[:6])
z = np.load(WC10)
wc, t = z["wc"], z["transform"]
dwat = ndimage.distance_transform_edt(wc != 80) * abs(t[4]) * MLAT        # metres to nearest water pixel
ry, rx = np.nonzero(blue & ~ndimage.binary_dilation(white, iterations=8))  # rivers = blue away from the sea
rlon, rlat = to_ll(rx, ry)
east = rlon >= 110.42
rlon, rlat = rlon[east], rlat[east]
sh = np.arange(-1000, 1001, 25.0)


def rdist(dx, dy):
    c = ((rlon + dx / MLON - t[2]) / t[0]).astype(int)
    r = ((rlat + dy / MLAT - t[5]) / t[4]).astype(int)
    return float(np.median(dwat[r, c]))


G2 = np.array([[rdist(dx, dy) for dx in sh] for dy in sh])
by, bx = np.unravel_index(np.argmin(G2), G2.shape)
river_res = dict(n_pixels=int(len(rlon)), median_dist_at_zero_m=rdist(0, 0),
                 best_shift_m=dict(dE=float(sh[bx]), dN=float(sh[by])), median_dist_at_best_m=float(G2[by, bx]))
offset = coast_res["median_dist_to_worldcover_coast_m"]
assert np.hypot(sh[bx], sh[by]) < 500, river_res     # georeference rule: a rigid offset > 500 m must be fixed first

fig, ax = plt.subplots(figsize=(10, 7))
ax.imshow(water, origin="lower", extent=[0, S.NX * S.PIX / 1e3, 0, S.NY * S.PIX / 1e3], cmap="Blues", vmin=0, vmax=1)
ax.plot(cx_ / 1e3, cy_ / 1e3, "r.", ms=2, label="Fig. 12 coastline")
ax.plot(seg[:, 0] / 1e3, seg[:, 1] / 1e3, "k,", label="WorldCover 2021 water = 0.5")
rE, rN = GM.grid.fw.transform(rlon, rlat)
ax.plot((rE - GM.grid.E0) / 1e3, (rN - GM.grid.N0) / 1e3, "m,", label="Fig. 12 eastern river")
wx, wy = E - GM.grid.E0, N - GM.grid.N0
ax.plot(wx / 1e3, wy / 1e3, "o", mfc="lime", mec="k", ms=4, label="digitized wells")
ax.set_xlim(0, S.NX * S.PIX / 1e3); ax.set_ylim(0, S.NY * S.PIX / 1e3)
ax.set_title(f"Fig. 12 vs WorldCover: coast median distance {offset:.0f} m; "
             f"eastern river best shift ({sh[bx]:.0f}, {sh[by]:.0f}) m", fontsize=10)
ax.set_xlabel("km east of grid origin"); ax.set_ylabel("km north"); ax.legend(loc="lower left", fontsize=8)
fig.savefig(f"{OUT}/fig12_qa_coast.png", dpi=130)

geo = dict(source="Lo et al. 2022, Water 14:201, Fig. 12 (page 16), two embedded rasters stacked",
           image_size=[int(nx), int(ny)], frame=dict(top=float(yt), bottom=float(yb), left=float(xl), right=float(xr)),
           ticks=dict(lon_values=LON.tolist(), top_px=tx_top.tolist(), bottom_px=tx_bot.tolist(),
                      lat_values=LAT.tolist(), left_py=ty_lef.tolist(), right_py=ty_rig.tolist()),
           affine_lon=c_lon.tolist(), affine_lat=c_lat.tolist(), m_per_px=list(m_per_px),
           tick_residuals_m=res_m.round(2).tolist(), tick_rms_m=rms_tick, coastline_check=coast_res, east_river_check=river_res,
           georef_rms_for_jitter_m=max(rms_tick, offset),
           dots=dict(n_blobs=int(len(cx)), n_merged_blobs=int(merged.sum()), n_dots_est=int(n_est.sum()),
                     single_dot_area_px=single, excluded_legend_dot=1,
                     excluded_inset_components=int((inbox(INSET)[iy, ix] & green[iy, ix]).sum())))
json.dump(geo, open(f"{OUT}/fig12_georef.json", "w"), indent=1)
print(json.dumps({k: v for k, v in geo.items() if k not in ("ticks",)}, indent=1))
