"""Truth test restricted to where truth exists: only cells within 3 km of a PANGAEA well or OSM
industrial polygon count, for both the sources and the random nulls (fair to sources in
under-surveyed Demak villages).

Usage: python real_truth_domain.py SOURCES.json [FIT_LABEL]
"""
import sys, json
import numpy as np
from scipy import ndimage
import real_lib as R
import synth as S

SD = "C:/Kuliah/hackathon/agc-26/realdata/semarang/"
g = R.Grid(428000.0, 9220000.0, 32749)
label = sys.argv[2] if len(sys.argv) > 2 else "cv"
src = np.array(json.load(open(sys.argv[1]))["fits"][label]["sources"]).reshape(-1, 3)
rms = [R.rate_map(SD + tr, gacos=True, min_dt=24) for tr in ("t076", "t127")]
H = R.grid_hgt(rms[0], g)
D, m, _ = R.combine_tracks(rms, g, H)
wells, _ = R.pangaea_wells(SD + "pangaea.tab", g)
ind, _ = R.osm_layers(SD + "osm.json", g)
truth = ind.copy()
ij = (wells // S.PIX).astype(int)
truth[ij[:, 1], ij[:, 0]] = True
dom = m & (ndimage.distance_transform_edt(~truth) * S.PIX <= 3000)
ins = dom[(src[:, 1] // S.PIX).astype(int), (src[:, 0] // S.PIX).astype(int)]
print(f"domain = {dom.sum() / m.sum():.0%} of coherent cells; sources inside {ins.sum()} of {len(src)}")
rng = np.random.default_rng(11)
s = src[ins]
Dn = np.nan_to_num(D)
for name, fn, tol in (("wells 1 km", lambda p: R.dist_to_points(p, wells), 1000),
                      ("industrial 500 m", lambda p: R.dist_to_raster(p, ind), 500),
                      ("either 1 km", lambda p: np.minimum(R.dist_to_points(p, wells), R.dist_to_raster(p, ind)), 1000)):
    print(name, R.location_test(s, dom, Dn, fn, tol, rng))
