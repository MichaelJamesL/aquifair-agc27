#!/bin/bash
# Build ISCE2 v2.6.5 from source into the micromamba env "alos" (no linux-aarch64 conda package exists).
set -e
# Source: git clone --depth 1 -b v2.6.5 https://github.com/isce-framework/isce2 ~/src/isce2
# Patch: comment out add_subdirectory(geo_autoRIFT) in contrib/CMakeLists.txt (needs the OpenCV C API, gone in OpenCV 5)
sed -i "s/^add_subdirectory(geo_autoRIFT)/# &/" ~/src/isce2/contrib/CMakeLists.txt
# gnu17: GCC 15 defaults to C23, which rejects the K&R-style prototypes in ALOS_pre_process
# After install: cp -r ~/src/isce2/contrib/stack/stripmapStack $CONDA_PREFIX/share/isce2/  (cmake does not install it)
export MAMBA_ROOT_PREFIX=~/mamba
eval "$(~/bin/micromamba shell hook -s bash)"
micromamba activate alos
cd ~/src/isce2 && mkdir -p build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX -DCMAKE_PREFIX_PATH=$CONDA_PREFIX \
  -DPYTHON_MODULE_DIR=lib/python3.11/site-packages -DCMAKE_BUILD_TYPE=Release -DWITH_CUDA=OFF -DCMAKE_C_FLAGS=-std=gnu17 \
  -DPython_EXECUTABLE=$CONDA_PREFIX/bin/python
make -j18
make install
python -c "import isce; print(isce.__file__)"
