#!/usr/bin/env bash

# unset inp_dir
unset output_dir
# inp_dir=$(parse_config.py inp_dir)
output_dir=$(parse_config.py data_output_path)
echo $output_dir
# cd $output_dir
# source select_inp.sh $1 $2
# echo "Reading from file $INP_PATH"
# demag_gui_au.py -v -i $INP_PATH -d 10
# demag_gui_au.py -v -i "./inp_files/Z118.inp" -d 10
# demag_gui_au.py -WD $output_dir -v -i $INP_PATH -d 10
# exit 0

