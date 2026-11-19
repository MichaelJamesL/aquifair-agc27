"""L4 (exploratory, NOT pre-registered): head decline at the 6 observation wells of Lo et al. 2022 (Fig. 14 insets,
observed heads 1990 -> 2010, read by eye) vs InSAR sinking and sinking per metre of soft sediment (L3 map) there.
Positions: O2-O5 = red stars digitized on Fig. 12 (fig12_georef.json affine); O1, O6 stars hidden under well dots,
placed from their label offset (~100 m uncertainty). Exact one-sided permutation p over the 720 orderings."""
import itertools
import numpy as np
from scipy.stats import spearmanr
import sx_common as C

W = {"O1": (110.35995, -6.98886, -1.8), "O2": (110.39005, -6.96244, 12.0), "O3": (110.40163, -6.96693, 12.5),
     "O4": (110.42466, -6.97980, 9.5), "O5": (110.43009, -6.99474, 2.4), "O6": (110.45530, -6.95920, 30.0)}
thk = np.load(f"{C.OUT}/feat_L3.npz")["lo2022_soft_thickness"]
alos = C.B["D_alos"].astype(float)
rows = []
for k, (lo, la, dh) in W.items():
    iy, ix = C.ll_to_cell([lo], [la])
    s = (slice(max(iy[0] - 1, 0), iy[0] + 2), slice(max(ix[0] - 1, 0), ix[0] + 2))
    t, a, th = float(np.nanmean(C.T[s])), float(np.nanmean(alos[s])), float(np.nanmean(thk[s]))
    rows.append(dict(well=k, head_decline_m=dh, sinking_1822=t, sinking_alos=a, soft_thickness_m=th,
                     sinking_per_m_soft=t / max(th, 5), sinking_per_m_head=t / dh if dh > 1 else None,
                     # Lo et al. 2022: ~0.1 m settlement per 1 m head drop; head decline rate over 1990-2010
                     predicted_0p1_ratio_mm_yr=max(dh, 0) / 20 * 0.1 * 1000))
dh = np.array([r["head_decline_m"] for r in rows])


def exact(y):
    obs = spearmanr(dh, y)[0]
    null = [spearmanr(dh, np.array(p))[0] for p in itertools.permutations(y)]
    return float(obs), float(np.mean(np.array(null) >= obs - 1e-12))


res = dict(wells=rows, note="exploratory; head declines read by eye from Fig. 14 insets")
for key in ("sinking_1822", "sinking_alos", "soft_thickness_m", "sinking_per_m_soft"):
    r, p = exact(np.array([x[key] for x in rows]))
    res[f"rho_head_vs_{key}"], res[f"p_exact_{key}"] = r, p
C.save("L4", res)
