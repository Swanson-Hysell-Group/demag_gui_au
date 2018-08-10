#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from setuptools import setup, find_packages
from utilities.find_dropbox import find_dropbox

def shortpath(abspath):
    return abspath.replace(os.path.expanduser('~') + os.sep, '~/', 1)

def main(dropbox=False):
    """

    Parameters
    ----------
    dropbox : bool, optional

    Returns
    -------
    local configuration for demag_gui_au

    """
    demaggui_user = {}

    data_dir = ''
    if dropbox:
        data_dir = find_dropbox()
    else:
        print("Enter directory (absolute path) to search for data files:")
        while not os.path.exists(data_dir):
            data_dir = input("> ")
            if "~" in data_dir:
                data_dir = os.path.expanduser(data_dir)
            if not os.path.exists(data_dir):
                print("%s not a valid path!"%(data_dir))

    demaggui_user["data_dir"] = data_dir
    demaggui_user["pkg_dir"] = os.path.abspath(os.path.dirname(__file__))
    demaggui_user["magic_out"] = os.path.join(demaggui_user["pkg_dir"], "data")
    demaggui_user["inp_dir"] = os.path.join(demaggui_user["magic_out"], "inp_files")
    if not os.path.exists(demaggui_user["magic_out"]):
        os.makedirs(demaggui_user["inp_dir"])
    if not os.path.exists(os.path.join(demaggui_user["pkg_dir"], "config")):
        os.makedirs(os.path.join(demaggui_user["pkg_dir"], "config"))
        open(os.path.join(demaggui_user["pkg_dir"], "config", "__init__.py"), 'x')
    if os.path.isfile(os.path.join(demaggui_user["pkg_dir"], "config", "user.py")):
        abort = input("Configuration file 'user.py' already exists. Overwrite? (y/[n])")
        if abort=="y":
            pass
        else:
            print("Aborting..."); sys.exit()
    user_vars = open("./config/user.py", "w")
    user_vars.write("demaggui_user = " + str(demaggui_user))
    user_vars.close()
    print("""
--------------------------------------------------------------------------------
                Package configuration values written to user.py
--------------------------------------------------------------------------------
            """)
    for vals in (("Base path to search for data files:", shortpath(demaggui_user["data_dir"])),
            ("MagIC file output directory:", shortpath(demaggui_user["magic_out"])),
            ("INP directory:", shortpath(demaggui_user["inp_dir"]))):
        print('{0:<35} {1:<45}'.format(*vals))
    print('')

if __name__ == "__main__":
    if "dropbox" in sys.argv:
        main(dropbox=True)
    else:
        main()
