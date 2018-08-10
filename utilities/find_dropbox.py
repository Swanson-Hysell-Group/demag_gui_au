#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
try:
    import json
except:
    pass


def find_dropbox():
    """
    Attempts to find the user's Dropbox folder.
    Will additionally search for Hargraves_Data folder in the top directory.

    Returns
    -------
    Path to Dropbox

    """
    if os.path.isfile(os.path.expanduser(os.path.join("~", ".dropbox", "info.json"))):
        drpbx_info_file = os.path.expanduser(os.path.join("~", ".dropbox", "info.json"))
        drpbx_info = open(drpbx_info_file, 'r')
        drpbx_json = drpbx_info.read()
        drpbx_info.close()
        try:
            drpbx_dict = json.loads(drpbx_json)
        except:
            drpbx_dict = dict(eval(drpbx_json.replace('false','False').replace('true','True')))
        finally:
            drpbx_acts = list(drpbx_dict.keys())
            if len(drpbx_acts)>1:
                print("Found multiple Dropbox accounts:")
                for i,j in enumerate(drpbx_acts):
                    print("[", i,"]", j)
                n = input("Which account to use? [index number]: ")
                drpbx_dict = drpbx_dict[drpbx_acts[n]]
            else:
                drpbx_dict = drpbx_dict[drpbx_acts[0]]
            drpbx_path=os.path.abspath(drpbx_dict['path'])

    else:
        drpbx_path = input("""
        There was a problem finding your Dropbox folder.
        Please provide the path to your Dropbox folder here (press Enter to skip): )
        """)

    if os.path.isdir(os.path.join(drpbx_path,"Hargraves_Data")):
        drpbx_path = os.path.join(drpbx_path,"Hargraves_Data")
    return drpbx_path

if __name__ == "__main__":
    find_dropbox()
