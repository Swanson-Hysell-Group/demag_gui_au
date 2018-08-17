#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import shutil
from setuptools import setup, find_packages
from dmgui_au.utilities import find_dropbox,shortpath,get_all_inp_files,debug_inp
import configparser
from contextlib import ContextDecorator
from time import asctime
import traceback

"""
TODO:
    script currently only takes care of assigning global pathnames used by the dmgui_au package
    It should eventually implement:
        1) get_all_inp_files
        2) debug all inp file paths (and possibly other values if user chooses)

        possible future additions
        3) most recently read files
        4) most recently edited files
            (stream data from magnetometer; referred to in demag_gui_au as 'go live')

"""

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Logger(object):
    """
    log stdout to debug_inp.log
    """
    def __init__(self, show = None, clr_output=True):
        if type(show) is str:
            self.show = [show]
        else:
            self.show = show
        self.clr_output = clr_output
        self.terminal = sys.stdout
        self.log = open("setup.log", "w+")
        self.log.write('\n{:-^80}\n\n'.format('  Started setup at {}  '.format(asctime())))

    def write(self, message):
        if self.clr_output:
            if '---' in str(message):
                self.terminal.write(bcolors.BOLD)
            elif '-I-' in str(message):
                if 'Timer' in str(message):
                    self.terminal.write(bcolors.OKBLUE)
                else:
                    self.terminal.write(bcolors.OKGREEN)
            elif '-W-' in str(message):
                self.terminal.write(bcolors.WARNING)
            elif '-E-' in str(message):
                self.terminal.write(bcolors.FAIL)
            elif str(message).startswith(' | '):
                msg_filt = filter(lambda x: any([y in x for y in self.show]),
                        str(message).splitlines())
                self.terminal.write(bcolors.OKBLUE)
                message = "\n".join(msg_filt)
        self.terminal.write(message)
        if self.clr_output:
            self.terminal.write(bcolors.ENDC)
        self.log.write(message)

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        pass

def start_logger(show=None):
    sys.stdout = Logger(show=show)

def stop_logger(*exc):
    if not any(exc):
        sys.stdout.log.write('{:-^80}\n'.format('  Setup finished successfully at {}  '.format(asctime())))
    else:
        sys.stdout.write('-E- Setup failed! Aborting...\n')
        sys.stdout.log.write('-E- The following error occurred:\n'+
                ''.join(traceback.format_exception(*exc)))
    sys.stdout.log.close()
    sys.stdout = sys.__stdout__

class loggercontext(ContextDecorator):
    def __init__(self, show=None):
        self.show = show

    def __enter__(self, show=None):
        start_logger(show=self.show)
        return self

    def __exit__(self, *exc):
        stop_logger(*exc)
        return False

def main(dropbox=False):
    """
    Parameters
    ----------
    dropbox : bool, optional

    Returns
    -------
    local paths to configure Demag GUI Autoupdate

    """
    # check if file already exists
    top_dir = os.path.abspath(os.path.dirname(__file__))
    pkg_dir = os.path.join(top_dir,'dmgui_au')
    configfile = os.path.join(pkg_dir, "dmgui_au.conf")
    if os.path.isfile(configfile):
        rewrite = input("Configuration file 'dmgui_au.conf' already exists. Overwrite? (y/[n]) ")
        if rewrite=="y":
            pass
        else:
            print("Quitting..."); sys.exit()
    # find main data directory
    data_src = ''
    if dropbox:
        data_src = find_dropbox()
    else:
        print("Enter directory (absolute path) to search for data files:")
        while not os.path.exists(data_src):
            data_src = input("> ")
            if "~" in data_src:
                data_src = os.path.expanduser(data_src)
            if not os.path.exists(data_src):
                print("%s not a valid path!"%(data_src))

    data_dir = os.path.join(top_dir, "data")
    inp_dir = os.path.join(data_dir, "inp_files")
    # make data directory tree if it does not exist
    if not os.path.exists(data_dir):
        os.makedirs(inp_dir)
    config = configparser.ConfigParser()
    config['PathNames'] = {'top_dir': top_dir, 'pkg_dir': pkg_dir,
            'data_src': data_src, 'data_dir': data_dir, 'inp_dir': inp_dir}
    with open(configfile, "w") as confs:
        config.write(confs)
    print("{:-^80}\n{:^80}\n{:-^80}".format(
        "","Package configuration values written to dmgui_au.conf", ""))
    for vals in (
            ("Base path to search for data files:", shortpath(data_src)),
            ("MagIC file output directory:", shortpath(data_dir)),
            ("INP directory:", shortpath(inp_dir))):
        print('{0:<35} {1:<45}'.format(*vals))
    print('')
    print('-I- Copying .inp files into data directory...')
    fileno = get_all_inp_files(data_src, data_dir, inp_dir, nocopy = False)
    print('-I- {} files copied!'.format(len(fileno)))
    print('-I- Fixing .sam paths...files might require further debugging (see debug_inp.py)')
    for i in os.listdir(inp_dir):
        debug_inp(os.path.join(inp_dir,i), noinput=True, usr_configs_read=True,
                data_src=data_src, data_dir=data_dir, inp_dir=inp_dir)

if __name__ == "__main__":
    if "clean" in sys.argv:
        try:
            top_dir = os.path.abspath(os.path.dirname(__file__))
            shutil.rmtree(os.path.join(top_dir,'data'))
            os.remove(os.path.join(top_dir, "dmgui_au", "dmgui_au.conf"))
            os.remove(os.path.join(top_dir, "setup.log"))
        except:
            pass
        sys.exit()
    if "dropbox" in sys.argv:
        dropbox=True
    with loggercontext(show=['sam_path', 'naming_convention','num_terminal_char']):
        main(dropbox)

