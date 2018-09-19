#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NAME
    get_all_inp_files.py

DESCRIPTION
    Retrieve all .inp files within the directory data_src

SYNTAX
    get_all_inp_files.py [command line options]

OPTIONS
    -h, --help :
        prints the help message and quits
    -ds, --data_src : string
        path to the top directory in which to search for files
    -nc, --nocopy :
        write to file all_inp_files.txt, but do not copy anything

"""
# import pdb
# pdb.set_trace()
import os
import sys
from string import ascii_uppercase
import shutil
import argparse
from dmgui_au.utilities import find_dropbox
global top_dir, pkg_dir, data_dir, data_src, inp_dir, usr_configs_read
try:  # get path names if set
    from dmgui_au import pkg_dir, data_dir, data_src, inp_dir
    usr_configs_read = True
except:
    # if setup.py is running, don't issue warning
    if sys.argv[0] != 'setup.py':
        print("-W- Local path names have not been set. Please run setup.py")
    usr_configs_read = False

def get_all_inp_files(data_src='.', inp_dir='.', nocopy = False):
    """
    Retrieve all .inp files within the directory data_src. By default, copies
    these files to directory inp_dir.

    Parameters
    ----------
    data_src : path
        directory to search; default is current directory
    inp_dir : path
        designated directory to which copied .inp files will be written
    nocopy : bool
        if True, do not copy any data files; only write all_inp_files.txt

    Returns
    -------
    list of .inp files

    """

    if '~' in data_src:
        data_src = os.path.expanduser(data_src)
    if not os.path.isdir(data_src):
        raise NameError("directory %s does not exist, aborting" % data_src)

    try:
        all_inp_files = []
        name_conflicts = {}

        for root, dirs, files in os.walk(data_src):
            for d in dirs:
                get_all_inp_files(os.path.join(root, d), inp_dir, nocopy)

            for f in files:
                # test if the file name matches another in the list
                already_recorded = f in map(lambda x: os.path.split(x)[1], all_inp_files)
                # add if it does not (+ other filters)
                if f.endswith(".inp") and not already_recorded:
                    if not any(list(f.startswith(prefix) for prefix in [".", "_", "-"])):
                        all_inp_files.append(os.path.join(root, f))
                # if matching names, are they same file? If not, add to list and
                # record the name conflict
                elif already_recorded and not any(map(lambda x: os.path.samefile(os.path.join(root, f), x), all_inp_files)):
                    # add to main list so that full path to the unique file is
                    # recorded
                    # all_inp_files.append(os.path.join(root, f))
                    # compile name conflicts in a dictionary
                    # name_conflicts[f]=[x for x in all_inp_files if f in os.path.split(x)[1]]
                    if f in name_conflicts.keys():
                        name_conflicts[f].append(os.path.join(root,f))
                    else:
                        name_conflicts[f] = [os.path.join(root,f)]
                    # name_conflicts[f]=[x for x in all_inp_files if f in os.path.split(x)[1]]
        out_file = open(os.path.join(inp_dir, "all_inp_files.txt"), "w")
        # print(name_conflicts)
        for inp in all_inp_files:
            out_file.write(inp+'\n')
            # if os.path.split(inp)[1] in name_conflicts.keys():
            #     for conflicted in name_conflicts[os.path.split(inp)[1]]:
            #         if conflicted != inp:
            #             out_file.write('## CONFLICTS WITH {}\n'.format(conflicted))
            #     print("-I- There are conflicting file names for {}. These "
            #           "have been marked in all_inp_files.txt and will not be "
            #           "copied".format(os.path.split(inp)[1]))
            if not nocopy:
                # TODO: Check to see if file already exists before copying
                # <08-14-18, Luke Fairchild> #
                # ------
                # TODO: Above is done but still need to figure out the best way
                # to go about this...there should be an alternative to
                # overwriting, since these are not actually identical data (a
                # and b series of the same sites). Could consider mimicing the
                # directory tree rather than having all inp files in the same
                # top level directory <08-19-18, Luke Fairchild> #
                # if os.path.isfile(os.path.join(inp_dir, inp)):
                #     overwrite_opt = input("""The file {} already exists in your inp
                #     directory. Do you want to overwrite it? Type 'all' after
                #     your answer if you want to apply this to all conflicts.
                #             (y/[N]/?all) """.format(inp))
                #     if overwrite_opt.split(' ')[0].lower() in "yes":
                #         overwrite = True
                #     else:
                #         overwrite = False
                #     if overwrite_opt.split(' ')[1].lower()=="all":
                #         a
                inp_copy = shutil.copy(inp, inp_dir)
                # set adequate permissions of the copied files
                os.chmod(inp_copy, 0o666)
                # copy conflicts
                # if os.path.split(inp)[1] in name_conflicts.keys():
                #     conflict_files = name_conflicts[os.path.split(inp)[1]]
                #     for i, conflict_file in enumerate(conflict_files):
                #         conflict_name = os.path.basename(inp).replace('.inp', ascii_uppercase[i]+'.inp')
                #         print('-I- Conflict file {} copied as {}'.format(inp,conflict_name))
                #         inp_conflict = shutil.copy(conflict_file, os.path.join(inp_dir,conflict_name))
                #         os.chmod(inp_conflict, 0o666)

        out_file.close()
        return all_inp_files
    except RuntimeError:
        raise RuntimeError(
            "Recursion depth exceded, please use different working "
            "directory. There are too many sub-directeries to walk")


def main():
    parser = argparse.ArgumentParser(description="""Find all .inp files within a
            directory tree and copy to the inp_files repository designated for
            Demag GUI Autoupdate""",
                                     add_help=False,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-h', action='help', help="""show short (-h) or detailed
            (--help) help message""")
    parser.add_argument('-ds', '--data_src', nargs='?', help="""Top-level
    directory in which to search for *.inp files""")
    parser.add_argument('-inp', '--inp_dir', nargs='?', help="""Target for copied
        *.inp files".""")
    parser.add_argument('--nocopy', action='store_true', help="""Do not copy
    files""", default=False)
    if usr_configs_read:
        parser.set_defaults(data_src=data_src, inp_dir=inp_dir)
    # parser.add_argument('--help', dest='help_long', action='store_const',
    #                     const=True, help=argparse.SUPPRESS)
    args = vars(parser.parse_args())
    # if args['help_long']:
    #     help(__name__)
    #     sys.exit()
    # ds = args.pop('data_src')
    # do = args.pop('data_dir')
    # inpd = args.pop('inp_dir')

    # print("""\
    # Getting all .inp files with settings:
    #     Top directory: {}
    #     Main data directory: {}
    #     Inp repository: {}
    #     Copy files = {}
    #         """.format(data_src,data_dir,inp_dir,str(not nocopy)))
    get_all_inp_files(**args)


if __name__ == "__main__":
    main()
