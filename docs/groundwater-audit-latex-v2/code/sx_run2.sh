#!/bin/bash
# Stage 2 on the DGX Spark: waits for stage 1 (X12), then runs 11 jobs in parallel: X08 stage 2, X13 on 8 targets,
# X16 robustness, X19 sharp edges. Usage: cd ~/sx_code && nohup bash sx_run2.sh > ~/sx_data/out/run2.log 2>&1 &
export MAMBA_ROOT_PREFIX=~/mamba OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONUNBUFFERED=1
PY="$HOME/bin/micromamba run -n xs python"
OUT=~/sx_data/out
cd ~/sx_code
while [ ! -f $OUT/X12.json ] && pgrep -f sx_X12.py > /dev/null; do sleep 20; done
echo "stage 2 start $(date +%T)"
run() { local s=$1 e=$2 n=$3; ( env $e $PY $s > $OUT/$n.log 2>&1 && echo "$n DONE $(date +%T)" || echo "$n FAILED $(date +%T)" ) & }
run sx_X08.py X=1 X08_stage2
for t in da1822 withL d1517 d2326 alos regional local strain; do run sx_X13.py TARGET=$t X13_$t; done
run sx_X16.py X=1 X16
run sx_X19.py X=1 X19
sleep 5; echo "running: $(pgrep -fc 'python sx_X')"
wait
echo ALL2_DONE $(date +%T)
