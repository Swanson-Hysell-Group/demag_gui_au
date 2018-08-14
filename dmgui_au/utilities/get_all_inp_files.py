#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NAME
    get_all_inp_files.py

DESCRIPTION
    Retrieve all .inp files within the directory WD

SYNTAX
    get_all_inp_files.py [command line options]

OPTIONS
    -h, --help :
        prints the help message and quits
    -WD : string
        path to the top directory in which to search for files
    -dx, --dropbox :
        find user's Dropbox folder and set that to the primary search path

"""

import os
import sys
import shutil
import warnings
from utilities import find_dropbox
global data_dir, inp_dir, data_output_path, usr_configs_read
try: # get path names if set
    import dmgui_au.config.user as user
    path_conf = user.demaggui_user
    data_dir = path_conf['data_dir']
    inp_dir = path_conf['inp_dir']
    data_output_path = path_conf['magic_out']
    usr_configs_read = True
except:
    warnings.warn("Local paths used by this package have not been defined; please run the script setup.py")
    usr_configs_read = False

def get_all_inp_files(WD = '.', output_path = '.', inp_dir = '.'):
    """
    Retrieve all .inp files within the directory WD

    Parameters
    ----------
    WD : path
        directory to search; default is current directory
    output_path : path
        primary write directory
    inp_dir : path
        designated directory for copying .inp files

    Returns
    -------
    list of .inp files

    """

    if '~' in WD:
        WD = os.path.expanduser(WD)
    if not os.path.isdir(WD):
        raise NameError("directory %s does not exist, aborting" % WD)

    try:
        all_inp_files = []

        for root, dirs, files in os.walk(WD):
            for d in dirs:
                all_inp_files += get_all_inp_files(os.path.join(root, d))

            for f in files:
                if f.endswith(".inp") and not f.startswith(".") and f not in map(
                        lambda x: os.path.split(x)[1], all_inp_files):
                    all_inp_files.append(os.path.join(root, f))

        out_file = open(os.path.join(output_path, "all_inp_files.txt"), "w")
        for inp in all_inp_files:
            out_file.write(inp+'\n')
            inp_copy = shutil.copy(inp, inp_dir)
            # set adequate permissions of the copied files
            os.chmod(inp_copy,0o666)
        out_file.close()
        return all_inp_files
    except RuntimeError:
        raise RuntimeError(
            "Recursion depth exceded, please use different working "
            "directory. There are too many sub-directeries to walk")

if __name__ == "__main__":
    for flg in ['-h', '--help']:
        if flg in sys.argv:
            help(__name__); sys.exit()
    if usr_configs_read and len(sys.argv)==1:
        get_all_inp_files(data_dir, data_output_path, inp_dir)
    if '-WD' in sys.argv:
        WD = sys.argv[sys.argv.index('-WD')+1]
    else:
        WD = '.'
    for flg in ['-dx', '--dropbox']:
        if flg in sys.argv:
            WD = find_dropbox()
            print("Top search directory set to Dropbox folder:\n\n%s\n\n"%(WD))
    get_all_inp_files(WD)
