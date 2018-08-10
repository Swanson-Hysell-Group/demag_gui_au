#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys,os
import pandas as pd
import pmagpy.controlled_vocabularies2 as cv
from functools import reduce

def main(inp_file, drpbx = False, force_rewrite_sam_path = None, force_rewrite_nc = None, force_rewrite_tc = None):
    """
    debugs and fixes with user input .inp format files of CIT (sam file) type data.

    SYNTAX:
        ~$ python debug_inp.py $INP_FILE

    FLAGS:
        -h, --help:
            prints this help message
        -dx, --dropbox:
            Prioritize user's Dropbox folder when searching/debugging sam file paths;
            the module will attempt to locate the Dropbox folder automatically.
        -fs, --force_rewrite_sam_path STR:
            forcibly rewrite the path to the .sam file
        -fn, --force_rewrite_nc INT:
            Forcibly overwrite the naming convention of the .inp file.
            Argument should be a number according to the MagIC convention given below:

            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name = sample name
            [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY


    """
    if not os.path.isfile(inp_file):
        print("%s is not a valid file path, aborting"%inp_file); return
    inp_directory,inp_file_name = os.path.split(inp_file)
    if inp_directory=='': inp_directory = '.'
    inp_file = os.path.abspath(inp_file)
    print("Running on %s and changing cwd to %s\n"%(inp_file_name,inp_directory))
    os.chdir(inp_directory)

    inpf = open(inp_file,'r')
    inpl = inpf.read().splitlines()
    header,sam_path,name_con,num_term_char = inpl[1].split('\t'),'','',''
    for line in inpl[2:]:
        if len(line.split('\t')) != len(header):
            print("\nPlease check file %s --- some lines have different length entries than the header.\n\n"
            "You will have to check this manually as this function is not supported yet. Aborting..."%inp_file)
            return
    # if inpl[0]=='CIT' and not all([h in header for h in ['sam_path','naming_convention','num_terminal_char']]):
    if inpl[0]=='CIT':
        if 'sam_path' not in header:
            sam_path = input("No .sam file name or path in .inp file %s, please provide a path: ")

        # TODO: Automate nc fix if 'force_rewrite' argument given
        # <08-08-18, Luke Fairchild> #

        if 'naming_convention' not in header:
            name_con = input("""
            No sample naming convention specified. Choose from the list below:

            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name = sample name
            [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY

            Enter number here: """)

        num_term_char = 1

        # if 'num_terminal_char' not in header:
        # num_term_char = input("Missing number of terminal characters that define a specimen, default is 0. Please enter that number here: ")

    df = pd.read_csv(inp_file, sep='\t', header=1, dtype=str)

    for i in range(len(df.index)):
        if sam_path=='': sam_path = df.ix[i]['sam_path']
        while not os.path.isfile(str(sam_path)):
            directory = os.path.split(str(sam_path))[0]
            sam_file = os.path.split(str(sam_path))[1]
            if drpbx:
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
                for root, dirs, files in os.walk(drpbx_path):
                    if sam_file in files:
                        new_directory=root
                        df.ix[i]['sam_path'] = os.path.join(new_directory,sam_file)
                        sam_path = df['sam_path'].tolist()[0]
                        break
                if os.path.isfile(str(sam_path)):
                    break
                    # print("The file %s could not be found in the Dropbox directory: \n\n%s\n\nYou will have to fix this manually..."%(sam_file,drpbx_path))

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
        meth_codes = vocab.get_meth_codes()
        if meth_codes==None:
            meth_codes = 'FS-FD:FS-H:FS-LOC-GPS:FS-LOC-MAP:SO-POM:SO-ASC:SO-MAG:SO-SUN:SO-SM:SO-SIGHT'.split(':')
        meth_codes_to_keep = []
        for meth_code in df.ix[i]['field_magic_codes'].split(':'):
            if meth_code in meth_codes: meth_codes_to_keep.append(meth_code)
        df.ix[i]['field_magic_codes'] = reduce(lambda x,y: x+':'+y, meth_codes_to_keep)

        nc = int(df.ix[i]['naming_convention'].split('-')[0])
        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     print(df.transpose())
        if nc > 7 or nc < 1:
            new_nc = input(""".inp file %s has invalid naming convention for .sam file %s please choose from the naming conventions below:

        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY

enter naming convention here: """)
            df.ix[i]['naming_convention']=new_nc
        if force_rewrite_nc is not None:
            print("\n----> Setting naming convention to %s..."%(str(force_rewrite_nc)))
            df.ix[i]['naming_convention']=str(force_rewrite_nc)
            print("----> Setting number of terminal characters to %s..."%(str(num_term_char)))
            df.ix[i]['num_terminal_char']=str(num_term_char)

        with pd.option_context('display.max_rows', None, 'display.max_columns', None):
            print(df.transpose())

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
    for flg in ['-h', '--help']:
        if flg in sys.argv:
            help(main); sys.exit()
    for flg in ['-dx', '--dropbox']:
        if flg in sys.argv:
            dropbox = True
            sys.argv.remove(flg)
            break
        else:
            dropbox = False
    for flg in ['-fs', '--force_rewrite_sam_path']:
        if flg in sys.argv:
            fs = sys.argv[sys.argv.index(flg)+1]
            sys.argv.remove(fs)
            sys.argv.remove(flg)
            break
        else:
            fs = None
    for flg in ['-fn', '--force_rewrite_nc']:
        if flg in sys.argv:
            fn = sys.argv[sys.argv.index(flg)+1]
            sys.argv.remove(fn)
            sys.argv.remove(flg)
            break
        else:
            fn = None
    if len(sys.argv)==1:
        print("program needs a .inp file to debug, aborting"); sys.exit()
    # print("Running with options drpbx={}, force_rewrite_sam_path = {}, force_rewrite_nc = {}".format(dropbox,fs,fn))
    main(sys.argv[1], drpbx=dropbox, force_rewrite_sam_path = fs, force_rewrite_nc = fn)
