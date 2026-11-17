#!/bin/bash
# Which acquisition dates already have a focused SLC; write the remaining focus lines to a resume file.
cd ~/alos_work
head -1 run_files/run_03_focus_split
ls SLC_crop/20061206/ | head
: > run_files/run_03_resume
while IFS= read -r line; do
  d=$(echo "$line" | grep -oE 'config_focus_split_[0-9]{8}' | grep -oE '[0-9]{8}')
  if ls SLC_crop/$d/*.slc >/dev/null 2>&1; then echo "$d focused"; else echo "$d todo"; echo "$line" >> run_files/run_03_resume; fi
done < run_files/run_03_focus_split
echo "resume lines: $(grep -c . run_files/run_03_resume)"
