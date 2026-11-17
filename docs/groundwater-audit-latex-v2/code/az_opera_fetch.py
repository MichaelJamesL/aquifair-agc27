"""Remote-subset OPERA DISP-S1 granules (frame F07091) to the central-Arizona box.

Run in WSL env `alos`:  python az_opera_fetch.py inspect | fetch
Auth: earthaccess netrc strategy (never reads the file itself here).
Reads only the needed HDF5 chunks with HTTP range requests (block cache), crops to the box in
the frame's UTM grid and stores per-granule arrays in realdata/arizona/opera/<sec>_<ref>.npz.
"""
import sys, os, json, io, time
import numpy as np
import h5py
import earthaccess
from pyproj import Transformer

ROOT = "/mnt/c/Kuliah/hackathon/agc-26/realdata/arizona"
OUT = f"{ROOT}/opera"
os.makedirs(OUT, exist_ok=True)
FR = json.load(open(f"{ROOT}/opera_search.json"))["F07091"]
LON0, LAT0, LON1, LAT1 = -112.1, 32.6, -111.2, 33.45
# 200 m output grid in EPSG 32612 (frame CRS) covering the box crop (x 396795-481395, y 3606975-3701715)
E0, N0, PIX, NX, NY = 396800.0, 3606800.0, 200.0, 423, 475
earthaccess.login(strategy="netrc")
S = earthaccess.get_requests_https_session()


class RangeFile(io.RawIOBase):
    """Seekable read-only file over HTTP range requests with a block cache."""

    def __init__(s, url, block=4 << 20):
        r = S.get(url, headers={"Range": "bytes=0-0"}, timeout=120, allow_redirects=True)
        s.url = r.url                                   # signed CDN URL after the login redirect
        s.size = int(r.headers["Content-Range"].split("/")[1])
        s.pos, s.block, s.cache, s.nbytes = 0, block, {}, 0

    def readable(s): return True
    def seekable(s): return True
    def tell(s): return s.pos

    def seek(s, off, whence=0):
        s.pos = off if whence == 0 else (s.pos + off if whence == 1 else s.size + off)
        return s.pos

    def _blk(s, i):
        if i not in s.cache:
            a = i * s.block
            b = min(a + s.block, s.size) - 1
            for k in range(5):
                try:
                    r = S.get(s.url, headers={"Range": f"bytes={a}-{b}"}, timeout=180)
                    r.raise_for_status()
                    break
                except Exception:
                    time.sleep(3 * (k + 1))
            s.cache[i] = r.content
            s.nbytes += len(r.content)
            if len(s.cache) > 64:                           # bound memory (~256 MB)
                s.cache.pop(next(iter(s.cache)))
        return s.cache[i]

    def readinto(s, buf):
        n = min(len(buf), s.size - s.pos)
        if n <= 0:
            return 0
        out, p = bytearray(), s.pos
        while len(out) < n:
            i = p // s.block
            d = s._blk(i)
            o = p - i * s.block
            take = d[o:o + n - len(out)]
            out += take
            p += len(take)
        buf[:n] = out
        s.pos += n
        return n


def crop_index(h):
    x, y = h["x"][()], h["y"][()]
    wkt = h["spatial_ref"].attrs.get("crs_wkt")
    wkt = wkt.decode() if isinstance(wkt, bytes) else str(wkt)
    import re
    z, hemi = re.search(r"UTM zone (\d+)([NS])", wkt).groups()
    epsg = (32600 if hemi == "N" else 32700) + int(z)
    t = Transformer.from_crs(4326, epsg, always_xy=True)
    xs, ys = t.transform([LON0, LON1, LON0, LON1], [LAT0, LAT0, LAT1, LAT1])
    ix = np.flatnonzero((x >= min(xs)) & (x <= max(xs)))
    iy = np.flatnonzero((y >= min(ys)) & (y <= max(ys)))
    return slice(ix[0], ix[-1] + 1), slice(iy[0], iy[-1] + 1), x, y, epsg


if sys.argv[1] == "inspect":
    f = RangeFile(FR[0]["url"])
    h = h5py.File(f, "r")
    h.visititems(lambda n, o: print(n, o.shape, o.dtype, o.chunks, o.compression) if isinstance(o, h5py.Dataset) and o.ndim >= 1 and o.size > 1 else None)
    sx, sy, x, y, epsg = crop_index(h)
    print("epsg", epsg, "x", x[0], x[-1], x[1] - x[0], "y", y[0], y[-1], "crop", sx, sy)
    for k in ("displacement",):
        print(k, {a: (v.decode() if isinstance(v, bytes) else v) for a, v in h[k].attrs.items() if a not in ("DIMENSION_LIST",)})
    for k in h["identification"]:
        v = h["identification"][k][()]
        print("id", k, v.decode() if isinstance(v, bytes) else v)
    print("bytes read", f.nbytes)

elif sys.argv[1] == "fetch":
    names = [n.strip() for n in sys.argv[2:] if n.strip()] or None   # strip: lists written on Windows carry \r
    todo = [g for g in FR if names is None or g["name"] in names]
    for g in todo:
        fn = f"{OUT}/{g['sec'][:8]}_{g['ref'][:8]}.npz"
        if os.path.exists(fn):
            continue
        t0 = time.time()
        f = RangeFile(g["url"])
        h = h5py.File(f, "r")
        sx, sy, x, y, epsg = crop_index(h)
        disp = h["displacement"][sy, sx]
        good = (h["recommended_mask"][sy, sx] == 1) & (h["water_mask"][sy, sx] == 1) & np.isfinite(disp)
        tc = h["temporal_coherence"][sy, sx]
        # bin 30 m pixels onto the 200 m output grid (good pixels only)
        X, Y = np.meshgrid(x[sx], y[sy])
        ix = ((X - E0) // PIX).astype(int)
        iy = ((Y - N0) // PIX).astype(int)
        ok = good & (ix >= 0) & (ix < NX) & (iy >= 0) & (iy < NY)
        lin = iy[ok] * NX + ix[ok]
        cnt = np.bincount(lin, minlength=NX * NY)
        s1 = np.bincount(lin, disp[ok], minlength=NX * NY)
        s2 = np.bincount(lin, disp[ok] ** 2, minlength=NX * NY)
        stc = np.bincount(lin, tc[ok], minlength=NX * NY)
        np.savez_compressed(fn, cnt=cnt.reshape(NY, NX).astype(np.int16),
                            mean=(s1 / np.maximum(cnt, 1)).reshape(NY, NX).astype(np.float32),
                            sd=np.sqrt(np.maximum(s2 / np.maximum(cnt, 1) - (s1 / np.maximum(cnt, 1)) ** 2, 0)).reshape(NY, NX).astype(np.float32),
                            tcoh=(stc / np.maximum(cnt, 1)).reshape(NY, NX).astype(np.float32),
                            epsg=epsg, ref=g["ref"], sec=g["sec"], name=g["name"], E0=E0, N0=N0, PIX=PIX)
        print(g["sec"][:8], g["ref"][:8], f"{f.nbytes / 1e6:.0f} MB read, {time.time() - t0:.0f} s", flush=True)
