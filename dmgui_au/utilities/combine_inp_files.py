#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse


def combine_inp(inp_files, file_name='all_inp'):
    """
    Function that combines inp files into a single inp file which allows faster
    running of autoupdate wrapper of demag_gui.

    Parameters
    ----------
    inp_files : list
        List of inp files to combine
    file_name : str, optional
        Name of new, combined .inp file to be written. If no name is specified,
        the file will be written with the default name `all_inp.inp`

    Returns
    -------
    bool
        True if successful, False otherwise.

    """
    out_path = '.'

    ofs = ""
    ofs += "CIT\r\n"
    ofs += "sam_path\tfield_magic_codes\tlocation\tnaming_convention\tnum_terminal_char\tdont_average_replicate_measurements\tpeak_AF\ttime_stamp\r\n"
    for inpfn in inp_files:
        if 'all.inp' in inpfn:
            continue
        inpf = open(inpfn, 'r')
        lines = inpf.read().splitlines()
        for line in lines[2:]:
            ofs += line+'\r\n'

    print('Writing file -',
          os.path.relpath(os.path.join(out_path, file_name + '.inp')))
    of = open(os.path.join(out_path, file_name + '.inp'), 'w+')
    of.write(ofs)
    of.close()
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="combine_inp_files.py",
                                     description="""\
                                     Combine .inp files so that particular data
                                     sets can be read into and viewed within
                                     DemagGUI AU at the same time. Accepts glob
                                     patterns for selecting files to be
                                     combined, or file names can be given as
                                     individual arguments.""")
    parser.add_argument('inp_files', nargs='*')
    parser.add_argument('--fname', dest='file_name', type=str, default="all_inp")

    args = vars(parser.parse_args())
    inp_file_list = args.pop('inp_files')
    combine_inp(inp_file_list, **args)
