"""Find OPERA DISP-S1 granules over the site box (opera_site.py, env SITE); frame coverage of the box and date ranges.

Run in WSL env `alos`. Writes realdata/arizona/opera_search.json (frame -> granules).
"""
import json, collections
import earthaccess
from shapely.geometry import Polygon, box

from opera_site import SITE, WSL_ROOT

BOX = box(*SITE["box"])
OUT = f"{WSL_ROOT}/opera_search.json"
res = earthaccess.search_data(short_name="OPERA_L3_DISP-S1_V1", bounding_box=SITE["box"], count=5000)
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
