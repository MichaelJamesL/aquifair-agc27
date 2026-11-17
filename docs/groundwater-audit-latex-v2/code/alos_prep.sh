#!/bin/bash
# Verify zips, copy to the WSL disk, organise by date (prepRawALOS, FBD->FBS) and unpack to ISCE raw.
set -e
export MAMBA_ROOT_PREFIX=~/mamba
export PYTHONPATH=$HOME/mamba/envs/alos/share/isce2
S=$HOME/mamba/envs/alos/share/isce2/stripmapStack
M="$HOME/bin/micromamba run -n alos"
W=~/alos_work
mkdir -p $W/download
cd /mnt/c/Kuliah/hackathon/agc-26/realdata/semarang/alos/raw
for z in *.zip; do
  $M python -c "import zipfile,sys; z=zipfile.ZipFile(sys.argv[1]); b=z.testzip(); print(sys.argv[1], 'OK' if b is None else 'BAD '+b)" $z
  [ -f $W/download/$z ] || cp $z $W/download/
done
cd $W
$M python $S/prepRawALOS.py -i download -o SLC -t "" --dual2single
ls $W; ls $W/download | head; ls run_unPackALOS* 2>/dev/null; head -3 run_unPackALOS* 2>/dev/null
