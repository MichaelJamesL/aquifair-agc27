# 03 Transformer / ViT ablation

## Question
Can a transformer, placed between the interferogram stack and the rate map (not replacing the
physics), produce a cleaner rate map than stacking?

## Setup (`real_ml.py`, GPU RTX 3050, checkpoints in `realdata/semarang/exp/ml_ckpt`)
- Training data: windows of real stable-ground interferograms (noise only) with injected deformation
  of known rate; 305 training and 228 validation windows, 3000 steps.
- Methods: `stack_all` (all pairs), `stack24` (pairs >= 24 days), `median`, `deepsets` (set model over
  pairs), `t0` (temporal transformer per pixel), `t0_24` (t0 on pairs >= 24 days), `t1` (t0 + coherence
  input), `stpix` (space-time pixel transformer), `vit` (ViT patches).
- Metric: MAE of the recovered rate on validation windows (mm/yr); also detection on planted cones.

## Results
| Method | MAE (mm/yr) | Parameters | Train time (s) |
|---|---|---|---|
| stack_all | 3.20 | - | - |
| stack24 | 2.70 | - | - |
| median | 3.71 | - | - |
| deepsets | 2.92 | 21.8 k | 55 |
| t0 | 2.69 | 106 k | 923 |
| **t0_24** | **2.14** | 106 k | 923 |
| t1 | 3.79 | 108 k | 931 |
| stpix | 5.83 | 187 k | 502 |
| vit | 3.51 | 177 k | 457 |

## Verdict
Only the temporal transformer on >= 24-day pairs beats plain stacking, modestly (2.14 vs 2.70 mm/yr).
Spatial models (ViT, space-time) are worse: the real noise is persistent local motion, which spatial
context cannot remove. The detector in file 02 uses plain stacking of >= 24-day pairs.

Results: `realdata/semarang/exp/ml_ablation.json`, `ml_ablation_spatial.json`.
