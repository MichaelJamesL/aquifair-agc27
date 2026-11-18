#!/bin/bash
# (DGX Spark) Build the layers of one confirmation region (xsite_prereg.md addendum 5):
# OPERA search -> frame/grid/static (xs_site_setup.py) -> granule fetch (3 parallel) + WorldCover + MODIS ET
# -> rate map. Usage: xs_spark_run.sh r3_east   (code in ~/xs_code, data in ~/xs_data/<site>)
export MAMBA_ROOT_PREFIX=~/mamba DATA_ROOT=~/xs_data SITE=$1
PY="$HOME/bin/micromamba run -n xs python"
D=$DATA_ROOT/$SITE; L=$D/run.log
mkdir -p $D && cd ~/xs_code
$PY az_opera_search.py > $L 2>&1 && $PY xs_site_setup.py >> $L 2>&1 || { echo SETUP_FAILED >> $L; exit 1; }
split -n r/3 -d $D/opera_selected.txt $D/sel_
for f in $D/sel_0*; do $PY az_opera_fetch.py fetch $(cat $f) > $D/fetch_$(basename $f).log 2>&1 & done
$PY az_features.py > $D/features.log 2>&1 &
$PY az_et.py > $D/et.log 2>&1 &
wait
$PY az_opera_rate.py >> $L 2>&1 && echo SITE_DONE >> $L || echo RATE_FAILED >> $L
