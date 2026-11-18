#!/bin/bash
# Stream the minimal ALOS set (raw only; refocus on the Spark) over the slow DERP-relayed link.
Z=~/mamba/envs/alos/bin/zstd
SSH="ssh -i $HOME/.ssh/id_spark -o BatchMode=yes -o ServerAliveInterval=30 michaeljl@100.103.204.6"
cd ~/alos_work
tar -cf - DEM configs run_files baselines isce.log | $Z -T0 -3 | $SSH 'cd ~/alos_work && zstd -dc | tar -xf - && echo small > xfer_done.txt' || exit 1
for d in 20080610 $(ls SLC_crop | grep -v 20080610); do
  $SSH "grep -qx $d ~/alos_work/xfer_done.txt" && continue
  for try in 1 2 3; do
    tar -cf - SLC_crop/$d/$d.raw SLC_crop/$d/$d.raw.xml SLC_crop/$d/$d.raw.vrt SLC_crop/$d/raw.bak SLC_crop/$d/raw.dat SLC_crop/$d/raw.dir \
      | $Z -T0 -3 | $SSH "cd ~/alos_work && zstd -dc | tar -xf - && echo $d >> xfer_done.txt" && break
  done
  echo "$d $(date +%T)"
done
echo ALLDONE
