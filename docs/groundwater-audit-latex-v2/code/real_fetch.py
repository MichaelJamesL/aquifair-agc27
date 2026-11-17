"""Fetch a clipped stack of LiCSAR interferograms (unw + coherence) by remote windowed reads.

Usage: python real_fetch.py OUTDIR FRAME LON0 LAT0 LON1 LAT1 START END [MAXDAYS]
Writes OUTDIR/stack.npz with unw (rad), cc (0-255), pair dates, and the lon/lat grid.
"""
import sys, os, json
from datetime import date
from concurrent.futures import ThreadPoolExecutor
import urllib.request
import numpy as np
import rasterio
from rasterio.windows import from_bounds

out, frame = sys.argv[1], sys.argv[2]
lon0, lat0, lon1, lat1 = map(float, sys.argv[3:7])
start, end = sys.argv[7], sys.argv[8]
maxdays = int(sys.argv[9]) if len(sys.argv) > 9 else 48
track = int(frame[:3])
JAS = f"https://gws-access.jasmin.ac.uk/public/nceo_geohazards/LiCSAR_products/{track}/{frame}"
CEDA = f"/vsicurl/https://data.ceda.ac.uk/neodc/comet/data/licsar_products/{track}/{frame}"
ENV = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
           GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="3")
os.makedirs(out, exist_ok=True)
d = lambda s: date(int(s[:4]), int(s[4:6]), int(s[6:]))

html = urllib.request.urlopen(JAS + "/interferograms/", timeout=120).read().decode()
import re
pairs = sorted(set(re.findall(r'href="(\d{8}_\d{8})"', html)))
pairs = [p for p in pairs if start <= p[:8] and p[9:] <= end and (d(p[9:]) - d(p[:8])).days <= maxdays]
print(len(pairs), "pairs", flush=True)


def read(url):
    with rasterio.Env(**ENV), rasterio.open(url) as s:
        w = from_bounds(lon0, lat0, lon1, lat1, s.transform).round_offsets().round_lengths()
        return s.read(1, window=w), s.window_transform(w)


def get(p):
    try:
        # each pair entry is a small link file; files live on CEDA or JASMIN depending on the pair
        stub = urllib.request.urlopen(f"{JAS}/interferograms/{p}", timeout=120).read().decode()
        url = {k: "/vsicurl/" + re.search(rf"href='([^']*\.geo\.{k}\.tif)'", stub).group(1) for k in ("unw", "cc")}
        u, tr = read(url["unw"])
        c, _ = read(url["cc"])
        return p, u.astype(np.float32), c, tr
    except Exception as e:  # missing files happen; skip the pair
        print("skip", p, str(e)[:80], flush=True)
        return p, None, None, None


if os.path.exists(f"{out}/stack.npz"):
    pairs = list(np.load(f"{out}/stack.npz")["pairs"])
    print("stack exists; fetching GACOS + look vectors only", flush=True)
res = []
with ThreadPoolExecutor(int(os.environ.get("NTHREADS", 16))) as ex:
    for k, r in enumerate(ex.map(get, [] if os.path.exists(f"{out}/stack.npz") else pairs)):
        if r[1] is not None:
            res.append(r)
        if k % 25 == 0:
            print(k, flush=True)
if res:
    shape = res[0][1].shape
    res = [r for r in res if r[1].shape == shape and r[2].shape == shape]
    tr = res[0][3]
    meta = {}
    for name in ("U", "hgt", "landmask"):
        a, _ = read(f"/vsicurl/{JAS}/metadata/{frame}.geo.{name}.tif")
        meta[name] = a[:shape[0], :shape[1]]
    np.savez_compressed(f"{out}/stack.npz", pairs=np.array([r[0] for r in res]),
                        unw=np.stack([r[1] for r in res]), cc=np.stack([r[2] for r in res]),
                        transform=np.array(tr)[:6], **meta)
    print("saved", len(res), shape, flush=True)
    pairs = [r[0] for r in res]
shape = np.load(f"{out}/stack.npz")["unw"].shape[1:]


def get_epoch(e):
    """GACOS slant delay (rad) for one acquisition date; None if LiCSAR has none."""
    try:
        stub = urllib.request.urlopen(f"{JAS}/epochs/{e}", timeout=120).read().decode()
        m = re.search(r"href='([^']*/\d{8}\.sltd\.geo\.tif)'", stub)
        return e, (read("/vsicurl/" + m.group(1))[0].astype(np.float32) if m else None)
    except Exception as ex:
        print("skip epoch", e, str(ex)[:80], flush=True)
        return e, None


epochs = sorted({d for p in pairs for d in p.split("_")})
with ThreadPoolExecutor(int(os.environ.get("NTHREADS", 16))) as ex:
    got = [(e, a) for e, a in ex.map(get_epoch, epochs) if a is not None and a.shape == tuple(shape)]
look = {n: read(f"/vsicurl/{JAS}/metadata/{frame}.geo.{n}.tif")[0][:shape[0], :shape[1]] for n in ("E", "N", "U")}
np.savez_compressed(f"{out}/gacos.npz", epochs=np.array([e for e, _ in got]),
                    sltd=np.stack([a for _, a in got]), **look)
print("gacos epochs", len(got), "of", len(epochs))
