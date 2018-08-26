#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
# from get_all_inp_files import get_all_inp_files
# global top_dir, pkg_dir, data_dir, data_src, inp_dir, usr_configs_read
# try:  # get path names if set
#     from dmgui_au import pkg_dir, data_dir, data_src, inp_dir
#     usr_configs_read = True
# except:
#     # if setup.py is running, don't issue warning
#     if sys.argv[0] != 'setup.py':
#         print("-W- Local path names have not been set. Please run setup.py")
#     usr_configs_read = False


def combine_inp(inp_files, file_name='all_inp'):
    """
    Function that combines inp files into a single inp file which allows faster
    running of autoupdate wrapper of demag_gui.

    @param: inp_files - list of inp files to combine
    @param: file_name - name of new combined .inp file
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

    print('Writing file -', os.path.relpath(os.path.join(out_path, file_name +
                                                         '.inp')))
    of = open(os.path.join(out_path, file_name + '.inp'), 'w+')
    of.write(ofs)
    of.close()


# def combine_inp(sd=None, out_path=None):
#     """
#     Function that combines inp files into a single inp file which allows faster
#     running of autoupdate wrapper of demag_gui.

#     @param: sd - top level directory whose subdirectories and files will be
#     searched for  all inp files to combine.
#     """

#     global top_dir, pkg_dir, data_dir, data_src, inp_dir, usr_configs_read
#     if sd is None and usr_configs_read:
#         sd = data_src
#     elif sd is None:
#         sd = input("No search directory found. Enter top-level directory to "
#                    "search for inp files: ")
#         sd = os.path.abspath(os.path.expanduser(sd))
#     else:
#         sd = os.path.abspath(sd)

#     if out_path is None and usr_configs_read:
#         out_path = inp_dir
#     elif out_path is None:
#         out_path = '.'
#     else:
#         out_path = os.path.abspath(out_path)

#     all_inp_files = get_all_inp_files(data_src=sd, data_dir=out_path,
#                                       inp_dir=out_path, nocopy=True)
#     if all_inp_files == []:
#         print("No inp files found, aborting process")
#         return

#     ofs = ""
#     ofs += "CIT\r\n"
#     ofs += "sam_path\tfield_magic_codes\tlocation\tnaming_convention\tnum_terminal_char\tdont_average_replicate_measurements\tpeak_AF\ttime_stamp\r\n"
#     for inpfn in all_inp_files:
#         if 'all.inp' in inpfn:
#             continue
#         inpf = open(inpfn, 'r')
#         lines = inpf.read().splitlines()
#         for line in lines[2:]:
#             ofs += line+'\r\n'

#     print('Writing file - ' + out_path + 'all' + '.inp')
#     of = open(out_path + 'all' + '.inp', 'w+')
#     of.write(ofs)
#     of.close()

#     # magic_files = []
#     # dg.read_inp(out_path + 'all' + '.inp', magic_files)
#     # print('Writing file - ' + out_path + 'magic_measurements.txt')
#     # dg.combine_magic_files(magic_files)


if __name__ == "__main__":
    # if "-h" in sys.argv:
    #     help(combine_inp)
    #     sys.exit()
    parser = argparse.ArgumentParser(description="Combine .inp files.")
    parser.add_argument('inp_files', nargs='*')  # , type=)#, default=sys.stdin)
    parser.add_argument('--fname', dest='file_name', type=str)

    args = vars(parser.parse_args())
    inp_file_list = args.pop('inp_files')
    combine_inp(inp_file_list, **args)

    # if usr_configs_read and len(sys.argv) == 1:
    #     combine_inp()
    #     sys.exit()
    # try:
    #     sd = sys.argv[1]
    # except IndexError:
    #     print("no directory to search for inp files to combine, aborting")
    #     sys.exit()
    # try:
    #     out_path = sys.argv[2]
    #     combine_inp(sd, out_path=out_path)
    # except:
    #    combine_inp(sd)
