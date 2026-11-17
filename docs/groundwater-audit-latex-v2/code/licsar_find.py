"""Find LiCSAR frames whose footprint polygon contains a lon/lat point.

Usage: python licsar_find.py LON LAT [LON LAT ...]
Scans all track directories on JASMIN, reads each frame's -poly.txt (small), prints matches
with the number of interferograms available. Cached listing in realdata/licsar_polys.json.
"""
import sys, re, json, os, urllib.request
from concurrent.futures import ThreadPoolExecutor
from matplotlib.path import Path

BASE = "https://gws-access.jasmin.ac.uk/public/nceo_geohazards/LiCSAR_products"
CACHE = "C:/Kuliah/hackathon/agc-26/realdata/licsar_polys.json"
pts = [(float(a), float(b)) for a, b in zip(sys.argv[1::2], sys.argv[2::2])]


def get(url):
    try:
        return urllib.request.urlopen(url, timeout=60).read().decode("utf-8", "replace")
    except Exception:
        return ""


if os.path.exists(CACHE):
    polys = json.load(open(CACHE))
else:
    with ThreadPoolExecutor(16) as ex:
        lists = list(ex.map(lambda t: (t, get(f"{BASE}/{t}/")), range(1, 176)))
    frames = [(t, f) for t, h in lists for f in sorted(set(re.findall(r'href="(\d{3}[AD]_\d{5}_\d{6})/"', h)))]
    print(len(frames), "frames", flush=True)

    def poly(tf):
        t, f = tf
        txt = get(f"{BASE}/{t}/{f}/metadata/{f}-poly.txt")
        xy = [tuple(map(float, l.split()[:2])) for l in txt.splitlines() if re.match(r"^\s*-?\d", l)]
        return f, t, xy

    with ThreadPoolExecutor(24) as ex:
        polys = {f: dict(track=t, poly=xy) for f, t, xy in ex.map(poly, frames) if xy}
    json.dump(polys, open(CACHE, "w"))
for lon, lat in pts:
    for f, d in polys.items():
        if len(d["poly"]) >= 3 and Path(d["poly"]).contains_point((lon, lat)):
            n = len(re.findall(r'href="\d{8}_\d{8}/"', get(f"{BASE}/{d['track']}/{f}/interferograms/")))
            print(f"{lon},{lat}: {f} track {d['track']} ifgs {n}", flush=True)
