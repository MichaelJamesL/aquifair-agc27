# 02 Semarang detector: global lasso vs local matched filter

## Question
Does the report's method (sparse inversion of cone-shaped sinking bowls, K0 kernel) find pumping
bowls in real Sentinel-1 data, and how accurately?

## How it was tested: planted cones
"Planted" = a synthetic sinking cone with a known volume q (thousand m3/yr of subsidence volume) is
added to the **real** Semarang rate map at a random place. The detector runs on the map; a cone counts
as found if a detection lies within the match tolerance (1 km; also reported at 500 m). The real
background (other sinking, noise) stays, so this measures detection in realistic clutter. It does not
prove that real detections are pumping.

Goal set by the user: recall above 60 % and median volume error under 30 % at q = 100.

## Global vs local
- **Global (lasso):** one non-negative lasso fit of all cones plus a smooth background over the whole
  24 x 16 km map (`synth.fit_sparse`, `real_goal.py`). Real background structure leaks into the cones.
- **Local (matched filter):** at every cell, fit "one K0 cone (B = 1.5 km) + local quadratic surface"
  inside a 2 km disc and keep the cone amplitude; threshold 60, peaks at least 1 km apart
  (`real_cfar.py`, `real_mf.py`). Background is removed locally, so distant structure does not leak in.

Global vs local is about how the background is handled when estimating each cone, not about where
cones are placed.

## Results (q = 100)
| Method | Recall | Median volume error | False per trial |
|---|---|---|---|
| Global lasso (best settings) | 20 % | 34 % | - |
| Two-track + median / edge background | ~45 % | bias depends on background | trade-off |
| Local matched filter, plain stack | 81 % | - | - |
| **Local matched filter, `--rw 2000 --nms 1000 --poly 2 --thrs 60`** | **87 %** (82 % at 500 m) | **12 %** | 0.22 |

Checked on 2 fresh seeds of 500 cones each. Off-mask cells are set to `-inf` before the maximum
filter (a bug that had distorted peaks).

## Limits
- Volume about 2x too high if the true cone width is B = 1 km; B = 2.5 km cones are mostly missed.
- Per-detection width refinement fails: it is collinear with the local quadratic.
- Real detections never beat chance against PANGAEA wells or OSM industrial land.

Results: `realdata/semarang/exp/cfar*.json`, `goal_*.json`.
