# 04 Blind realistic test and repeatability

Identical cones at random places do not look like reality, so two further checks were run.

## 4a Blind realistic planted fields (`real_blind.py`, `realdata/semarang/exp/blind1/`)
- `gen`: hidden fields with varied cone widths, volumes and clusters (well fields), saved without
  showing them to the detector step; `detect`: fixed detector from file 02; `score`: compare.
- Result: **recall 73 %**, but **median volume error 61 %**, because the detector assumes a fixed
  width (B = 1.5 km) and real-like cones vary.
- Verdict: detection holds up; per-bowl volume does not.

## 4b Repeatability (`real_repeat.py`)
If detections are real ground motion (not noise), the same places should show up in independent data.
- Across periods 2014-17, 2018-22, 2023-26: **58-64 %** of detections repeat within 1 km vs ~27 %
  under a shifted-map null.
- Across tracks (descending vs ascending, different geometry): **78 %** repeat.
- Verdict: the bowls are real and persistent. Whether they are pumping is a separate question
  (files 05-09).
