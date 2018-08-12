#!/usr/bin/env bash
# set -euo pipefail
# IFS=$'\n\t'

# Run by simply calling from terminal:
# ~$ ./debug_all_inp_files.sh [path to check for inp files to debug]
# if this doesn't work you might have to change file permissions try typing chmod a+x debug_all_inp_files.sh first.

for f in $(find $1 -name "*.inp"); do python debug_inp.py $f; done
