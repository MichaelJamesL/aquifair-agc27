#!/bin/bash
# Copernicus GLO-30 DEM (open, AWS) for the Semarang box -> ISCE DEM in ~/alos_work/DEM.
# shortcut: heights stay on the EGM2008 geoid (~+25 m vs ellipsoid here); a constant height
# offset on a flat coastal plain adds an almost uniform phase, removed by referencing.
set -e
export MAMBA_ROOT_PREFIX=~/mamba
M="$HOME/bin/micromamba run -n alos"
mkdir -p ~/alos_work/DEM && cd ~/alos_work/DEM
for t in S07_00_E110_00 S08_00_E110_00; do
  f=Copernicus_DSM_COG_10_${t}_DEM
  [ -f $f.tif ] || curl -sS -f -o $f.tif https://copernicus-dem-30m.s3.amazonaws.com/$f/$f.tif
done
$M gdalbuildvrt -q merged.vrt Copernicus_DSM_COG_10_*_DEM.tif
# crop to box + 0.15 deg margin, ENVI int16 as ISCE expects
$M gdal_translate -q -of ENVI -ot Int16 -projwin 110.15 -6.75 110.75 -7.25 merged.vrt dem.wgs84
$M python $HOME/mamba/envs/alos/lib/python3.11/site-packages/isce/applications/gdal2isce_xml.py -i dem.wgs84
ls -la ~/alos_work/DEM
