"""Find OPERA DISP-S1 granules over central Arizona; frame coverage of the box and date ranges.

Run in WSL env `alos`. Writes realdata/arizona/opera_search.json (frame -> granules).
"""
import json, collections
import earthaccess
from shapely.geometry import Polygon, box

BOX = box(-112.1, 32.6, -111.2, 33.45)
OUT = "/mnt/c/Kuliah/hackathon/agc-26/realdata/arizona/opera_search.json"
res = earthaccess.search_data(short_name="OPERA_L3_DISP-S1_V1", bounding_box=(-112.1, 32.6, -111.2, 33.45), count=5000)
fr = collections.defaultdict(list)
for g in res:
    u = g["umm"]
    name = u["GranuleUR"]
    pts = u["SpatialExtent"]["HorizontalSpatialDomain"]["Geometry"]["GPolygons"][0]["Boundary"]["Points"]
    poly = Polygon([(p["Longitude"], p["Latitude"]) for p in pts])
    nc = [l for l in g.data_links() if l.endswith(".nc")]
    fr[name.split("_")[4]].append(dict(name=name, ref=name.split("_")[6], sec=name.split("_")[7],
                                       url=nc[0] if nc else None, cover=poly.intersection(BOX).area / BOX.area))
for k, v in sorted(fr.items(), key=lambda kv: -len(kv[1])):
    v.sort(key=lambda x: x["sec"])
    refs = sorted(set(x["ref"] for x in v))
    print(k, len(v), f"cover {v[0]['cover']:.2f}", v[0]["sec"][:8], "->", v[-1]["sec"][:8], "refs", len(refs))
json.dump(fr, open(OUT, "w"))
