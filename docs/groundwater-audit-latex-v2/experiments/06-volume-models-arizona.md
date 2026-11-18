# 06 Volume models from open data (Arizona, 4 km blocks)

## Question
Is there data that predicts pumping volume per area better than a constant ratio, by a formula
(physics) or by training (supervised)?

## Setup (`az_model.py --block 4000`)
Truth: ADWR metered pumping per 4 km block. Splits: region hold-out (SOUTH <-> ESRV) and within-region
spatial cross-validation (16 km super-blocks, 5 folds).
- `baseline`: regional mean per block.
- `physics` (demand formula): Q = a x built area + b x crop area x ET (non-negative least squares).
- `ml_all`: quantile gradient boosting (10/50/90 %) on InSAR + heads + land cover + ET.
- `ml_noinsar`, `ml_insar_only`: ablations.

## Results (Spearman / median |log10 error| / total error)
| Model | SOUTH -> ESRV | ESRV -> SOUTH | Spatial CV |
|---|---|---|---|
| baseline | - / 0.35 / +57 % | - / 0.42 / -36 % | - / 0.37 / +1 % |
| physics (demand) | **0.49** / 0.44 / +101 % | **0.61** / 0.70 / -79 % | 0.55 / 0.33 / -6 % |
| ml_all | 0.38 / 0.52 / -53 % | 0.40 / 0.67 / -74 % | **0.59** / 0.38 / -24 % |
| ml_noinsar | 0.21 / 0.76 / -10 % | 0.55 / 0.65 / -73 % | 0.50 / 0.46 / -25 % |
| ml_insar_only | 0.09 / 1.12 / -85 % | 0.00 / 0.49 / -39 % | 0.36 / 0.46 / -22 % |

2 km blocks fail.

## Verdict
The demand formula **ranks** areas best across regions (rho 0.5-0.6); InSAR adds little; ML needs
local training data. Totals are off -79 % to +101 % between regions because the share of demand met by
groundwater is unknown. Lesson: transfer the method, never the Arizona ratio.

Results: `realdata/arizona/az_model_4000.json`, `az_model_2000.json`.
