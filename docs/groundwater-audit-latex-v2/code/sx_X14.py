"""X14: GNSS check. Nevada Geodetic Laboratory MIDAS velocities for stations inside / near the grid vs the InSAR
vertical rate at the station (sx_prereg.md, descriptive)."""
import urllib.request
import numpy as np
import sx_common as C

rows = []
for ref in ("IGS14", "IGS20"):
    try:
        txt = urllib.request.urlopen(f"https://geodesy.unr.edu/velocities/midas.{ref}.txt", timeout=300).read().decode()
        rows = [l.split() for l in txt.splitlines() if l.strip()]
        break
    except Exception as e:
        print("midas miss", ref, str(e)[:80], flush=True)
lo0, la0, lo1, la1 = C.bbox_ll(110000)                  # stations within ~1 degree
st = []
for r in rows:
    lat, lon = float(r[24]), float(r[25])
    lon = lon - 360 if lon > 180 else lon
    if lo0 < lon < lo1 and la0 < lat < la1:
        iy, ix = C.ll_to_cell([lon], [lat])
        ins = len(iy) == 1
        T3 = float(np.nanmean(C.T[max(iy[0] - 1, 0):iy[0] + 2, max(ix[0] - 1, 0):ix[0] + 2])) if ins else None
        st.append(dict(station=r[0], start=float(r[2]), end=float(r[3]), lon=lon, lat=lat, vu_mm_yr=float(r[10]) * 1000,
                       sd_vu=float(r[13]) * 1000, ve_mm_yr=float(r[8]) * 1000, inside_grid=ins,
                       insar_sinking_3x3=T3))
res = dict(n_stations=len(st), n_listed=len(rows), ref=ref, stations=st,
           note="GNSS vu is + up; InSAR sinking is + down and relative to high ground in the south")
C.save("X14", res)
