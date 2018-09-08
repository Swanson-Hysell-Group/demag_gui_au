#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import pandas as pd
from funcs import shortpath


def print_inp(inp_file_name):
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


def main():
    parser = argparse.ArgumentParser(prog="parse_inp.py",
                                     description="""Simple tools for inspecting inp
                                     files""")
    parser.add_argument('inp_file', nargs='*')
    parser.add_argument('-p', '--print', action='store_true',
                        help="""print contents of inp file in readable format""")
    args = vars(parser.parse_args())
    inp_file_list = args.pop('inp_file')
    for filename_inp in inp_file_list:
        if args['print']:
            print_inp(filename_inp)


if __name__ == "__main__":
    main()
