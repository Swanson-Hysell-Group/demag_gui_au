#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import textwrap
import argparse


def combine_inp(inp_files, file_name='all_inp'):
    """
    Function that combines inp files into a single inp file, allowing data to be
    conveniently grouped into custom data sets and viewed altogether.

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


def main():
    prog_desc = textwrap.dedent("""\
    Combine .inp files so that particular data sets can be read into and viewed
    in DemagGUI AU simultaneously. Accepts glob patterns for selecting files to
    be combined, or file names can be given as individual arguments.""")

    prog_epilog = textwrap.dedent("""\

    Examples
    --------
    Consider a paleomagnetic study comprising 50 sites total. Each site name
    begins with 'NE' such that the set of inp files from this study are
    'NE1.inp', 'NE2.inp', [...] , 'NE50.inp'. As you develop data for each site,
    you decide you want to be able to view all data together (i.e. at the
    study-level) within DemagGUI. This can be done by combining all inp files
    from this study (which can be selected via a simple glob pattern, e.g.
    'NE*.inp') into a single composite inp file named, say, 'NE_study_all':

        $ combine_inp_files.py --fname NE_study_all NE*.inp

    Instead of providing a glob pattern, you can also simply list out the files as
    positional arguments on the command line. This might be preferable when
    combining a small number of sites:

        $ combine_inp_files.py --fname NE1_thru_4 NE1.inp NE2.inp NE3.inp NE4.inp

    Or when file names are dissimilar and you don't care to figure out what glob
    pattern would work:

        $ combine_inp_files.py --fname combined_inp CF16R.inp UF2.inp BFR-.inp py4H.inp

    """)
    parser = argparse.ArgumentParser(prog="combine_inp_files.py",
                                     description=prog_desc,
                                     epilog=prog_epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('inp_files', nargs='*',
                        help="""inp files to combine. If no file names are
                        provided, defaults to all *.inp files within the current
                        directory.""")
    parser.add_argument('--fname', dest='file_name', type=str, default="all_inp")

    args = vars(parser.parse_args())
    inp_file_list = args.pop('inp_files')
    if len(inp_file_list) == 0:
        filt = re.compile('.*\.inp')
        # search for inp files in CWD; the filter below excludes directories
        for s in list(filter(os.path.isfile, os.listdir())):
            if filt.match(s):
                inp_file_list.append(s)
    if len(inp_file_list) == 0:
        print("Nothing to combine---no file names were provided, and no inp "
              "files were found in current directory.")
    else:
        combine_inp(inp_file_list, **args)


if __name__ == "__main__":
    main()
