"""X16 (stage 2, robustness, descriptive): every driver feature saved by X01-X12 and L1/L3 against the sinking map of
each period (ALOS 2006-10, 2014-17, 2018-22, 2023-26, descending-only 2018-22): rho, partial rho (geography residual)
and shift-null p (199 draws). A driver whose sign flips between periods is not a stable explanation."""
import glob
import json
import numpy as np
import sx_common as C

TG = {"alos_0610": C.B["D_alos"], "d_1417": C.B["D_d1517"], "da_1822": C.T, "d_2326": C.B["D_d2326"],
      "d_1822": C.B["D_d1822"]}
feats = {}
for f in sorted(glob.glob(f"{C.OUT}/feat_[XL]*.npz")):
    z = np.load(f)
    gm = json.loads(str(z["_groups"]))
    feats.update({k: (z[k], gm.get(k)) for k in z.files if k != "_groups" and gm.get(k) not in (None, "observation")})
out = {}
for k, (x, g) in feats.items():
    row = dict(group=g)
    for tn, t in TG.items():
        t = np.asarray(t, float)
        m = C.LAND & np.isfinite(t) & np.isfinite(x)
        if m.sum() < 50:
            continue
        r = C.rho(x, t, m)
        gr = C.geo_resid(np.where(C.LAND, t, np.nan))
        rp = C.rho(x, gr, m)
        p = C.shift_p(lambda xx: C.rho(xx, t, C.LAND & np.isfinite(t)), x, r, 199, np.sign(r) or 1)[0]
        pp = C.shift_p(lambda xx: C.rho(xx, gr, C.LAND & np.isfinite(t)), x, rp, 199, np.sign(rp) or 1)[0]
        row[tn] = dict(rho=r, p=p, rho_partial=rp, p_partial=pp)
    signs = [np.sign(v["rho_partial"]) for kk, v in row.items() if kk != "group" and abs(v["rho_partial"]) >= 0.1]
    row["partial_sign_stable"] = bool(len(signs) >= 3 and abs(sum(signs)) == len(signs))
    out[k] = row
C.save("X16", out)
