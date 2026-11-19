# 11 Negative results and lessons

## Tried and failed (do not retry without a new reason)
| Idea | Result | Where |
|---|---|---|
| GACOS troposphere correction | no reduction of noise | file 02 |
| Longer time spans (2014-26) | noise is persistent real local motion; not reduced | file 02 |
| Short pairs (< 24 days) | biased (phase bias); dropped | file 02 |
| SBAS instead of stacking | no gain | file 02 |
| Per-detection width refinement | collinear with local quadratic | file 02 |
| ViT / space-time transformer | worse than stacking | file 03 |
| Detections vs PANGAEA wells / OSM industrial | never beats chance (2014-26 and 2006-10) | files 02, 10 |
| Sinking map / bowls vs registered deep wells (Lo et al. 2022 Fig. 12) | wells on slower-sinking ground; bowls at chance (2018-22 and 2006-10) | file 13 |
| Volume per bowl from subsidence (fixed ratio) | Arizona hold-out error 68 %; T6 coverage 6 % | file 05 |
| Change-over-time (delta pumping vs delta sinking) | rho ~0 | file 05 |
| Transferable calibration (subsidence, heads) | no method beats regional mean | file 05 |
| Transferring a model across sites (with clay) | error factor 5-27 | file 08 |
| Clay thickness as a ratio predictor | rho 0.01 in Houston | file 08 |
| Unweighted top-down split at 4-16 km | fails one direction | file 09 |
| 2 km / 4 km / 8 km volume cells | not accurate | files 06, 09 |
| Relative ranking inside a region (S5, demand, subsidence; 2-8 km) | 0 of 4 new regions pass | file 12 |

## Lessons
1. **Detection is not identification.** The detector finds real, persistent sinking; in Arizona that
   sinking is mostly pumping, in Semarang much of it may be fill loading and natural compaction.
2. **The subsidence-per-pumped-volume ratio is local** (0.2-3 % Arizona, ~28 % Houston). Never carry
   it between sites; anchor volumes to a local total instead.
3. **Patterns transfer, levels do not.** The share of a known total (demand x subsidence) transfers
   across regions at 16 km; absolute volumes do not.
4. **Pre-register, then confirm.** Every claimed pass was fixed in writing before the test data were
   looked at; the one exploratory improvement (volume weighting) was confirmed on two new regions.
5. **Planted-cone success is necessary, not sufficient.** 87 % recall on planted cones said nothing
   about real well locations.

## Operational notes
- Background sessions must edit in a git worktree, then fast-forward `main`.
- Large processing (ALOS) runs on the DGX Spark. Download directly from ASF there; streaming from the
  laptop over the relayed Tailscale link runs at ~0.5-1 MB/s (9 GB took ~2 h in the 2026-11-18 run).
- Credentials (`~/.netrc`, passwords) are entered by the user only.
