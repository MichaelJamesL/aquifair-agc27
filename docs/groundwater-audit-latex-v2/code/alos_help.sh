#!/bin/bash
# Print the ISCE2 stripmapStack tool options used by the ALOS pipeline.
export MAMBA_ROOT_PREFIX=~/mamba
S=$HOME/mamba/envs/alos/share/isce2/stripmapStack
ls $S
for t in prepRawALOS.py stackStripMap.py; do
  echo "== $t"; $HOME/bin/micromamba run -n alos python $S/$t -h 2>&1 | head -90
done
