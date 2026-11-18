#!/bin/bash
# (DGX Spark, aarch64) Run ISCE stripmapStack run files with independent lines in parallel.
# Usage: alos_run_par.sh RUNFILE JOBS THREADS   (run from ~/alos_work; logs in logs/<runfile>.<k>.log)
export MAMBA_ROOT_PREFIX=~/mamba
E=$MAMBA_ROOT_PREFIX/envs/alos
export PYTHONPATH=$E/share/isce2
export PATH=$E/share/isce2/stripmapStack:$E/bin:$PATH
export OMP_NUM_THREADS=${3:-4}
rf=$1; P=${2:-4}; b=$(basename $rf)
cd ~/alos_work && mkdir -p logs
echo "== $rf ($(grep -c . $rf) lines, P=$P, OMP=$OMP_NUM_THREADS) $(date +%T)"
grep -n . $rf | xargs -d '\n' -P $P -I{} bash -c '
  k=${1%%:*}; cmd=${1#*:}
  bash -c "$cmd" > logs/'$b'.$k.log 2>&1 && echo "ok   $k" || echo "FAIL $k: $cmd"' _ {}
echo "   done $rf $(date +%T)"
