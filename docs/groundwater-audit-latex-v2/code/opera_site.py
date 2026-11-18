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
NAME = os.environ.get("SITE", "arizona")
SITE = SITES[NAME]
WIN_ROOT = f"C:/Kuliah/hackathon/agc-26/realdata/{SITE['root']}"
WSL_ROOT = f"/mnt/c/Kuliah/hackathon/agc-26/realdata/{SITE['root']}"
