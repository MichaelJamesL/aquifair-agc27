"""L3: soft-sediment thickness at 16 boreholes from Lo et al. 2022 Fig. 5 (two lithology sections), positioned with the
section lines on Fig. 4 (geology map), interpolated to the model grid and compared with the sinking map.
Local run (PDF on the laptop): SX_DATA=<realdata>/semarang/sx python sx_L3.py -> out/L3.json, out/feat_L3.npz."""
import csv
import fitz
import numpy as np
from scipy import ndimage
from scipy.interpolate import griddata
import sx_common as C

PDF = "C:/Kuliah/hackathon/agc-26/docs/groundwater-audit-latex-v2/water-14-00201-v2.pdf"
pm = fitz.open(PDF)[6].get_pixmap(dpi=300)
a = np.frombuffer(pm.samples, np.uint8).reshape(pm.h, pm.w, pm.n)[..., :3].astype(float)
K = 1654 / 1624 * 1.5                                   # screen px (1624-wide page view) -> 300 dpi px
REF = {"clay": (91, 203, 249), "lens": (254, 100, 69), "sand": (253, 161, 142)}
# Fig. 5 sections: borehole x (screen px), axis (y of 0 m, px per m), distance along section (m)
SEC_A = dict(y0=1193, ppm=41.3 / 20, holes=[("G", 197, 6), ("G1", 367, 5), ("G2", 485, 5), ("D", 574, 5),
                                              ("G4a", 605, 5), ("G5", 653, 5), ("H", 741, -6)])
SEC_B = dict(y0=1254, ppm=75.8 / 50, holes=[("G4", 850, 6), ("C7", 970, 5), ("G3", 1040, 5), ("C6", 1063, 5),
                                              ("C5", 1103, 5), ("C4", 1193, 5), ("C3", 1222, 5), ("C2", 1343, 5),
                                              ("C", 1393, -6)])
DIST_B = {"G4": 0, "C7": 1390, "G3": 2200, "C6": 2470, "C5": 2930, "C4": 3970, "C3": 4300, "C2": 5700, "C": 6280}


def column(x, off, y0, ppm):
    """Ground elevation, top of sandstone (m) and clay-only thickness at one borehole line."""
    xs = [int(round(x * K)) + off + d for d in (-1, 0, 1)]
    col = a[int(1080 * K):int(1500 * K), xs].mean(1)
    dist = {k: np.linalg.norm(col - np.array(v), axis=1) for k, v in REF.items()}
    cls = np.full(len(col), "", object)
    best = np.argmin(np.stack(list(dist.values())), 0)
    ok = np.min(np.stack(list(dist.values())), 0) < 40
    cls[ok] = np.array(list(REF))[best[ok]]
    rows = np.arange(len(col)) + int(1080 * K)
    elev = lambda r: -(r / K - y0) / ppm
    filled = np.flatnonzero(cls != "")
    g = rows[filled[0]]
    sand = rows[np.flatnonzero(cls == "sand")[0]]
    return elev(g), elev(sand), (cls[(rows >= g) & (rows < sand)] == "clay").sum() / K / ppm


holes = []
for sec in (SEC_A, SEC_B):
    for name, x, off in sec["holes"]:
        got = []                                         # borehole lines are drawn double: sample both sides, 8-16 px out
        for o in (8, 12, 16, -8, -12, -16):
            try:
                got.append(column(x, int(np.sign(off)) * o if abs(off) == 6 else o, sec["y0"], sec["ppm"]))
            except IndexError:
                pass
        g, s, c = np.median(np.array(got), 0)
        holes.append(dict(name=name, ground_m=g, sandstone_top_m=s, soft_thickness_m=g - s, clay_only_m=c))
