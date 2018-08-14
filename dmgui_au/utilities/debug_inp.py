#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NAME:
    debug_inp

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

import sys,os
import pandas as pd
import numpy as np
import pmagpy.controlled_vocabularies2 as cv2
import pmagpy.controlled_vocabularies3 as cv
from functools import reduce
import pdb

global data_dir, inp_dir, data_output_path, usr_configs_read
try: # get path names if set
    import dmgui_au.config.user as user
    path_conf = user.demaggui_user
    data_dir = path_conf['data_dir']
    inp_dir = path_conf['inp_dir']
    data_output_path = path_conf['magic_out']
    usr_configs_read = True
except:
    warnings.warn("Local paths used by this package have not been defined; please run the script setup.py")
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

def shortpath(abspath):
    return abspath.replace(os.path.expanduser('~') + os.sep, '~/', 1)

def debug_inp(inp_file, drpbx = False, **kwargs):

    """Fixes .inp files

    Parameters
    ----------
    inp_file : filename
        Name of .inp file; can be relative or absolute path.

    drpbx : bool, optional
        When searching for the correct paths to data files,
        prioritize user Dropbox folder. If you have already
        specified your data directory in the global configuration
        (with setup.py) this does nothing.

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
    global data_dir, inp_dir, data_output_path, usr_configs_read

    if "~" in inp_file: inp_file = os.path.expanduser(inp_file)
    if not os.path.isfile(inp_file):
        if usr_configs_read:
            if os.path.isfile(os.path.join(inp_dir,os.path.basename(inp_file))):
                inp_file = os.path.abspath(os.path.join(inp_dir,os.path.basename(inp_file)))
        else:
            print("%s is not a valid file path, aborting"%inp_file); return
    inp_directory,inp_file_name = os.path.split(inp_file)
    if inp_directory=='': inp_directory = '.'
    inp_file = os.path.abspath(inp_file)
    print("Running on %s and changing CWD to %s\n"%(inp_file_name,inp_directory))
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
        for key, value in force_rewrite_dict.items():
            if value is not None:
                if int(value) == -1:
                    print("\n----> Resetting {} to NULL...".format(key))
                    df.ix[0][key]=None
                else:
                    print("\n----> Setting {} to {}...".format(key, value))
                    df.ix[0][key]=str(value)
        inp_out = open(inp_file, 'w+')
        inp_out.write("CIT\r\n")
        df.to_csv(inp_out, sep="\t", header=True, index=False)
        inp_out.close()

    inpf = open(inp_file,'r')
    inpl = inpf.read().splitlines()
    header,sam_path,name_con,num_term_char = inpl[1].split('\t'),'','',''
    for line in inpl[2:]:
        if len(line.split('\t')) != len(header):
            print("""
            Some lines in file -- %s -- have different length entries than the header.

            You will have to check this manually as this function is not supported yet. Aborting...

            """%inp_file)
            return
    if inpl[0]=='CIT':
        if 'sam_path' not in header:
            sam_path = input("No .sam file name or path in .inp file %s, please provide a path: ")

        # TODO: Automate nc fix if 'force_rewrite' argument given
        # <08-08-18, Luke Fairchild> #

        if 'naming_convention' not in header:
            name_con = input(nc_info_str)

        if 'num_terminal_char' not in header:
            num_term_char = input("""
