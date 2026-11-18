#!/bin/bash
# (DGX Spark) Finish the ALOS-1 stripmapStack after the WSL handover: as each date's raw data
# arrives (xfer_done.txt), rewrite the WSL paths and focus it; then run steps 04-09.
cd ~/alos_work
PY=~/mamba/envs/alos/bin/python
NDATES=$(ls run_files.orig >/dev/null && grep -c . run_files/run_03_focus_split)
done_focus() { grep -qx "$1" focus_done.txt 2>/dev/null; }
touch focus_done.txt
while [ $(grep -c . focus_done.txt) -lt $NDATES ]; do
  for d in $(grep -E '^[0-9]{8}$' xfer_done.txt | grep -v 20080610); do
    done_focus $d && continue
    $PY alos_fix_paths.py SLC_crop/$d > logs/fix_$d.log 2>&1
    grep "config_focus_split_$d" run_files/run_03_focus_split > run_files/run_03_one_$d
    ./alos_run_par.sh run_files/run_03_one_$d 1 16 && [ -f SLC_crop/$d/$d.raw.slc.xml ] && echo $d >> focus_done.txt
  done
  sleep 60
done
echo "all focused $(date +%T)"
./alos_run_par.sh run_files/run_04_geo2rdr_coarseResamp 10 2
./alos_run_par.sh run_files/run_05_refineSecondaryTiming 20 1
./alos_run_par.sh run_files/run_06_invertMisreg 1 4
./alos_run_par.sh run_files/run_07_fineResamp 10 2
./alos_run_par.sh run_files/run_08_grid_baseline 10 2
./alos_run_par.sh run_files/run_09_igram 16 1
echo PIPELINE_DONE $(date +%T)
