#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import pandas as pd


def shortpath(abspath):
    """return shorter path name with '~' for display/logging"""
    return abspath.replace(os.path.expanduser('~') + os.sep, '~/', 1)


def cache_site_files(data_path):
    """cache site-level magic files to de-clutter data folder"""
    if not os.path.exists(os.path.join(data_path, 'magic_cache')):
        os.makedirs(os.path.join(data_path, 'magic_cache'))
    filt = re.compile('.*_(specimens|samples|sites|locations).txt|.*\.magic')
    for s in os.listdir(data_path):
        if filt.match(s):
            os.rename(os.path.join(data_path, s),
                      os.path.join(data_path, 'magic_cache', s))
    return True


def uncache_site_files(data_path):
    """uncache site-level magic files to speed up magic conversion"""
    if not os.path.exists(os.path.join(data_path, 'magic_cache')):
        return False, 0
    num_cached_files = len(os.listdir(os.path.join(data_path, 'magic_cache')))
    for s in os.listdir(os.path.join(data_path, 'magic_cache')):
        os.rename(os.path.join(data_path, 'magic_cache', s), os.path.join(data_path, s))
    return True, num_cached_files


def print_inp(inp_file_name):
    """Print contents of inp file in readable format. For multi-line inp files,
    each line will be displayed as an individual site.

    Parameters
    ----------
    inp_file_name : str
        relative path to inp file

    Returns
    -------
    bool
        True if successful

    """
    inp_file_full = pd.read_csv(inp_file_name, sep='\t', header=1, dtype=str)
    for j in range(len(inp_file_full)):
        inp_file = inp_file_full.loc[[j], :]
        # format df for display
        with pd.option_context('display.colheader_justify', 'left', 'display.max_rows', None,
                               'display.max_columns', None, 'display.max_colwidth', -1):
            df_display = inp_file.copy()
            site_name = os.path.basename(os.path.dirname(df_display.sam_path.values[0]))
            df_display.sam_path = df_display.sam_path.map(shortpath)
            df_display = df_display.T
            df_display.rename(index={'dont_average_replicate_measurements': 'dont_average'},
                              inplace=True)
            print("{:-^80}".format("  "+site_name+"  "), end="\n")
            print("\n".join([" |  {}".format(i)
                             for i in df_display.to_string(header=False).split("\n")]))
            print("{:-^80}".format(""))