hb = {h["name"]: h for h in holes}
hb["C"]["soft_thickness_m"] = hb["C"]["clay_only_m"]      # hill edge: sloping sandstone confuses the column read
hb["G4"]["note"] = f"sections disagree: {hb['G4a']['soft_thickness_m']:.0f} (W-E) vs {hb['G4']['soft_thickness_m']:.0f} m (N-S); mean used"
hb["G4"]["soft_thickness_m"] = (hb["G4"]["soft_thickness_m"] + hb.pop("G4a")["soft_thickness_m"]) / 2
holes = list(hb.values())
for h in holes:
    h.setdefault("note", "")
# positions: section lines on the Fig. 4 zoom (600 dpi clip at pdf points x 220-330, y 215-270)
z2p = lambda x, y: ((220 + x / (600 / 72)) * 300 / 72, (215 + y / (600 / 72)) * 300 / 72)
lon = lambda X: 110 + 20 / 60 + (X - 922.5) / (1358.0 - 922.5) * (10 / 60)
lat = lambda Y: -(6 + 50 / 60) - (Y - 639.5) / (1074.5 - 639.5) * (10 / 60)
PA = {"G": (108, 218), "G1": (302, 243), "G2": (430, 203), "D": (484, 130), "G4a": (548, 165), "G5": (598, 157),
      "H": (695, 146)}
LINE_B = np.array([(548, 165), (527, 190), (512, 240), (520, 316), (481, 386), (480, 412)], float)
seg = np.r_[0, np.cumsum(np.hypot(*np.diff(LINE_B, axis=0).T))]
for h in holes:
    if h["name"] in PA:
        zx, zy = PA[h["name"]]
    else:
        f = DIST_B[h["name"]] / DIST_B["C"] * seg[-1]
        zx, zy = np.interp(f, seg, LINE_B[:, 0]), np.interp(f, seg, LINE_B[:, 1])
    X, Y = z2p(zx, zy)
    h["lon"], h["lat"] = float(lon(X)), float(lat(Y))
    iy, ix = C.ll_to_cell([h["lon"]], [h["lat"]])
    h["in_grid"] = len(iy) == 1
    h["T_3x3"] = float(np.nanmean(C.T[max(iy[0] - 1, 0):iy[0] + 2, max(ix[0] - 1, 0):ix[0] + 2])) if len(iy) else None
assert all(5 <= h["soft_thickness_m"] <= 130 for h in holes if h["name"] != "C"), holes
with open(f"{C.OUT}/L3_boreholes.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(holes[0]))
    w.writeheader(); w.writerows(holes)
# interpolate: boreholes + zero thickness at the hill foot (H > 25 m), linear inside, nearest outside
E, N = C.FW.transform([h["lon"] for h in holes], [h["lat"] for h in holes])
pts = np.c_[np.array(E) - C.E0, np.array(N) - C.N0]
hill = ndimage.binary_opening(C.H > 25, iterations=1)
edge = hill & ~ndimage.binary_erosion(hill)
P = np.r_[pts, np.c_[C.XX[edge], C.YY[edge]][::3]]
V = np.r_[[h["soft_thickness_m"] for h in holes], np.zeros(edge[edge].size)[::3]]
thk = griddata(P, V, (C.XX, C.YY), "linear")
thk = np.where(np.isfinite(thk), thk, griddata(P, V, (C.XX, C.YY), "nearest"))
thk[hill] = 0.0
th_in = np.array([h["T_3x3"] for h in holes if h["T_3x3"] is not None and np.isfinite(h["T_3x3"])])
tk_in = np.array([h["soft_thickness_m"] for h in holes if h["T_3x3"] is not None and np.isfinite(h["T_3x3"])])
from scipy.stats import spearmanr
res = dict(boreholes=holes, rho_boreholes_thickness_T=float(spearmanr(tk_in, th_in)[0]), n_boreholes_in_grid=len(th_in),
           map_test=C.driver_test("lo2022_soft_thickness_m", thk, +1),
           strain_pct_per_yr_median=float(np.nanmedian((C.T / np.maximum(thk, 5) / 10)[C.LAND & (thk > 20)])))
C.save("L3", res, dict(lo2022_soft_thickness=thk), dict(lo2022_soft_thickness="soil"))
