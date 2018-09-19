# -*- coding: utf-8 -*-
"""Utilities for demag_gui_au.py

This module contains tools used by the Demag GUI Autoupdate-wrapper that provide
additional functionality outside the main GUI wrapper in demag_gui_au.py.
"""

import sys
import os
from time import asctime
from contextlib import ContextDecorator


################################################################################
#                            Command Line Interface                            #
################################################################################

############
#  Colors  #
############

class bcolors:
    """define colors for output to terminal"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''
        self.BOLD = ''


############
#  Logger  #
############

class Logger(object):
    """
    Log stdout to debug_inp.log
    """

    def __init__(self, log_file, quiet=False, clr_output=True):
        self.tclr = bcolors()
        if not clr_output:
            self.tclr.disable()
        self.terminal = sys.stdout
        self.log = open(log_file, "a+")
        self.log.write(
            '\n{:-^80}\n\n'.format('  Starting session at {}  '.format(asctime())))

    def write(self, message):
        for warn_var in ('warning:', 'Warning:', 'WARNING:'):
            if message.lstrip().startswith(warn_var):
                message = message.lstrip().replace(warn_var, '-W-')
        for err_var in ('error:', 'Error:', 'ERROR:'):
            if message.lstrip().startswith(err_var):
                message = message.lstrip().replace(err_var, '-E-')
        self.log.write(message)
        if '-I-' in str(message):
            if 'Timer' in str(message):
                self.terminal.write(self.tclr.OKBLUE)
            else:
                self.terminal.write(self.tclr.OKGREEN)
        elif '-W-' in str(message):
            self.terminal.write(self.tclr.WARNING)
        elif '-E-' in str(message):
            self.terminal.write(self.tclr.FAIL)
        self.terminal.write(message)
        self.terminal.write(bcolors.ENDC)

    def flush(self):
        self.terminal.flush()


class loggercontext(ContextDecorator):
    """A context manager for the Logger class.

    This simplifies integration in the code to a `with` statement. This also
    ensures that sys.stdout is returned to its original state.

    """

    def __init__(self, log_file, quiet=False):
        self.log_file = log_file
        self.quiet = quiet

    def __enter__(self):
        sys.stdout = Logger(self.log_file, quiet=self.quiet)
        return sys.stdout

    def __exit__(self, *exc):
        sys.stdout.log.write('{:-^80}\n'.format('  Closing session  '))
        sys.stdout.log.close()
        sys.stdout = sys.__stdout__
        return False
