"""OpenStreetMap features over the Semarang grid via the Overpass API (cached in $SX_DATA/osm_<tag>.json)."""
import json
import os
import time
import urllib.parse
import urllib.request
import numpy as np
from scipy import ndimage
import sx_common as C

API = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]


def query(tag, body):
    fn = f"{C.DATA}/osm_{tag}.json"
    if not os.path.exists(fn):
        lo0, la0, lo1, la1 = C.bbox_ll(1000)
        q = f"[out:json][timeout:300][bbox:{la0},{lo0},{la1},{lo1}];({body});out geom;"
        for k in range(6):
            try:
                req = urllib.request.Request(API[k % 2], data=urllib.parse.urlencode({"data": q}).encode(),
                                             headers={"User-Agent": "research-script"})
                json.dump(json.load(urllib.request.urlopen(req, timeout=400)), open(fn, "w"))
                break
            except Exception as e:
                print("overpass retry", k, str(e)[:80], flush=True)
                time.sleep(30)
    return json.load(open(fn))["elements"]


def coords(e):
    if "geometry" in e:
        return [np.array([[p["lon"], p["lat"]] for p in e["geometry"]])]
    if "members" in e:
        return [np.array([[p["lon"], p["lat"]] for p in m["geometry"]]) for m in e["members"] if "geometry" in m]
    if "lat" in e:
        return [np.array([[e["lon"], e["lat"]]])]
    return []


def rasterize(els, step=40.0):
    """Mark every grid cell touched by the features' lines / points (densified every `step` m)."""
    M = np.zeros((C.NY, C.NX), bool)
    for e in els:
        for ll in coords(e):
            E, N = C.FW.transform(ll[:, 0], ll[:, 1])
            pts = [np.c_[E, N][:1]]
            for a, b in zip(np.c_[E, N][:-1], np.c_[E, N][1:]):
                n = max(int(np.hypot(*(b - a)) // step), 1)
                pts.append(a + (b - a) * np.linspace(0, 1, n + 1)[:, None])
            P = np.vstack(pts)
            iy, ix = C.en_to_cell(P[:, 0], P[:, 1])
            M[iy, ix] = True
    return M


def dist(M):
    return ndimage.distance_transform_edt(~M) * C.PIX if M.any() else np.full(M.shape, np.inf)
