"""X06: regional drawdown from the registered wells x soft soil. Cooper-Jacob superposition s ~ sum ln(R / r) over the
74 digitized ESDM wells; does (drawdown, drawdown x soil proxy) add block-CV R2 over the soil proxy alone?
Null: the same gain with the well pattern shifted >= 2 km (sx_prereg.md)."""
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from scipy import ndimage
import sx_common as C

W = C.B["reg_wells_EN"]
WXY = np.c_[W[:, 0] - C.E0, W[:, 1] - C.N0]
m = C.LAND
hill = ndimage.binary_opening(C.H > 25, iterations=1)
P = ndimage.distance_transform_edt(~hill) * C.PIX / 1000.0            # km seaward of the hill foot (thickness proxy)
BASE = np.c_[P[m], C.H[m], C.DCOAST[m] / 1000.0]


def drawdown(xy, R):
    r = np.hypot(C.XX[..., None] - xy[:, 0], C.YY[..., None] - xy[:, 1])
    return np.clip(np.log(R / np.maximum(r, 100.0)), 0, None).sum(-1)


def r2b(args):
    xy, R = args
    s = drawdown(xy, R)
    return C.block_cv_r2(np.c_[BASE, s[m], s[m] * P[m]], C.T[m])


def shifted(dy, dx):
    xy = WXY.copy()
    xy[:, 0] = (xy[:, 0] + dx * C.PIX) % (C.NX * C.PIX)                  # wrap inside the grid
    xy[:, 1] = (xy[:, 1] + dy * C.PIX) % (C.NY * C.PIX)
    return xy


if __name__ == "__main__":                                           # spawned workers import helpers only
    R2A = C.block_cv_r2(BASE, C.T[m])
    res = dict(n_wells=len(W), r2_soil_only=R2A)
    gain = lambda a: r2b(a) - R2A
    # spawn, not fork: forking after OpenMP threads started (HistGradientBoosting) deadlocks the workers
    with ProcessPoolExecutor(8, mp_context=multiprocessing.get_context("spawn")) as ex:
        for R in (5000.0, 2000.0, 10000.0):
            g = gain((WXY, R))
            out = dict(gain=g)
            if R == 5000.0:
                null = np.array(list(ex.map(r2b, [(shifted(*s), R) for s in C.shifts(199)]))) - R2A
                out.update(p_shift=float((1 + np.sum(null >= g)) / (1 + len(null))), null_p95=float(np.percentile(null, 95)),
                           null_mean=float(null.mean()))
                out["PASS"] = bool(g >= 0.05 and g > out["null_p95"])
            s = drawdown(WXY, R)
            out["rho_drawdown_T"] = C.rho(s, C.T, m)
            out["rho_drawdownXsoil_T"] = C.rho(s * P, C.T, m)
            out["rho_soil_T"] = C.rho(P, C.T, m)
            res[f"R{int(R / 1000)}km"] = out
    s5 = drawdown(WXY, 5000.0)
    res["linear_check"] = dict(zip(["b0", "b_soil", "b_drawdown_x_soil"], np.linalg.lstsq(
        np.c_[np.ones(m.sum()), P[m], (s5 * P)[m]], C.T[m], rcond=None)[0].tolist()))
    C.save("X06", res, dict(reg_drawdown_5km=s5, reg_well_density_1km=drawdown(WXY, 1000.0), hill_dist_km=P),
           dict(reg_drawdown_5km="pumping", reg_well_density_1km="pumping", hill_dist_km="soil"))
