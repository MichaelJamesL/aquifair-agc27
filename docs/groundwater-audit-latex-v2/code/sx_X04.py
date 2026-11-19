"""X04: linear embankments (toll road, main roads, rail, runway, dikes) -> extra sinking on the line vs a
400-1000 m ring around it (sx_prereg.md)."""
import numpy as np
import sx_common as C
import sx_osm as O

TYPES = {"motorway_trunk": 'way[highway~"^(motorway|trunk|motorway_link|trunk_link)$"];',
         "primary": 'way[highway~"^(primary|primary_link)$"];',
         "rail": 'way[railway=rail];',
         "runway": 'way[aeroway=runway];',
         "dike_embankment": 'way[man_made~"^(dyke|embankment|breakwater|groyne)$"];way[embankment=yes];way[barrier=retaining_wall];'}
els = O.query("lines", "".join(TYPES.values()))


def match(e, t):
    g = e.get("tags", {})
    return {"motorway_trunk": g.get("highway", "").split("_")[0] in ("motorway", "trunk"),
            "primary": g.get("highway", "").startswith("primary"), "rail": g.get("railway") == "rail",
            "runway": g.get("aeroway") == "runway",
            "dike_embankment": g.get("man_made") in ("dyke", "embankment", "breakwater", "groyne")
            or g.get("embankment") == "yes" or g.get("barrier") == "retaining_wall"}[t]


masks = {t: O.rasterize([e for e in els if match(e, t)]) for t in TYPES}
ALL = np.any(list(masks.values()), 0)


def contrast(M):
    d = O.dist(M)
    on, ring = C.LAND & (d <= 200), C.LAND & (d >= 400) & (d <= 1000)
    return C.T[on].mean() - C.T[ring].mean() if on.sum() >= 5 and ring.sum() >= 5 else np.nan


obs = contrast(ALL)
p, nul = C.shift_p(contrast, ALL, obs)
per = {}
for t, M in masks.items():
    o = contrast(M)
    per[t] = dict(cells=int(M.sum()), contrast=o, p_shift=C.shift_p(contrast, M, o, 499)[0] if np.isfinite(o) else None)
res = dict(n_ways=len(els), line_cells=int(ALL.sum()), contrast_mm_yr=obs, p_shift=p, null=nul,
           PASS=bool(obs >= 5 and p < 0.05), per_type=per)
C.save("X04", res, dict(dist_embankment=np.minimum(O.dist(ALL), 5000)), dict(dist_embankment="load"))
