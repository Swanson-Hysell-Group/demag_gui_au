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
    -nc, --nocopy :
        write to file all_inp_files.txt, but do not copy anything

"""
# import pdb
# pdb.set_trace()
import os
import sys
import shutil
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

def get_all_inp_files(WD='.', output_path='.', inp_dir='.', nocopy = False):
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
    nocopy : bool
        if True, do not copy any data files; only write
        to all_inp_files.txt

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
        name_conflicts = {}

        for root, dirs, files in os.walk(WD):
            for d in dirs:
                get_all_inp_files(os.path.join(root, d), output_path, inp_dir, nocopy)

            for f in files:
                # test if the file name matches another in the list
                already_recorded = f in map(lambda x: os.path.split(x)[1], all_inp_files)
                # add if it does not (+ other filters)
                if f.endswith(".inp") and not f.startswith(".") and not already_recorded:
                    all_inp_files.append(os.path.join(root, f))
                # if matching names, are they same file? If not, add to list and
                # record the name conflict
                elif already_recorded and not any(map(lambda x: os.path.samefile(f, x), all_inp_files)):
                    # add to main list so that full path to the unique file is
                    # recorded
                    all_inp_files.append(os.path.join(root, f))
                    # compile name conflicts in a dictionary
                    name_conflicts[f]=[x for x in all_inp_files if f in os.path.split(x)[1]]

        out_file = open(os.path.join(output_path, "all_inp_files.txt"), "w")
        for inp in all_inp_files:
            out_file.write(inp+'\n')
            if os.path.split(inp)[1] in name_conflict.keys():
                for conflicted in name_conflict[os.path.split(inp)[1]]:
                    if conflicted != inp:
                        out_file.write('## CONFLICTS WITH {}\n'.format(conflicted))
                print("-I- There are conflicting file names for {}. These "
                      "have been marked in all_inp_files.txt and will not be "
                      "copied".format(os.path.split(inp)[1]))
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
                os.chmod(inp_copy,0o666)
        out_file.close()
        return all_inp_files
    except RuntimeError:
        raise RuntimeError(
            "Recursion depth exceded, please use different working "
            "directory. There are too many sub-directeries to walk")


# TODO: Put this under a main() function <08-19-18, Luke Fairchild> #
def main():
    try:  # get path names if set
        from dmgui_au import pkg_dir, data_dir, data_src, inp_dir
        usr_configs_read = True
    except:
        usr_configs_read = False

    parser = argparse.ArgumentParser(description="""Find all .inp files within
            a directory tree and copy to the inp_files repository designated for
            Demag GUI Autoupdate""", add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-h', action='help', help="""show short (-h) or detailed
            (--help) help message""")
    parser.add_argument('-ds','--data_src', nargs='?', help="""Top-level
    directory in which to search for *.inp files""")
    parser.add_argument('-do','--data_dir', nargs='?', help="""Top-level output
        directory (target for all_inp_files.txt)""", default = "./data")
    parser.add_argument('-inp','--inp_dir', nargs='?', help="""Target for copied
        *.inp files".""")
    parser.add_argument('--nocopy', action='store_true', help="""Do not copy
    files""")
    if usr_configs_read:
        parser.set_defaults(data_src=data_src,data_dir=data_dir,inp_dir=inp_dir)

    parser.add_argument('--help', dest='help_long', action='store_const',
                        const=True, help=argparse.SUPPRESS)
    args = vars(parser.parse_args())
    if args['help_long']:
        help(__name__)
        sys.exit()

    # parser.add_argument('--sam_path')
    # parser.add_argument('--magic_codes')
    # parser.add_argument('--nc')
    # parser.add_argument('--term')
    # parser.add_argument('--no_ave')
    # parser.add_argument('--peak_AF')
    # parser.add_argument('--noinput', action='store_true',
    #                     help='bypass all input()')

    # for flg in ['-h', '--help']:
    #     if flg in sys.argv:
    #         help(__name__)
    #         sys.exit()
    # for flg in ['-nc', '--nocopy']:
    #     if flg in sys.argv:
    #         nocopy = True
    #         break
    #     else:
    #         nocopy = False
    # if '-WD' in sys.argv:
    #     WD = sys.argv[sys.argv.index('-WD')+1]
    # else:
    #     WD = '.'
    # for flg in ['-dx', '--dropbox']:
    #     if flg in sys.argv:
    #         WD = find_dropbox()
    #         print("Top search directory set to Dropbox folder:\n\n%s\n\n"%(WD))
    # if usr_configs_read:
    #     print('-I- Successfully read in user configs and local paths')
    #     WD = data_src
    #     output_path = data_dir
    #     inp_dir = inp_dir

    # print("""\
    # Getting all .inp files with settings:
    #     Top directory: {}
    #     Main data directory: {}
    #     Inp repository: {}
    #     Copy files = {}
    #         """.format(data_src,data_dir,inp_dir,str(not nocopy)))
    get_all_inp_files(data_src, data_dir, inp_dir, nocopy=nocopy)


if __name__ == "__main__":
    main()
