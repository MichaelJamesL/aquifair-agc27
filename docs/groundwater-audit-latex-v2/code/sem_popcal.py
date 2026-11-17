"""Calibrate people per m2 of building footprint from census population and Microsoft building
footprints summed inside each district (Kota Semarang, Demak). Output: exp/sem_areas/popcal.json."""
import gzip, json, glob
import numpy as np
from matplotlib.path import Path

ROOT = "C:/Kuliah/hackathon/agc-26/realdata"
POP = {"Kota Semarang": 1_694_740, "Demak": 1_203_956}       # BPS 2023 estimate; Census 2020
adm = json.load(open(f"{ROOT}/semarang/admin/idn_adm2.geojson"))
paths = {}
for f in adm["features"]:
    n = f["properties"]["shapeName"]
    if n in POP:
        g = f["geometry"]
        paths[n] = [Path(np.array(p[0])) for p in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]])]
bbox = {n: (min(p.vertices[:, 0].min() for p in ps), min(p.vertices[:, 1].min() for p in ps),
            max(p.vertices[:, 0].max() for p in ps), max(p.vertices[:, 1].max() for p in ps)) for n, ps in paths.items()}
area = {n: 0.0 for n in POP}
count = {n: 0 for n in POP}
buf = []


def flush():
    if not buf:
        return
    a = np.array(buf)
    for n, ps in paths.items():
        x0, y0, x1, y1 = bbox[n]
        sel = (a[:, 0] > x0) & (a[:, 0] < x1) & (a[:, 1] > y0) & (a[:, 1] < y1)
        if not sel.any():
            continue
        ins = np.zeros(sel.sum(), bool)
        for p in ps:
            ins |= p.contains_points(a[sel, :2])
        area[n] += a[sel][ins, 2].sum()
        count[n] += int(ins.sum())
    buf.clear()


for fn in sorted(glob.glob(f"{ROOT}/msbuild/31001*.csv.gz")):
    with gzip.open(fn, "rt") as fh:
        for line in fh:
            j = line.find("[[[")
            if j < 0:
                continue
            ring = np.array(json.loads(line[j + 1:line.find("]]", j) + 2]))     # outer ring "[[x,y],...]"
            lon0, lat0 = ring[:, 0].mean(), ring[:, 1].mean()
            if not (110.2 < lon0 < 110.9 and -7.2 < lat0 < -6.65):
                continue
            x = (ring[:, 0] - lon0) * 111320 * np.cos(np.radians(lat0))
            y = (ring[:, 1] - lat0) * 110540
            buf.append((lon0, lat0, 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))))
            if len(buf) >= 200000:
                flush()
    flush()
    print(fn[-20:], {n: round(area[n] / 1e6, 1) for n in POP}, flush=True)
out = {n: dict(population=POP[n], footprint_km2=round(area[n] / 1e6, 2), buildings=count[n],
               m2_footprint_per_person=round(area[n] / POP[n], 1)) for n in POP}
json.dump(out, open(f"{ROOT}/semarang/exp/sem_areas/popcal.json", "w"), indent=1)
print(json.dumps(out, indent=1))
