#!/usr/bin/env bash

source select_inp.sh $1 $2
echo $INP_PATH
demag_gui_au.py -v -i $INP_PATH -d 10
# exit 0

