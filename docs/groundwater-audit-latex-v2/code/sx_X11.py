"""X11: large water users (industry, factories, hotels, malls, hospitals, universities, water parks; OpenStreetMap)
-> is the ground within 500 m sinking faster than matched land? (sx_prereg.md)"""
import numpy as np
import sx_common as C
import sx_osm as O

CATS = {"industrial": 'nwr[landuse=industrial];', "works_factory": 'nwr[man_made=works];nwr[building~"^(industrial|factory)$"];',
        "hotel": 'nwr[tourism=hotel];', "mall": 'nwr[shop=mall];', "hospital": 'nwr[amenity=hospital];',
        "university": 'nwr[amenity=university];', "water_park": 'nwr[leisure=water_park];'}
els = O.query("users", "".join(CATS.values()))


def cat(e):
    g = e.get("tags", {})
    return ("industrial" if g.get("landuse") == "industrial" else
            "works_factory" if g.get("man_made") == "works" or g.get("building") in ("industrial", "factory") else
            "hotel" if g.get("tourism") == "hotel" else "mall" if g.get("shop") == "mall" else
            "hospital" if g.get("amenity") == "hospital" else "university" if g.get("amenity") == "university" else
            "water_park" if g.get("leisure") == "water_park" else None)


masks = {k: O.rasterize([e for e in els if cat(e) == k]) for k in CATS}
ALL = np.any(list(masks.values()), 0) | C.B["osm_industrial"].astype(bool)
near = lambda M: O.dist(M) <= 500


def stat(M):
    s = C.LAND & near(M)
    return C.T[s].mean() if s.sum() >= 5 else np.nan


sel = C.LAND & near(ALL)
obs, pm, nm = C.matched_p(sel)
ps, ns = C.shift_p(stat, ALL, stat(ALL))
per = {}
for k, M in masks.items():
    s = C.LAND & near(M)
    if s.sum() >= 5:
        o, p, n = C.matched_p(s, 3000)
        per[k] = dict(features=int(sum(cat(e) == k for e in els)), cells=int(s.sum()), mean_T=o, matched_mean=n, p_matched=p)
res = dict(n_features=len(els), cells_near=int(sel.sum()), mean_T_near=obs, matched_null_mean=nm, p_matched=pm,
           p_shift=ps, shift_null=ns, PASS=bool(pm < 0.05 and ps < 0.05 and obs > nm), per_category=per)
C.save("X11", res, dict(dist_big_user=np.minimum(O.dist(ALL), 5000)), dict(dist_big_user="pumping"))
