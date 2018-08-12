#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from utilities import data_output_path, data_dir, inp_dir

def get_config(x):
    global data_output_path, data_dir, inp_dir
    if x=="data_output_path":
        return data_output_path
    elif x=="data_dir":
        return data_dir
    elif x=="inp_dir":
        return inp_dir

if __name__ == "__main__":
    if len(sys.argv)==1:
        sys.exit()
    conf = get_config(str(sys.argv[1]))
    print(conf)
    if "all" in sys.argv:
        for x in [data_output_path, data_dir, inp_dir]:
            print(x)

