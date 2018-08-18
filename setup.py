#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import shutil
import configparser
import argparse
from contextlib import ContextDecorator
from time import asctime
import traceback
# from setuptools import setup, find_packages
from dmgui_au.utilities import find_dropbox, shortpath, get_all_inp_files, debug_inp



class Logger(object):
    """
    Logger that redirects all standard output and any unhandled exceptions to file
    `setup.log`. It will also return output to the terminal by default, unless
    the --quiet option was specified during setup.
    """
    # define colors for output to terminal
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    def __init__(self, show=None, clr_output=True):
        self.clr_output = clr_output
        self.terminal = sys.stdout
        self.log = open("setup.log", "w+")
        self.log.write('\n{:-^80}\n\n'.format('  Started setup at {}  '.format(asctime())))
        # the show attribute was meant to trim the terminal output to a more
        # reasonable length, although it didn't really help at all in the end
        # and isn't useful enough to keep in
        #
        # if isinstance(show, str):
        #     self.show = [show]
        # else:
        #     self.show = show

    def write(self, message):
        if self.clr_output:
            if '---' in str(message):
                self.terminal.write(BOLD)
            elif '-I-' in str(message):
                self.terminal.write(OKGREEN)
            elif '-W-' in str(message):
                self.terminal.write(WARNING)
            elif '-E-' in str(message):
                self.terminal.write(FAIL)
            elif str(message).startswith(' | '):
                # msg_filt = filter(lambda x: any([y in x for y in self.show]),
                #                   str(message).splitlines())
                # message = "\n".join(msg_filt)
                self.terminal.write(OKBLUE)
        self.terminal.write(message)
        if self.clr_output:
            self.terminal.write(ENDC)
        self.log.write(message)

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass


class loggercontext(ContextDecorator):
    def __init__(self, show=None):
        self.show = show

    def __enter__(self, show=None):
        start_logger(show=self.show)
        return self

    def __exit__(self, *exc):
        stop_logger(*exc)
        return False


def start_logger(show=None):
    sys.stdout = Logger(show=show)


def stop_logger(*exc):
    if not any(exc):
        sys.stdout.log.write(
            '{:-^80}\n'.format('  Setup finished successfully at {}  '.format(asctime())))
    else:
        sys.stdout.write('-E- Setup failed! Aborting...\n')
        sys.stdout.log.write('-E- The following error occurred:\n' +
                             ''.join(traceback.format_exception(*exc)))
    sys.stdout.log.close()
    sys.stdout = sys.__stdout__


def setup_dirs_and_files(dropbox=False):
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
    pkg_dir = os.path.join(top_dir, 'dmgui_au')
    configfile = os.path.join(pkg_dir, "dmgui_au.conf")
    if os.path.isfile(configfile):
        rewrite = input("Configuration file 'dmgui_au.conf' already exists. Overwrite? (y/[n]) ")
        # TODO: Need to handle the case where configs have already been set, but
        # user still wants to continue with the rest of the setup <08-17-18, Luke Fairchild> #
        if rewrite == "y":
            pass
        else:
            print("-I- Quitting...")
            sys.exit()
    # find main data directory
    data_src = ''
    if dropbox:
        data_src = find_dropbox()
    if not data_src:
        print("Enter directory (absolute path) to search for data files ([Enter] to abort):")
        while not os.path.exists(data_src):
            data_src = input("> ")
            if not data_src:
                print("-E- Could not find a valid path for data source. Aborting...")
                return
            if "~" in data_src:
                data_src = os.path.expanduser(data_src)
            if not os.path.exists(data_src):
                print("%s not a valid path!" % (data_src))

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
        "", "Package configuration values written to dmgui_au.conf", ""))
    for vals in (
            ("Base path to search for data files:", shortpath(data_src)),
            ("MagIC file output directory:", shortpath(data_dir)),
            ("INP directory:", shortpath(inp_dir))):
        print('{0:<35} {1:<45}'.format(*vals))
    print('')
    print('-I- Copying .inp files into data directory...')
    fileno = get_all_inp_files(data_src, data_dir, inp_dir, nocopy=False)
    print('-I- {} files copied!'.format(len(fileno)))

    print("-I- Validating path names and structure of .inp files. This is no "
          "guarantee that the contents are sufficiently correct for the program "
          "to read and properly format data files. Use the debugging script "
          "'debug_inp.py' if there are issues.")

    for i in os.listdir(inp_dir):
        debug_inp(os.path.join(inp_dir, i), noinput=True, usr_configs_read=True,
                  data_src=data_src, data_dir=data_dir, inp_dir=inp_dir)


def main():
    parser = argparse.ArgumentParser(description="Setup script for Demag GUI Autoupdate Package")
    # parser.add_argument('-h', '--help', action='help', help='show this help message')
    run_or_clean = parser.add_subparsers()
    run = run_or_clean.add_parser()
    # run = parser.add_argument_group()
    run.add_argument('dropbox', action='store_true',
                     help="""Set this option if main data directory is within a local
                     Dropbox folder. This script should then configure path
                     names for the package automatically""")
    clean = run_or_clean.add_parser("Other")
    # clean = parser.add_argument_group("Other functions")
    clean.add_argument('clean', action='store_true',
                       help="""Clear the configurations from a previous setup
                       and remove all data files in this package""")
    # subparsers = parser.add_subparsers(help='sub-command help')

    # subparsers = parser.add_subparsers(title='subcommands',
    #                                description='valid subcommands',
    #                                help='additional help')
    args = vars(parser.parse_args())
    if args['clean']:
        top_dir = os.path.abspath(os.path.dirname(__file__))
        shutil.rmtree(os.path.join(top_dir, 'data'))
        os.remove(os.path.join(top_dir, "dmgui_au", "dmgui_au.conf"))
        os.remove(os.path.join(top_dir, "setup.log"))
        sys.exit()
    with loggercontext(show=['sam_path', 'naming_convention', 'num_terminal_char']):
        setup_dirs_and_files(args['dropbox'])


if __name__ == "__main__":
    main()
