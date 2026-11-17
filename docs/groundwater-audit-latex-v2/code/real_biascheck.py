"""Are detected sources real motion or phase bias? Bias decays with pair length (Ansari et al.);
real deformation does not. For each source: local anomaly = rate at source minus median rate in a
1-2 km ring, from rate maps built with ONLY 24-, 36- or 48-day pairs (descending track).

Usage: python real_biascheck.py SOURCES.json
"""
import sys, json
import numpy as np
import real_lib as R
import synth as S

SD = "C:/Kuliah/hackathon/agc-26/realdata/semarang/"
g = R.Grid(428000.0, 9220000.0, 32749)
src = np.array(json.load(open(sys.argv[1]))["fits"]["cv"]["sources"]).reshape(-1, 3)
z = np.load(SD + "t076/stack.npz")
days = np.array([(np.datetime64(f"{p[9:13]}-{p[13:15]}-{p[15:]}") -
                  np.datetime64(f"{p[:4]}-{p[4:6]}-{p[6:8]}")).astype(int) for p in z["pairs"]])


def rate_exact(d):
    """Stacked rate from pairs of exactly d days (reuses rate_map by masking the stack on the fly)."""
    import tempfile, os
    keep = days == d
    tmp = tempfile.mkdtemp()
    np.savez(f"{tmp}/stack.npz", **{k: (z[k][keep] if k in ("pairs", "unw", "cc") else z[k]) for k in z.files})
    rm = R.rate_map(tmp)
    D, c = g.block_mean(rm["sub"], rm["transform"])
    return np.where(c >= 1, D, np.nan), int(keep.sum())


rr = np.hypot(S.XX[..., None] - src[:, 0], S.YY[..., None] - src[:, 1])      # (NY, NX, nsrc)
print("pairs   " + "  ".join(f"src{k}" for k in range(len(src))) + "   median")
for d in (12, 24, 36, 48):
    D, n = rate_exact(d)
    an = []
    for k, s in enumerate(src):
        core = D[rr[..., k] <= 300]
        ring = D[(rr[..., k] >= 1000) & (rr[..., k] <= 2000)]
        an.append(np.nanmedian(core) - np.nanmedian(ring))
    print(f"{d:2d} d ({n:3d})  " + "  ".join(f"{a:5.1f}" for a in an) + f"   {np.nanmedian(an):5.1f}")
