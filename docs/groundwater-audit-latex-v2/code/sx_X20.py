"""X20 (added after stage 2, labelled as such): is the high block-CV R2 of X13 just spatial interpolation?
Compare feature sets against a coordinates-only model (x, y) at block sizes 2 / 4 / 8 km.
Env: FEATSET in coords | soil | soil_coords | all | all_coords, BLOCK_KM in 2 | 4 | 8. One process per combination."""
import glob
import json
import os
import numpy as np
import sx_common as C

fs, bk = os.environ["FEATSET"], int(os.environ["BLOCK_KM"])
feats = {}
for f in sorted(glob.glob(f"{C.OUT}/feat_X*.npz")):
    z = np.load(f)
    gm = json.loads(str(z["_groups"]))
    feats.update({k: (z[k], gm.get(k)) for k in z.files if k != "_groups" and gm.get(k) in ("soil", "load", "pumping")
                  and np.isfinite(z[k][C.LAND]).mean() > 0.2})
use = {"coords": [], "soil": [k for k, v in feats.items() if v[1] == "soil"], "all": list(feats)}
cols = use[fs.replace("_coords", "")]
m = C.LAND
X = [feats[k][0][m] for k in cols]
if fs == "coords" or fs.endswith("_coords"):
    X += [C.XX[m], C.YY[m]]
n = bk * 1000 // int(C.PIX)
blocks = ((C.IY // n) * (C.NX // n + 1) + C.IX // n)[m]
r2 = C.block_cv_r2(np.c_[X].T, C.T[m], blocks)
C.save(f"X20_{fs}_{bk}km", dict(featset=fs, block_km=bk, n_features=len(X), cv_r2=r2, n_blocks=int(len(np.unique(blocks)))))
