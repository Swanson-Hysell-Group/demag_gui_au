#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""setup.py

This is a basic setup script for Demag GUI Autoupdate. It functions mainly to
resolve path names to the data files on your machine (saved to dmgui_au.conf)
and retrieve data from the *.inp files of data directories. These files contain
site-specific information that allow the GUI to convert these data to
MagIC-formatted files (written locally to the data repository of this package,
'demag_gui_au/data') and monitor changes to the original remote directories in
order to update the local MagIC files whenever new data becomes available.


Usage
-----
The setup script can simply be run by::

    $ python setup.py [--quiet]

The optional ``quiet`` flag will limit printed messages to headings, warnings
and errors (all messages will still be written to ``setup.log``). If your local
data files are synced by Dropbox, this script can find this location
automatically with the additional 'dropbox' flag::

    $ python setup.py dropbox [--quiet]

The ``clean`` sub-command will clear the output of the output configuration file
``dmgui_au.conf``. The ``--all`` option will also wipe the entire ``data``
directory created by this script (see *Output* section)::

    $ python setup.py clean [--all]


Output
-------
If not previously run, the script will create the ``data`` directory tree within
the top level of the ``demag_gui_au`` directory. All ``*.inp`` files found will
be copied to ``data/inp_files`` with a composite record of these files output to
``all_inp_files.txt``. Path names will be stored within the INI-style
configuration file ``dmgui_au.conf``. A full log for the script is written to
``setup.log``.

demag_gui_au/
├── data
│   ├── all_inp_files.txt
│   └── inp_files
├── dmgui_au
│   └── dmgui_au.conf
├── setup.log
└── setup.py

The original directory structure can be reset with the ``clean --all`` option.


