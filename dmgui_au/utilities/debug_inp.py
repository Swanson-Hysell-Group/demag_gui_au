#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NAME:
    debug_inp.py

DESCRIPTION:
    debugs and fixes with user input .inp format files of CIT (sam file) type data.

SYNTAX:
    ~$ python debug_inp.py $INP_FILE

FLAGS:
    -h, --help:
        prints this help message
    -dx, --dropbox:
        Prioritize user's Dropbox folder when searching/debugging sam file paths;
        the module will attempt to locate the Dropbox folder automatically.

    Options to explicitly set value of inp fields:
    --sam_path:
        Path to .sam file

    --magic_codes:
        Magic method codes

    --loc:
        Site description given in .sam file; commonly location

    --nc:
        Naming convention; see docstring for debug_inp function.
        Set to -1 if you are sure you want to change the current value
        but want this module to try to figure out the correct value for you.

        ** WARNING **
        This is not a robust functionality yet; you are safer explicitly
        specifying the value.

    --term:
        Number of terminal characters in sample names (used to define specimens).
        Default is 1

    --no_ave:
        Import all measurements (do not average repeat measurements)

    --peak_AF:
        Peak AF field used in ARM experiments

"""

import sys
import os
import argparse
import textwrap
import pandas as pd
import pmagpy.controlled_vocabularies3 as cv
from functools import reduce
from time import time, asctime
from funcs import shortpath
import pdb

# global top_dir, pkg_dir, data_dir, data_src, inp_dir, usr_configs_read
try:  # get path names if set
    from dmgui_au import pkg_dir, data_dir, data_src, inp_dir
    usr_configs_read = True
except:
    # if setup.py is running, don't issue warning
    if sys.argv[0] != 'setup.py':
        print("-W- Local path names have not been set. Please run setup.py")
    usr_configs_read = False

nc_info_str ="""
Sample naming convention could not be determined. Choose from the list below:

    [1] XXXXY: where XXXX is an arbitrary length site designation and Y
        is the single character sample designation.  e.g., TG001a is the
        first sample from site TG001.    [default]
    [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
    [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
    [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
    [5] site name = sample name
    [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
    [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY

Enter number here: """

class Logger(object):
    """
    log stdout to debug_inp.log
    """
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("debug_inp.log", "a+")
        self.log.write('\n{:-^80}\n\n'.format('  Starting session at {}  '.format(asctime())))

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        pass

def start_logger():
    sys.stdout = Logger()

def stop_logger():
    sys.stdout.log.write('{:-^80}\n'.format('  Closing session  '))
    sys.stdout.log.close()
    sys.stdout = sys.__stdout__

def debug_inp(inp_file, dropbox = False, noinput=False, usr_configs_read=None,
        data_src=None, inp_dir=None, **kwargs):
    """Fixes .inp files

    Parameters
    ----------
    inp_file : filename
        Name of .inp file; can be relative or absolute path.

    data_src : path
        Top-level directory to search for data (for debugging sam paths).
        Defaults to the value provided in dmgui_au.conf, if applicable.

    dropbox : bool, default is False
        When searching for the correct paths to data files,
        prioritize user Dropbox folder. If you have already
        specified your data directory in the global configuration
        (with setup.py) this does nothing. Defaults to False.

    noinput : bool, default is False
        bypass all user input; may result in unresolved issues

    **kwargs : optional
        Manually overwrite certain fields of the .inp file.
        Possible fields are abbreviations of the actual header name,
        as shown in the table below.

        For calculated fields like `nc` and `term`, setting the
        keyword argument to -1 will force these to be recalculated
        by the module. This functionality is still in development,
        so you may prefer to explicitly pass the correct values instead.

        -------------------------------------------------------
        kwargs    -------------->    inp fields
        -------------------------------------------------------
        sam_path                     sam_path
        magic_codes                  field_magic_codes
        loc                          location
        nc                           naming_convention
        term                         num_terminal_char
        no_ave                       dont_average_replicate_measurements
        peak_AF                      peak_AF
        time                         time_stamp

    Returns
    -------
    New .inp file

    """
    inp_directory,inp_file_name = os.path.split(inp_file)
    if inp_directory=='': inp_directory = '.'
    inp_file = os.path.abspath(inp_file)
    print("-I- Running on %s and changing CWD to '%s'" %
          (inp_file_name, shortpath(inp_directory)))
    os.chdir(inp_directory)

    # first deal with any user-specified overrides
    kwarg_map = {
            'sam_path':'sam_path',
            'magic_codes':'field_magic_codes',
            'loc':'location',
            'nc':'naming_convention',
            'term':'num_terminal_char',
            'no_ave':'dont_average_replicate_measurements',
            'peak_AF':'peak_AF',
            'time':'time_stamp'
            }
    force_rewrite_dict = dict.fromkeys(kwarg_map.values())
    for key,value in kwargs.items():
        if key in kwarg_map.keys():
            force_rewrite_dict[kwarg_map[key]] = value
    if any(force_rewrite_dict.values()):
        df = pd.read_csv(inp_file, sep='\t', header=1, dtype=str)
        old_values = {}
        for key, value in force_rewrite_dict.items():
            if value is not None:
                if int(str(value)) == -1:
                    print("\n-I- Resetting {} to NULL...".format(key))
                    old_values[key] = df.ix[0][key]
                    df.ix[0][key]=None
                else:
                    print("\n-I- Setting {} to {}...".format(key, value))
                    # df.ix[0][key]=str(value)
                    # print(df.ix[0][key])
                    df.ix[0][key] = value
        inp_out = open(inp_file, 'w+')
        inp_out.write("CIT\r\n")
        df.to_csv(inp_out, sep="\t", header=True, index=False)
        inp_out.close()

    inpf = open(inp_file,'r')
    inpl = inpf.read().splitlines()
    header,sam_path,name_con,num_term_char = inpl[1].split('\t'),'','',''
    for line in inpl[2:]:
        if len(line.split('\t')) != len(header):
            print("""\
            -E- Some lines in file -- %s -- have different length entries than the header.

                You will have to check this manually as this function is not supported yet. Aborting...
            """%inp_file)
            return
    if inpl[0]=='CIT':
        if 'sam_path' not in header:
            if noinput:
                print("-W- No .sam file name or path in .inp file %s"%inp_file)
            else:
                sam_path = input("No .sam file name or path in .inp file %s, please provide a path: "%inp_file)

        if 'naming_convention' not in header:
            if noinput:
                print('-W- No naming convention in .inp file %s'%inp_file)
            else:
                name_con = input(nc_info_str)

        if 'num_terminal_char' not in header:
            if noinput:
                print("-W- Missing number of terminal characters in .inp file %s"%inp_file)
            else:
                num_term_char = input("""\
                        Missing number of terminal characters that define a specimen.
                        Please enter that number here or press enter to continue with default (=1): """)

    df = pd.read_csv(inp_file, sep='\t', header=1, dtype=str)

    for i in range(len(df.index)):
        if sam_path=='': sam_path = df.ix[i]['sam_path']
        while not os.path.isfile(str(sam_path)):
            directory = os.path.split(str(sam_path))[0]
            sam_file = os.path.split(str(sam_path))[1]
            if dropbox or usr_configs_read:
                if usr_configs_read:
                    search_path = data_src
                elif dropbox:
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
                    search_path = drpbx_path
                for root, dirs, files in os.walk(search_path):
                    if sam_file in files:
                        new_directory=root
                        df.ix[i]['sam_path'] = os.path.join(new_directory,sam_file)
                        sam_path = df['sam_path'].tolist()[0]
                        break
                if os.path.isfile(str(sam_path)):
                    break

            if noinput:
                print("-W- Could not resolve the file path in .inp file %s. Aborting..."%inp_file_name)
                return
            d_or_f = input("The .sam file path in inp_file %s does not exist.\n\n"
                    "Was given directory:\n\n    %s\n\nand file:\n\n    %s\n\n"
                    "Is the [f]ile name or [d]irectory bad? "
                    "If both, correct the file name first. ( [d] / f , or s to skip): "%(inp_file_name,directory,sam_file))
            if d_or_f=='s':
                return
            if d_or_f=='f':
                new_file_name = input("Please input the correct file name for the .sam file: ")
                df['sam_path'] = os.path.join(directory,new_file_name)
            else:
                new_directory = input("If the new directory is known input here. Else just leave blank and the current directory and subdirectories will be searched for file %s and path will be corrected: "%(sam_file))
                if new_directory=='':
                    for root, dirs, files in os.walk(os.getcwd()):
                        if sam_file in files: break
                    new_directory=root
                df.ix[i]['sam_path'] = os.path.join(new_directory,sam_file)
            sam_path = df['sam_path'].tolist()[0]

        vocab = cv.Vocabulary()
        # pdb.set_trace()
        meth_codes, _ = vocab.get_meth_codes()
        if type(meth_codes)==pd.DataFrame:
            meth_codes = meth_codes.index.tolist()
        if meth_codes==None:
            meth_codes = 'FS-FD:FS-H:FS-LOC-GPS:FS-LOC-MAP:SO-POM:SO-ASC:SO-MAG:SO-SUN:SO-SM:SO-SIGHT'.split(':')
        meth_codes_to_keep = []
        for meth_code in df.ix[i]['field_magic_codes'].split(':'):
            if meth_code in meth_codes: meth_codes_to_keep.append(meth_code)
        df.ix[i]['field_magic_codes'] = reduce(lambda x,y: x+':'+y, meth_codes_to_keep)

        sam_contents = open(sam_path, 'r')
        sl = sam_contents.read().splitlines()
        sam_contents.close()
        if 'CIT' not in sl:
            sl = sl[2:]
        else:
            sl = sl[3:]
        if '' in sl:
            sl.remove('')

        nc = df.ix[i]['naming_convention']
        if pd.isna(nc): # force rewrite
            site_name = os.path.basename(os.path.dirname(sam_path))
            if site_name not in sl[0]:
                if noinput:
                    print("-W- Trouble with site name {} -- does not match samples (e.g. {}).".format(site_name,sl[0]))
                    print("-W- Naming convention reset to old value of {}".format(old_values['naming_convention']))
                else:
                    site_name = input("Trouble with site name {} -- does not match samples (e.g. {}).\n"
                            "Input correct site name: ".format(site_name,sl[0]))

            # catch delimeter if it is appended to site name (sometimes the case)
            if not site_name[-1].isalnum():
                if site_name[-1]=='-':
                    nc = int(2)
                elif site_name[-1]=='.':
                    nc = int(3)
            else:
                samp_names = []
                for samp in sl:
                    samp_names.append(samp.partition(site_name)[-1])
                if all([not x[0].isalnum() for x in samp_names]):
                    if all([x[0]=='-' for x in samp_names]):
                        nc = int(2)
                    if all([x[0]=='.' for x in samp_names]):
                        nc = int(3)
            if not pd.isna(nc):
                new_nc = nc
                df.ix[i]['naming_convention']=str(new_nc)
            else:
                if noinput:
                    print("-W- Could not determine correct naming convention...resetting to old value of {}".format(old_values['naming_convention']))
                    nc = old_values['naming_convention']
                    new_nc = nc
                else:
                    nc = input(nc_info_str)
                    new_nc = nc
                df.ix[i]['naming_convention']=str(new_nc)

        if int(nc) > 7 or int(nc) < 1:
            new_nc = input(nc_info_str)
            df.ix[i]['naming_convention']=new_nc

        nt = df.ix[i]['num_terminal_char']
        if pd.isna(nt): # force rewrite
            nt_ctr = 0
            lastchar = pd.Series([t[-1] for t in sl])
            the_rest = pd.Series([t[0:-1] for t in sl])
            # nt_rename_timeout = 0
            while True:
                if len(the_rest)==len(the_rest.unique()) and len(lastchar.unique())<3:
                    try:
                        nt_ctr += 1
                        lastchar = pd.Series([t[-1] for t in the_rest])
                        the_rest = pd.Series([t[0:-1] for t in the_rest])
                    except IndexError:
                        pdb.set_trace()
                else:
                    break
            if noinput:
                try:
                    print("Guessing that the number of terminal "
                          "characters = {}  based on sample names "
                          "like:\n{:^15}{:^15}{:^15}{:^15}".format(nt_ctr, *sl[:4]))
                except IndexError:
                    print("Guessing that the number of terminal characters = {}".format(nt_ctr))
                nt_confirm = ''
            else:
                nt_confirm = input("Guessing that the number of terminal "
                                   "characters = {}  based on sample names "
                                   "like:\n{:^15}{:^15}{:^15}{:^15}\n\nPress "
                                   "enter to confirm or enter the correct number "
                                   "here: ".format(nt_ctr, *sl[:4]))
            if nt_confirm == '':
                new_nt = str(nt_ctr)
            else:
                new_nt = nt_confirm
            df.ix[i]['num_terminal_char'] = new_nt

        # format df for display
        with pd.option_context('display.colheader_justify', 'left', 'display.max_rows', None,
                               'display.max_columns', None, 'display.max_colwidth', -1):
            df_display = df.copy()
            df_display.sam_path = df_display.sam_path.map(shortpath)
            df_display = df_display.T
            df_display.rename(index={'dont_average_replicate_measurements': 'dont_average'},
                              inplace=True)
            print("\n".join([" |  {}".format(i)
                             for i in df_display.to_string(header=False).split("\n")]))

    print("-I- Writing to %s..." % (inp_file_name)+"\n")
    try:
        inp_out = open(inp_file, 'w+')
        inp_out.write("CIT\r\n")
        df.to_csv(inp_out, sep="\t", header=True, index=False)
    except IOError:
        print("-E- Could not write to directory %s, writing to %s instead" %
              (directory, os.path.abspath('.')))
        inp_out = open(os.path.join(os.path.abspath('.'), inp_file_name), 'w+')
        inp_out.write("CIT\r\n")
        df.to_csv(inp_out, sep="\t", header=True, index=False)


def main():
    prog_desc = textwrap.dedent("""\
    debug_inp.py is a debugging script for .inp files (DemagGUI AU). The script
    allows the user to overwrite incorrect values for inp fields (accessed via
    the arguments listed below) and also supports globbing such that multiple
    files can be debugged at a time (see examples below):

           args    -------->    field name in inp file
    -------------------------------------------------------
          -sampath              sam_path
          -magcodes             field_magic_codes
          -nc                   naming_convention
          -term                 num_terminal_char
          -noavg                dont_average_replicate_measurements
          -peakAF               peak_AF

    """)

    # There is limited functionality for auto-debugging some inp fields, namely
    # the `sam_path` field (reliable) and the `naming_convention` and
    # `num_terminal_character` fields (less reliable; in development). If the
    # setup script for demag_gui_au was successfully run, the `sam_path` field in
    # all inp files have already been debugged and should be correct.

    prog_epilog = textwrap.dedent("""\

    Examples
    --------
    For a set of inp files 'Z01.inp', 'Z02.inp', [...] , 'Z160.inp', etc.,
    change the naming convention to 3 and the number of terminal characters to 1:

        $ debug_inp.py Z* -nc 3 -term 1

    The particular glob needed will depend on other file names within the
    directory. In the example above, if you had another group of files
    'ZF10.inp', 'ZF20.inp', etc., you might exclude this second set by requiring
    that 'Z' is always followed by a number:

        $ debug_inp.py Z[0-9]* -nc 3 -term 1


    """)

    global data_src, inp_dir, usr_configs_read
    if usr_configs_read:
        dsrc_default = data_src
    else:
        dsrc_default = None
    parser = argparse.ArgumentParser(prog="debug_inp.py",
                                     description=prog_desc,
                                     epilog=prog_epilog,
                                     add_help=False,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    helpers = parser.add_argument_group('HELP')
    helpers.add_argument('-h', action='help',
                         help='show short help message')
    helpers.add_argument('--help', dest='help_long', action='store_const',
                         const=True, help='show detailed help and usage manual')
    data_setup = parser.add_argument_group('MAIN')
    data_setup.add_argument('inp_file', nargs='*')
    data_setup.add_argument('-datasrc', dest='data_src',
                            help="""Top-level directory to search for data (for
                            debugging sam paths).""", metavar='',
                            default=dsrc_default)
    inp_fields = parser.add_argument_group('INP FIELDS')
    inp_fields.add_argument('-sampath', dest='sam_path',
                            help="""path to the corresponding .sam file (CIT
                            format)""", metavar='')
    inp_fields.add_argument('-magcodes', dest='magic_codes',
                            help='MagIC method codes', metavar='')
    inp_fields.add_argument('-nc', dest='nc',
                            help="""site+sample naming convention (see --help
                            for chart)""", metavar='')
    inp_fields.add_argument('-term', dest='term',
                            help="""number of terminal characters that
                            distinguish specimen from sample.""", metavar='')
    inp_fields.add_argument('-noavg', dest='no_ave', type=bool,
                            help="""if True (default), import all repeat
                            measurements (do not average them).""", metavar='')
    inp_fields.add_argument('-peakAF', dest='peak_AF', metavar='')
    other_flags = parser.add_argument_group('OTHER FLAGS')
    other_flags.add_argument('--noinput', action='store_true',
                             help="""bypass all prompts for user input; may
                             result in unresolved issues""")
    # parser.add_argument('-datasrc', dest='data_src',
    #                     help="""Top-level directory to search for data (for
    #                     debugging sam paths).  Defaults to the value provided in
    #                     dmgui_au.conf, if configured.""")
    # parser.add_argument('-nc', dest='nc',
    #                     help="""site+sample naming convention (use --help to see
    #                     chart of all naming conventions recognized for CIT/MagIC
    #                     conversion)""")
    # parser.add_argument('-term', dest='term', help="""number of terminal
    #         characters that distinguish different specimens of the same sample.
    #         For example, the two specimens 'PI47-1a' and 'PI47-1b'---both from
    #         the same sample 'PI47-1'---are distinguished by a single terminal
    #         character (either 'a' or 'b') so that `term_chars` should be set to 1.
    #         """)
    # parser.add_argument('-noavg', dest='no_ave', type=bool,
    #                     help="""if True (default), do not average measurements
    #                     made at the same treatment level; instead, import all
    #                     duplicate measurements individually. If False, all repeat
    #                     measurements will be averaged (beware: this will include faulty
    #                     measurements unless these have been filtered via some
    #                     other method).""")
    # parser.add_argument('--dropbox', action='store_true', default=False)
    args = vars(parser.parse_args())
    if args['help_long']:
        help(__name__)
        sys.exit()
    start_logger()
    inp_file_list = args.pop('inp_file')
    for filename_inp in inp_file_list:
        if not usr_configs_read:
            data_src, inp_dir = None, None, None

        if "~" in filename_inp:
            filename_inp = os.path.expanduser(filename_inp)
        if not os.path.isfile(filename_inp):
            if usr_configs_read:
                print('-I- Successfully read in user configs and local paths')
                if os.path.isfile(os.path.join(inp_dir, os.path.basename(filename_inp))):
                    filename_inp = os.path.abspath(os.path.join(inp_dir,
                                                                os.path.basename(filename_inp)))
            else:
                print("-E- %s is not a valid file path, aborting" % filename_inp)
                return
        debug_inp(
            filename_inp,
            usr_configs_read=usr_configs_read,
            inp_dir=inp_dir,
            **args)
    stop_logger()


if __name__ == "__main__":
    main()
