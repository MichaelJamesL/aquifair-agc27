"""X07: seasonal motion in the 2018-22 LiCSBAS time series (descending) and its timing vs CHIRPS rainfall
(sx_prereg.md). Fit per cell: d = a + b t + c t^2 + A cos(2 pi t) + B sin(2 pi t)."""
import numpy as np
import sx_common as C

ep = C.B["ts_epochs"]
t = np.array([(np.datetime64(f"{e[:4]}-{e[4:6]}-{e[6:]}") - np.datetime64("2020-01-01")).astype(int) / 365.25 for e in ep])
cum = C.B["ts_cum"].astype(float)
U = C.B["ts_U"].astype(float)
ok = C.LAND & (cum[-1] != 0) & np.isfinite(cum).all(0) & (U > 0.5)
Y = -(cum[:, ok] / U[ok])                                            # vertical, mm, + = down (sinking)
X = np.c_[np.ones_like(t), t, t ** 2, np.cos(2 * np.pi * t), np.sin(2 * np.pi * t)]
beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
res_ = Y - X @ beta
r1 = np.sum(res_[1:] * res_[:-1], 0) / np.sum(res_ ** 2, 0)
neff = len(t) * (1 - np.clip(r1, 0, 0.95)) / (1 + np.clip(r1, 0, 0.95))
s2 = np.sum(res_ ** 2, 0) / (len(t) - 5)
cov = np.linalg.inv(X.T @ X)
se_plain = np.sqrt(s2 * (cov[3, 3] + cov[4, 4]) / 2)
se = se_plain * np.sqrt(len(t) / neff)                               # AR(1)-corrected
amp = np.hypot(beta[3], beta[4])
phase = np.arctan2(beta[4], beta[3])                                 # time of maximum downward offset in the year
fast = C.T[ok] > 20
sig = amp > 3 * se
sig_plain = amp > 3 * se_plain
ph = phase[fast & sig]
R = float(np.abs(np.mean(np.exp(1j * ph)))) if len(ph) else 0.0
peak_doy = float((np.angle(np.mean(np.exp(1j * ph))) / (2 * np.pi) % 1) * 365.25) if len(ph) else None
# rainfall timing: CHIRPS (data.chc.ucsb.edu) answers 403 to the Spark, so ERA5 daily rain at the city centre
# from the Open-Meteo archive API, summed per month
import json, urllib.request
q = ("https://archive-api.open-meteo.com/v1/archive?latitude=-6.97&longitude=110.42&start_date=2018-01-01"
     "&end_date=2022-12-31&daily=precipitation_sum&timezone=Asia%2FJakarta")
dd = json.load(urllib.request.urlopen(q, timeout=120))["daily"]
mon = {}
for d, p in zip(dd["time"], dd["precipitation_sum"]):
    mon[d[:7]] = mon.get(d[:7], 0.0) + (p or 0.0)
rain = np.array([(int(k[:4]) + (int(k[5:]) - 0.5) / 12 - 2020, v) for k, v in sorted(mon.items())])
rain_peak = None
if len(rain) > 24:
    Xr = np.c_[np.ones(len(rain)), np.cos(2 * np.pi * rain[:, 0]), np.sin(2 * np.pi * rain[:, 0])]
    br = np.linalg.lstsq(Xr, rain[:, 1], rcond=None)[0]
    rain_peak = float((np.arctan2(br[2], br[1]) / (2 * np.pi) % 1) * 365.25)
acc = np.full((C.NY, C.NX), np.nan); acc[ok] = 2 * beta[2]           # mm/yr^2, + = sinking speeding up
A = np.full((C.NY, C.NX), np.nan); A[ok] = amp
res = dict(n_cells=int(ok.sum()), n_fast=int(fast.sum()), share_fast_significant=float(sig[fast].mean()),
           share_fast_significant_plain_se=float(sig_plain[fast].mean()), median_amp_fast_mm=float(np.median(amp[fast])),
           phase_resultant_length=R, peak_sinking_doy=peak_doy, rain_peak_doy=rain_peak,
           lag_days_sinking_after_rain=None if (peak_doy is None or rain_peak is None) else float((peak_doy - rain_peak) % 365.25),
           PASS=bool(sig[fast].mean() >= 0.2 and R >= 0.5),
           median_acceleration_fast=float(np.median(acc[ok][fast])),
           share_fast_accelerating=float(np.mean(acc[ok][fast] > 0)),
           rho_amp_T=C.rho(A, C.T, ok), rain_monthly=rain.tolist())
C.save("X07", res, dict(seasonal_amp=A, accel_1822=acc), dict(seasonal_amp="observation", accel_1822="observation"))
