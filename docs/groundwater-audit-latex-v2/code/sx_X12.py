"""X12: many small domestic wells. WorldPop 2000 and 2020 (100 m, unconstrained) population density and growth vs
sinking beyond geography (sx_prereg.md)."""
import os
import urllib.request
import numpy as np
import sx_common as C

pop = {}
for y in (2000, 2020):
    u = f"https://data.worldpop.org/GIS/Population/Global_2000_2020/{y}/IDN/idn_ppp_{y}.tif"
    try:
        pop[y] = C.to_grid("/vsicurl/" + u) * 100.0                     # persons per km2 (100 m pixels)
    except Exception as e:
        print("remote read failed, downloading", y, str(e)[:80], flush=True)
        fn = f"{C.DATA}/idn_ppp_{y}.tif"
        if not os.path.exists(fn):
            urllib.request.urlretrieve(u, fn)
        pop[y] = C.to_grid(fn) * 100.0
growth = pop[2020] - pop[2000]
d20 = C.driver_test("population_density_2020", pop[2020], +1)
dg = C.driver_test("population_growth_2000_2020", growth, +1)
res = dict(density_2020=d20, growth=dg, PASS=bool(d20["rho_partial"] >= 0.2 and d20["p_shift_partial"] < 0.05),
           pop_total_grid_2020=float(np.nansum(pop[2020]) * 0.04), pop_total_grid_2000=float(np.nansum(pop[2000]) * 0.04))
C.save("X12", res, dict(pop_2020=pop[2020], pop_growth=growth), dict(pop_2020="pumping", pop_growth="pumping"))
