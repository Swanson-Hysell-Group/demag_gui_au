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
# import argparse
# import pickle

# set up argparser for cli
# parser = argparse.ArgumentParser(description="Retrieve all .inp files within the directory WD")

# parser.add_argument("-WD")
# parser.add_argument("-dx", "--dropbox", action='store_true')

# TODO: For testing purposes --- but should obviously not be hard coded
# like this <08-08-18, Luke Fairchild> #
data_output_path = os.path.expanduser("~/GitHub_files/demag_gui_au/data/inp_files")

def find_dropbox():
    """
    Attempts to find the user's Dropbox folder.
    Will additionally search for Hargraves_Data folder in the top directory.

    Returns
    -------
    Path to Dropbox

    """
    if os.path.isfile(os.path.expanduser("~/.dropbox/info.json")):
        drpbx_info_file = os.path.expanduser("~/.dropbox/info.json")
        drpbx_info = open(drpbx_info_file, 'r')
        drpbx_dict = drpbx_info.read().splitlines()[0]
        drpbx_info.close()
        drpbx_dict=dict(eval(drpbx_dict.replace('false','False').replace('true','True')))
        drpbx_path=drpbx_dict['personal']['path']
    else:
        drpbx_path = input("Option '-dropbox' given but there was a problem finding your Dropbox folder.\n"
                "Please provide the path to your Dropbox folder here (press Enter to skip): ")
    if os.path.isdir(os.path.join(drpbx_path,"Hargraves_Data")):
        drpbx_path = os.path.join(drpbx_path,"Hargraves_Data")
    return drpbx_path

def get_all_inp_files(WD='.'):
    """
    Retrieve all .inp files within the directory WD

    Parameters
    ----------
    WD : directory to search; default is current directory

    Returns
    -------
    list of .inp files

    """

    global data_output_path

    if '~' in WD:
        WD = os.path.expanduser(WD)
    if not os.path.isdir(WD):
        print("directory %s does not exist, aborting" % WD)
        return []

    try:
        all_inp_files = []

        for root, dirs, files in os.walk(WD):
            for d in dirs:
                all_inp_files += get_all_inp_files(os.path.join(root, d))

            for f in files:
                if f.endswith(".inp") and f not in map(
                        lambda x: os.path.split(x)[1], all_inp_files):
                    all_inp_files.append(os.path.join(root, f))

        # out_file = open("all_inp_files.p", "wb")
        # pickle.dump(all_inp_files,out_file)
        out_file = open("all_inp_files.txt", "w")
        for inp in all_inp_files:
            out_file.write(inp+'\n')
            inp_copy = shutil.copy(inp, data_output_path)
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
    if '-WD' in sys.argv:
        WD = sys.argv[sys.argv.index('-WD')+1]
    else:
        WD = '.'
    for flg in ['-dx', '--dropbox']:
        if flg in sys.argv:
            WD = find_dropbox()
            print("Top search directory set to Dropbox folder:\n\n%s\n\n"%(WD))
    get_all_inp_files(WD)
