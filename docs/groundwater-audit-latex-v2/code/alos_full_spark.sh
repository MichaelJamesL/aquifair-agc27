#!/bin/bash
# (DGX Spark) Full ALOS-1 Semarang pipeline from ASF zips: wait for alos_download_spark.py,
# unpack (prepRawALOS, FBD->FBS), configure the stripmapStack (alos_stack.sh), run 01-09, pack.
# Prereqs in ~/alos_work: download/ (21 zips), DEM/ (alos_dem.sh), alos_run_par.sh, alos_stack.sh, alos_extract.py.
cd ~/alos_work
export MAMBA_ROOT_PREFIX=~/mamba
E=$MAMBA_ROOT_PREFIX/envs/alos
export PYTHONPATH=$E/share/isce2
export PATH=$E/share/isce2/stripmapStack:$E/bin:$PATH
while pgrep -f alos_download_spark >/dev/null; do sleep 30; done
n=$(ls download/*.zip | wc -l); echo "zips: $n $(date +%T)"
for z in download/*.zip; do python -c "import zipfile,sys; b=zipfile.ZipFile(sys.argv[1]).testzip(); sys.exit(b is not None)" $z || echo "BAD ZIP $z"; done
python $E/share/isce2/stripmapStack/prepRawALOS.py -i download -o SLC -t "" --dual2single
./alos_run_par.sh run_unPackALOS 12 1
bash alos_stack.sh
ls run_files
for rf in run_01_crop:12:1 run_02_reference:1:16 run_03_focus_split:10:2 run_04_geo2rdr_coarseResamp:10:2 \
          run_05_refineSecondaryTiming:20:1 run_06_invertMisreg:1:4 run_07_fineResamp:10:2 \
          run_08_grid_baseline:10:2 run_09_igram:16:1; do
  IFS=: read f p t <<< "$rf"
  ./alos_run_par.sh run_files/$f $p $t
done
python alos_extract.py
echo PIPELINE_DONE $(date +%T)
