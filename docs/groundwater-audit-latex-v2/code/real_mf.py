"""Local matched-filter cone detector (validated settings from real_cfar.py experiments):
K0 cone (B = 1.5 km) + local quadratic surface fitted by least squares in a 2 km disc around
every cell; detections = local maxima (1 km spacing) of the fitted volume >= 60 (1000 m^3/yr)."""
import numpy as np
from scipy import ndimage
from scipy.signal import fftconvolve
import synth as S
import real_lib as R
import real_goal_maps as GM


class Detector:
    def __init__(s, mask, H, D, B=1500.0, rw=2000.0, thr=60.0, nms=1000.0):
        s.mask, s.thr, s.nms = mask, thr, nms
        clay = R.background("edge", H, D, mask, GM.grid)          # fault-edge step from the clean map
        s.Z, s.idx = S.Zmat(clay), np.flatnonzero(mask.ravel())
        n = int(rw // S.PIX)
        yy, xx = np.mgrid[-n:n + 1, -n:n + 1] * S.PIX
        disc = (np.hypot(xx, yy) <= rw).astype(float)
        u, v = xx / rw, yy / rw
        s.basis = [S.kern(np.hypot(xx, yy), "k0", B) * disc] + [b * disc for b in (1, u, v, u * u, v * v, u * v)]
        m = mask.astype(float)
        nb = len(s.basis)
        NM = np.empty((nb, nb) + mask.shape)
        for i in range(nb):
            for j in range(i, nb):
                NM[i, j] = NM[j, i] = s._conv(m, s.basis[i] * s.basis[j])
        s.NM = np.moveaxis(NM, (0, 1), (-2, -1)) + np.eye(nb) * 1e-9
        s.ok = mask & (s._conv(m, disc) / disc.sum() >= 0.5)

    @staticmethod
    def _conv(a, k):
        return fftconvolve(a, k[::-1, ::-1], mode="same")

    def qhat(s, d):
        beta = np.linalg.lstsq(s.Z[s.idx], d.ravel()[s.idx], rcond=None)[0]
        r = np.where(s.mask, d - (s.Z @ beta).reshape(d.shape), 0.0)
        rhs = np.stack([s._conv(r, b) for b in s.basis], -1)
        return np.linalg.solve(s.NM, rhs[..., None])[..., 0, 0]

    def detect(s, d):
        q = np.where(s.ok, s.qhat(d), -np.inf)
        k = int(s.nms // S.PIX) * 2 + 1
        iy, ix = np.nonzero((q == ndimage.maximum_filter(q, size=k)) & (q > s.thr))
        return np.c_[S.XX[iy, ix], S.YY[iy, ix], q[iy, ix]]
