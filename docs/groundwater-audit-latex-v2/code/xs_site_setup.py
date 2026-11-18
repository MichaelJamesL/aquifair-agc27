"""(DGX Spark) Fill in frame, UTM grid and static layers for a confirmation region (xsite_prereg.md
addendum 5) after az_opera_search.py. Picks the frame covering most of the box, selects granules for
2016-10..2020-12 (every ministack link + about one date per 2 months), downloads the static layers and
writes <root>/site.json + opera_selected.txt. Usage: SITE=r3_east DATA_ROOT=~/xs_data python xs_site_setup.py
"""
import datetime as dt, glob, json, math, os, re
import earthaccess
import rasterio
from pyproj import Transformer
from opera_site import SITE, WIN_ROOT as ROOT

d8 = lambda s: dt.datetime.strptime(s[:8], "%Y%m%d")
FRS = json.load(open(f"{ROOT}/opera_search.json"))
ok = {k: v for k, v in FRS.items() if min(g["sec"][:8] for g in v) <= "20161031" and max(g["sec"][:8] for g in v) >= "20201101"}
frame = max(ok, key=lambda k: (round(ok[k][0]["cover"], 2), len(ok[k])))
G = [g for g in FRS[frame] if g["url"] and "20160901" <= g["sec"][:8] <= "20201231" and g["ref"][:8] <= "20201231"]
refs = sorted({g["ref"][:8] for g in G})
sel = []
for r in refs:
    last = None
    for g in sorted((g for g in G if g["ref"][:8] == r), key=lambda g: g["sec"]):
        s = g["sec"][:8]
        if s in refs or last is None or (d8(s) - d8(last)).days >= 55:
            sel.append(g["name"]); last = s
open(f"{ROOT}/opera_selected.txt", "w").write("\n".join(sel) + "\n")

earthaccess.login(strategy="netrc")
os.makedirs(f"{ROOT}/opera_static", exist_ok=True)
st = earthaccess.search_data(short_name="OPERA_L3_DISP-S1-STATIC_V1", granule_name=f"*{frame}*")
links = [l for g in st for l in g.data_links() if l.endswith(("_dem.tif", "_line_of_sight_enu.tif"))]
earthaccess.download(links, f"{ROOT}/opera_static")
dem = sorted(glob.glob(f"{ROOT}/opera_static/*{frame}*_dem.tif"))[0]
static_date = re.search(rf"{frame}_(\d{{8}})_", dem).group(1)
with rasterio.open(dem) as s:                              # static layers are on the frame's UTM grid
    epsg = s.crs.to_epsg()

lo0, la0, lo1, la1 = SITE["box"]
xs, ys = Transformer.from_crs(4326, epsg, always_xy=True).transform([lo0, lo1, lo0, lo1], [la0, la0, la1, la1])
E0, N0 = math.floor(min(xs) / 200) * 200.0, math.floor(min(ys) / 200) * 200.0
grid = [E0, N0, 200.0, math.ceil((max(xs) - E0) / 200), math.ceil((max(ys) - N0) / 200)]
for f in glob.glob(f"{ROOT}/opera_static/*{frame}*.tif"):     # az_opera_rate.py expects the S1A_v1.0 name
    want = re.sub(r"_(\d{8})_S1[ABC]_v[\d.]+_", rf"_\1_S1A_v1.0_", f)
    if want != f and not os.path.exists(want):
        os.symlink(f, want)
cfg = dict(frame=frame, epsg=epsg, grid=grid, static_date=static_date)
json.dump(cfg, open(f"{ROOT}/site.json", "w"))
print(SITE["root"], cfg, "cover", round(FRS[frame][0]["cover"], 2), "granules", len(sel), "refs", len(refs))
