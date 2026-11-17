#!/bin/bash
# Configure the ISCE2 stripmap stack: crop to the Semarang box (+ margin), ~100 m looks
# (14 range x 32 azimuth on ALOS FBS), snaphu unwrapping. Args are passed through (e.g. --summary).
export MAMBA_ROOT_PREFIX=~/mamba
E=$HOME/mamba/envs/alos
export PYTHONPATH=$E/share/isce2
export PATH=$E/share/isce2/stripmapStack:$E/bin:$PATH
cd ~/alos_work
python $E/share/isce2/stripmapStack/stackStripMap.py -s SLC -d DEM/dem.wgs84 -w . \
  -x "-7.10 -6.87 110.30 110.61" -m 20080610 -t ${DT:-700} -b ${DB:-2500} -a 32 -r 14 \
  -u snaphu -f 0.5 -W interferogram -c "" "$@"
