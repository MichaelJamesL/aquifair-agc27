#!/bin/bash
# Pair counts for a few time/baseline thresholds (summary only).
D=$(dirname "$0")
for c in "400 1500" "300 1200" "500 1000" "250 2000"; do
  set -- $c
  echo "t=$1 b=$2: $(DT=$1 DB=$2 bash $D/alos_stack.sh --summary 2>&1 | grep 'number of pairs')"
done