Missing number of terminal characters that define a specimen.
Please enter that number here or press enter to continue with default (=1): """)

    df = pd.read_csv(inp_file, sep='\t', header=1, dtype=str)

    for i in range(len(df.index)):
        if sam_path=='': sam_path = df.ix[i]['sam_path']
        while not os.path.isfile(str(sam_path)):
            directory = os.path.split(str(sam_path))[0]
            sam_file = os.path.split(str(sam_path))[1]
            if drpbx or usr_configs_read:
                if usr_configs_read:
                    search_path = data_dir
                elif drpbx:
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

            d_or_f = input("The .sam file path in inp_file %s does not exist.\n\n"
                    "Was given directory:\n\n    %s\n\nand file:\n\n    %s\n\n"
                    "Is the [f]ile name or [d]irectory bad? "
                    "If both, correct the file name first. ([d]/f): "%(inp_file_name,directory,sam_file))
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

        nc = df.ix[i]['naming_convention']
        if pd.isna(nc): # force rewrite
            site_name = os.path.basename(os.path.dirname(sam_path))

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
                nc = input(nc_info_str)
                new_nc = nc
                df.ix[i]['naming_convention']=str(new_nc)

        if nc > 7 or nc < 1:
            new_nc = input(nc_info_str)
            df.ix[i]['naming_convention']=new_nc

        nt = df.ix[i]['num_terminal_char']
        if pd.isna(nt): # force rewrite
            nt_ctr = 0
            lastchar = pd.Series([t[-1] for t in sl])
            the_rest = pd.Series([t[0:-1] for t in sl])
            while True:
                if len(the_rest)==len(the_rest.unique()) and len(lastchar.unique())<3:
                    nt_ctr += 1
                    lastchar = pd.Series([t[-1] for t in the_rest])
                    the_rest = pd.Series([t[0:-1] for t in the_rest])
                else:
                    break
            nt_confirm = input("Guessing that the number of terminal characters is {}.\nPress enter to confirm or enter the correct number here: ".format(nt_ctr))
            if nt_confirm=='':
                new_nt = str(nt_ctr)
            else:
                new_nt = nt_confirm
            df.ix[i]['num_terminal_char'] = new_nt

        # switch to short path for display
        df_display = df.copy()
        df_display.sam_path = df_display.sam_path.map(shortpath)
        with pd.option_context('display.max_rows', None,
                'display.max_columns', None, 'display.max_colwidth', int(1.2*len(df_display.sam_path.max()))):
            print(df_display.transpose())

    print("\nWriting fixed data back to %s"%(inp_file_name))
    try:
        inp_out = open(inp_file, 'w+')
        inp_out.write("CIT\r\n")
        df.to_csv(inp_out, sep="\t", header=True, index=False)
    except IOError:
        print("Could not write to directory %s, writing to %s instead"%(directory,os.path.abspath('.')))
        inp_out = open(os.path.join(os.path.abspath('.'),inp_file_name), 'w+')
        inp_out.write("CIT\r\n")
        df.to_csv(inp_out, sep="\t", header=True, index=False)

if __name__=="__main__":
    kwargs = {}
    for flg in ['-h', '--help']:
        if flg in sys.argv:
            help(main); sys.exit()
    for flg in ['-dx', '--dropbox']:
        if flg in sys.argv:
            dropbox = True
            break
        else:
            dropbox = False

    if '--sam_path' in sys.argv:
        idx = sys.argv.index('--sam_path')
        kwargs['sam_path'] = sys.argv[idx+1]
    if '--magic_codes' in sys.argv:
        idx = sys.argv.index('--magic_codes')
        kwargs['magic_codes'] = sys.argv[idx+1]
    if '--loc' in sys.argv:
        idx = sys.argv.index('--loc')
        kwargs['loc'] = sys.argv[idx+1]
    if '--nc' in sys.argv:
        idx = sys.argv.index('--nc')
        kwargs['nc'] = sys.argv[idx+1]
    if '--term' in sys.argv:
        idx = sys.argv.index('--term')
        kwargs['term'] = sys.argv[idx+1]
    if '--no_ave' in sys.argv:
        idx = sys.argv.index('--no_ave')
        kwargs['no_ave'] = sys.argv[idx+1]
    if '--peak_AF' in sys.argv:
        idx = sys.argv.index('--peak_AF')
        kwargs['peak_AF'] = sys.argv[idx+1]

    if len(sys.argv)==1:
        print("program needs a .inp file to debug, aborting"); sys.exit()
    # print("Running with options drpbx={}, force_rewrite_sam_path = {}, force_rewrite_nc = {}".format(dropbox,fs,fn))
    debug_inp(sys.argv[1], drpbx=dropbox, **kwargs)
