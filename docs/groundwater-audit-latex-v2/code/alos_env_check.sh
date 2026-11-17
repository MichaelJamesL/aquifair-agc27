#!/bin/bash
# Check the WSL conda env used for ALOS-1 processing (ISCE2 + snaphu + asf_search).
export MAMBA_ROOT_PREFIX=~/mamba
tail -3 ~/alos_env.log
M="$HOME/bin/micromamba run -n alos"
$M python -c "import isce, asf_search; print('isce', isce.__file__, 'asf_search', asf_search.__version__)"
$M which snaphu stripmapApp.py stackStripMap.py 2>&1
