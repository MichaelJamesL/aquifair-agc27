#!/bin/bash
# Run ISCE stripmapStack run files sequentially (one heavy job at a time: RAM is tight).
# Usage: alos_run.sh RUNFILE [RUNFILE ...]   (paths relative to ~/alos_work)
export MAMBA_ROOT_PREFIX=~/mamba
E=$HOME/mamba/envs/alos
export PYTHONPATH=$E/share/isce2
export PATH=$E/share/isce2/stripmapStack:$E/bin:$PATH
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-2}       # 4 threads crashed WSL (memory) during focusing
cd ~/alos_work
for rf in "$@"; do
  n=$(grep -c . $rf); k=0
  echo "== $rf ($n lines) $(date +%T)"
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    k=$((k+1))
    bash -c "$line" > /tmp/alos_step.log 2>&1 || { echo "FAIL [$k/$n]: $line"; tail -15 /tmp/alos_step.log; }
  done < $rf
  echo "   done $rf $(date +%T)"
done