"""

import sys
import os
import shutil
import configparser
# import argparse
from contextlib import ContextDecorator
from time import asctime
import traceback
# from setuptools import setup, find_packages
from dmgui_au.utilities import find_dropbox, shortpath, get_all_inp_files, debug_inp


# define colors for output to terminal
class logclr:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class Logger(object):
    """
    Logger that redirects all standard output and any unhandled exceptions to file
    `setup.log`. It will also return output to the terminal by default, unless
    the --quiet option was specified during setup.
    """

    def __init__(self, show=None, quiet=False, clr_output=True):
        self.quiet = quiet
        self.clr_output = clr_output
        self.terminal = sys.stdout
        self.quiet_count = 0
        self.log = open("setup.log", "w+")
        self.log.write('\n{:-^80}\n\n'.format('  Started setup at {}  '.format(asctime())))
        self.msg_to_term = True  # send output at start, even if --quiet

    def write(self, message):
        """main write method for redirection of sys.stdout"""
        # first classify the message content to determine whether it should be
        # written to the console in addition to being logged
        if self.msg_to_term or "-W-" in str(message) or "-E-" in str(message):
            # should always evaluate True if quiet==False; if quiet==True,
            # should only evaluate True when printing initial messages during
            # file copy and during warnings/errors
            self.msg_to_term = self.msg_type(message)
        self.log.write(message)

    def msg_type(self, message):
        """classify the message and color output to console"""
        msg_lvl = 0
        # if self.clr_output:
        if '---' in str(message):
            self.terminal.write(logclr.BOLD)
            msg_lvl = 1
        elif '-E-' in str(message):
            self.terminal.write(logclr.FAIL)
            msg_lvl = 2
        elif '-W-' in str(message):
            self.terminal.write(logclr.WARNING)
            msg_lvl = 3
        elif '-I-' in str(message):
            self.terminal.write(logclr.OKGREEN)
            # filter out debug_inp messages if quiet
            if any([x in str(message) for x in ('Running', 'Writing')]):
                msg_lvl = 5
            else:
                msg_lvl = 4
        elif str(message).startswith(' | '):
            self.terminal.write(logclr.OKBLUE)
            msg_lvl = 6
        if self.quiet:
            if msg_lvl < 5:
                self.terminal.write(message)
            else:
                return False
        else:
            self.terminal.write(message)
        self.terminal.write(logclr.ENDC)
        return True

    def flush(self):
        self.terminal.flush()

        # self.terminal.flush()

                # msg_filt = filter(lambda x: any([y in x for y in self.show]),
                #                   str(message).splitlines())
                # message = "\n".join(msg_filt)
                # if not self.quiet:
                #     self.terminal.write(new_msg)
                # msg_lvl = 5
            # self.terminal.write(str(message))
        # if not self.quiet or msg_lvl < 5:
        #     self.terminal.write(message)
        #     if self.clr_output:
        #         self.terminal.write(logclr.ENDC)
        # else:
        #     self.terminal.write(str(self.dbcounter))
        #     self.dbcounter += 1



class loggercontext(ContextDecorator):
    def __init__(self, show=None, quiet=False):
        self.show = show
        self.quiet = quiet

    def __enter__(self, show=None):
        start_logger(show=self.show, quiet=self.quiet)
        return self

    def __exit__(self, *exc):
        stop_logger(*exc)
        return False


def start_logger(show=None, quiet=False):
    sys.stdout = Logger(show=show, quiet=quiet)


def stop_logger(*exc):
    if not any(exc):
        sys.stdout.log.write(
            '{:-^80}\n'.format('  Setup finished successfully at {}  '.format(asctime())))
        finished=True
    elif exc[0] is SystemExit:
        finished=False
        pass
    else:
        sys.stdout.write('-E- Setup failed! Aborting...\n')
        sys.stdout.log.write('-E- The following error occurred:\n' +
                             ''.join(traceback.format_exception(*exc)))
        finished=False
    sys.stdout.log.close()
    sys.stdout = sys.__stdout__
    if finished:
        print("Setup finished! Full record written to setup.log")


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
        print("-W- Configuration file 'dmgui_au.conf' already exists. Overwrite? (y/[n]) ")
        rewrite = sys.stdin.readline()
        # TODO: Need to handle the case where configs have already been set, but
        # user still wants to continue with the rest of the setup <08-17-18, Luke Fairchild> #
        if rewrite.strip().lower() in "yes":
            pass
        else:
            print("-W- Quitting...")
            sys.exit()
    # find main data directory
    data_src = ''
    if dropbox:
        data_src = find_dropbox()
    if not data_src:
        while not os.path.exists(data_src):
            print("Enter directory (absolute path) to search for data files ([Enter] to abort):")
            data_src = sys.stdin.readline().strip()
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
    print("{:-^80}\n{:^80}\n{:-^80}\n".format(
        "", "Package configuration values written to dmgui_au.conf", ""), end="\n")
    for vals in (("Base path to search for data files:", shortpath(data_src)),
                 ("MagIC file output directory:", shortpath(data_dir)),
                 ("INP directory:", shortpath(inp_dir))):
        print('{0:<35} {1:<45}'.format(*vals))
    print('')
    print('-I- Finding .inp files...')
    fileno = get_all_inp_files(data_src, data_dir, inp_dir, nocopy=False)
    print("-I- {} files found! All files copied to 'data/inp_files'".format(len(fileno)))

    print("-I- Validating path names and structure of .inp files...")
    # debug_auto = """
    # Other values might not be
    # correct and the program to read and properly format data files. The provided
    # debugging script 'debug_inp.py' can be used to replace incorrect values
    # within individual .inp files as specified by the user. However, there is
    # some functionality for bulk debugging the 'naming convention' and 'number of
    # terminal characters' fields for CIT files. CAUTION: this is in active
    # development and experimental.
    # """
    # print("-W- This fixes the path names only. {}".format(debug_auto.ljust(4)))
    # print("Use this now? (y/[n]): ")
    # debug_now = sys.stdin.readline()
    # if debug_now.strip().lower() in "yes":
    #     for i in os.listdir(inp_dir):
    #         debug_inp(os.path.join(inp_dir, i), noinput=True, usr_configs_read=True,
    #                   data_src=data_src, data_dir=data_dir, inp_dir=inp_dir, nc=-1,
    #                   term=-1)
    # else:
    # print("Okay, ")
    for i in os.listdir(inp_dir):
        debug_inp(os.path.join(inp_dir, i), noinput=True, usr_configs_read=True,
                  data_src=data_src, data_dir=data_dir, inp_dir=inp_dir)


def main():
    if any(j in sys.argv for j in ['-h', '--help']):
        help(__name__)
        sys.exit()
    if 'clean' in sys.argv:
        top_dir = os.path.abspath(os.path.dirname(__file__))
        try:
            print("Deleting 'dmgui_au.conf' ...")
            os.remove(os.path.join(top_dir, "dmgui_au", "dmgui_au.conf"))
        except FileNotFoundError:
            print("Config file 'dmgui_au.conf' not found")
        if '--all' in sys.argv:
            data_tree = os.path.join(top_dir, 'data')
            del_data_tree = input("WARNING: This will delete everything under\n\n"
                                  "{}\n\nContinue? (y/[n]) ".format(data_tree))
            if del_data_tree.lower() in 'yes':
                pass
            else:
                return
            try:
                x = "'data/'"
                print("Deleting {} ...".format(x))
                shutil.rmtree(data_tree)
                x = "'setup.log'"
                print("Deleting {} ...".format(x))
                os.remove(os.path.join(top_dir, "setup.log"))
            except FileNotFoundError as err:
                print("'clean' already run?", err)
        sys.exit()
    if "dropbox" in sys.argv:
        dropbox = True
    else:
        dropbox = False
    if "--quiet" in sys.argv:
        quiet = True
    else:
        quiet = False
    # with loggercontext(show=['sam_path', 'naming_convention', 'num_terminal_char']):
    with loggercontext(quiet=quiet):
        setup_dirs_and_files(dropbox)


if __name__ == "__main__":
    main()
