"""Per-site settings for the OPERA DISP-S1 scripts (az_opera_search/fetch/rate.py).
Pick with env var SITE (default arizona). Grid = 200 m cells in the frame's UTM CRS."""
import os

SITES = {
    "arizona": dict(root="arizona", box=(-112.1, 32.6, -111.2, 33.45), frame="F07091", epsg=32612,
                    grid=(396800.0, 3606800.0, 200.0, 423, 475), static_date="20140403", track=27, direction="Descending"),
    # Houston-Galveston / Fort Bend / Montgomery subsidence districts (GULF model truth)
    "houston": dict(root="houston", box=(-96.0, 29.35, -94.9, 30.45), frame="F08882", epsg=32615,
                    grid=(208600.0, 3248200.0, 200.0, 545, 622), static_date="20140403", track=34, direction="Ascending"),
    # Texas GULF-model area west of the Houston box (confirmatory region R2, xsite_prereg.md addendum 3)
    "texas_w": dict(root="texas_w", box=(-97.0, 28.75, -96.0, 29.75), frame="F08882", epsg=32615,
                    grid=(109200.0, 3183800.0, 200.0, 497, 570), static_date="20140403", track=34, direction="Ascending"),
    # Semarang: not an OPERA site (LiCSAR); listed so az_et.py can use the same 24 x 16 km model grid
    "semarang": dict(root="semarang", box=(110.33, -7.07, 110.6, -6.9), frame=None, epsg=32749,
                     grid=(428000.0, 9220000.0, 200.0, 120, 80), static_date=None, track=None, direction=None),
}
# Confirmation regions R3-R7 (xsite_prereg.md addendum 5): frame, epsg and grid are filled in by
# xs_site_setup.py into <root>/site.json
for _k, _b in dict(r3_east=(-94.9, 29.6, -93.8, 30.45), r4_brazos=(-97.0, 29.75, -96.0, 30.75),
                   r5_south=(-96.0, 28.75, -95.0, 29.35), r6_north=(-96.0, 30.45, -94.9, 31.3),
                   r7_northeast=(-94.9, 30.45, -93.8, 31.3)).items():
    SITES[_k] = dict(root=_k, box=_b, frame=None, epsg=None, grid=None, static_date=None, track=0, direction="")
NAME = os.environ.get("SITE", "arizona")
SITE = dict(SITES[NAME])
_base = os.environ.get("DATA_ROOT")                     # set on the DGX Spark; unset on the laptop
WIN_ROOT = f"{_base or 'C:/Kuliah/hackathon/agc-26/realdata'}/{SITE['root']}"
WSL_ROOT = f"{_base or '/mnt/c/Kuliah/hackathon/agc-26/realdata'}/{SITE['root']}"
if os.path.exists(f"{WIN_ROOT}/site.json"):
    import json
    SITE.update(json.load(open(f"{WIN_ROOT}/site.json")))
