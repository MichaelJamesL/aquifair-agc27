#!/bin/bash
# Run the subsidence-cause experiments on the DGX Spark: stage 1 = X01-X12 + X14 in parallel, stage 2 = X08 again + X13.
# Usage (on the Spark): cd ~/sx_code && nohup bash sx_run.sh > ~/sx_data/out/run.log 2>&1 &
export MAMBA_ROOT_PREFIX=~/mamba OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONUNBUFFERED=1
PY="$HOME/bin/micromamba run -n xs python"
OUT=~/sx_data/out
mkdir -p $OUT
cd ~/sx_code
$PY sx_common.py > $OUT/selfcheck.log 2>&1 || { echo "SELFCHECK FAILED"; exit 1; }
pids=()
for x in X01 X02 X03 X04 X05 X06 X07 X08 X09 X10 X11 X12 X14; do
  [ -f $OUT/$x.json ] && [ "$x" != X08 ] && continue
  ( $PY sx_$x.py > $OUT/$x.log 2>&1 && echo "$x DONE $(date +%T)" || echo "$x FAILED $(date +%T)" ) &
  pids+=($!)
done
echo "stage 1: ${#pids[@]} experiments running in parallel $(date +%T)"
wait
$PY sx_X08.py > $OUT/X08_stage2.log 2>&1 && echo "X08 stage2 DONE" || echo "X08 stage2 FAILED"
$PY sx_X13.py > $OUT/X13.log 2>&1 && echo "X13 DONE" || echo "X13 FAILED"
echo ALL_DONE $(date +%T)
