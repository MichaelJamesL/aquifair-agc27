"""(WSL or Spark, alos env) Pack ISCE stripmapStack outputs into one npz for the Windows analysis:
unwrapped phase + coherence per pair (multilooked radar grid), and lat/lon/height/incidence
multilooked to the same grid. Writes realdata/semarang/alos/stack_alos.npz."""
import glob, os
import numpy as np
from osgeo import gdal

W = os.path.expanduser("~/alos_work")
OUT = os.path.expanduser("~/alos_work/stack_alos.npz")  # Spark: copied back to realdata/semarang/alos/


def rd(path, band=1):
    ds = gdal.Open(path if os.path.exists(path) else path + ".vrt")
    return ds.GetRasterBand(band).ReadAsArray()


pairs, unw, coh = [], [], []
for d in sorted(glob.glob(f"{W}/Igrams/*_*")):
    p = os.path.basename(d)
    fu = glob.glob(f"{d}/filt_{p}.unw") or glob.glob(f"{d}/*.unw")
    fc = glob.glob(f"{d}/filt_{p}.cor") or glob.glob(f"{d}/*.cor")
    if not fu or not fc:
        print("missing", p); continue
    unw.append(rd(fu[0], 2).astype(np.float32))       # band 2 = unwrapped phase (rad)
    coh.append(rd(fc[0], 1).astype(np.float32))
    pairs.append(p)
shape = unw[0].shape
geo = {}
for k, f in (("lat", "lat.rdr"), ("lon", "lon.rdr"), ("hgt", "hgt.rdr"), ("inc", "los.rdr")):
    a = rd(f"{W}/geom_reference/{f}").astype(np.float64)   # already multilooked 32 az x 14 rg by topo (same as igrams); .full vrts are stale
    fy, fx = a.shape[0] // shape[0], a.shape[1] // shape[1]       # looks used for the igrams
    a = a[:shape[0] * fy, :shape[1] * fx].reshape(shape[0], fy, shape[1], fx).mean((1, 3))
    geo[k] = a.astype(np.float32)
np.savez_compressed(OUT, pairs=np.array(pairs), unw=np.array(unw), coh=np.array(coh), **geo)
print(len(pairs), "pairs", shape, "->", OUT)
