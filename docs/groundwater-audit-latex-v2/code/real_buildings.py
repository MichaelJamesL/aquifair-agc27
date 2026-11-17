"""Building footprint fraction per 200 m model cell from Microsoft Global ML Building Footprints.

Usage: python real_buildings.py OUT.npz TILE.csv.gz [TILE.csv.gz ...]
Streams GeoJSON lines; keeps buildings whose first vertex is inside the model box (+pad).
Output: frac (NY, NX) = footprint area / cell area, count (NY, NX).
"""
import sys, gzip, json
import numpy as np
from pyproj import Transformer
import synth as S
import real_lib as R

grid = R.Grid(428000.0, 9220000.0, 32749)
lo0, la0, lo1, la1 = grid.lonlat_bounds(0)
area = np.zeros(S.NY * S.NX)
cnt = np.zeros(S.NY * S.NX)
n = 0
for path in sys.argv[2:]:
    with gzip.open(path, "rt") as f:
        for line in f:
            j = line.find("[[[")
            if j < 0:
                continue
            lon, lat = map(float, line[j + 3:line.find("]", j)].split(",")[:2])
            if not (lo0 < lon < lo1 and la0 < lat < la1):
                continue
            ring = np.array(json.loads(line)["geometry"]["coordinates"][0])
            E, N = grid.fw.transform(ring[:, 0], ring[:, 1])
            a = 0.5 * abs(np.dot(E, np.roll(N, 1)) - np.dot(N, np.roll(E, 1)))
            ix = int((E.mean() - grid.E0) // S.PIX)
            iy = int((N.mean() - grid.N0) // S.PIX)
            if 0 <= ix < S.NX and 0 <= iy < S.NY:
                area[iy * S.NX + ix] += a
                cnt[iy * S.NX + ix] += 1
                n += 1
    print(path, "buildings kept so far", n, flush=True)
np.savez_compressed(sys.argv[1], frac=(area / S.PIX ** 2).reshape(S.NY, S.NX), count=cnt.reshape(S.NY, S.NX))
print("saved", n)
