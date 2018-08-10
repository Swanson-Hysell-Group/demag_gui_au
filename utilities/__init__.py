from __future__ import absolute_import
import sys

from . import combine_inp_files
from . import demag_gui_au
from . import get_all_inp_files
from . import debug_inp
try:
    from config import user
    from_usr = user.demaggui_user
except:
    if sys.argv[0] != 'setup.py':
        print("User configuration/local path names not loaded. Please run setup.py")
    else:
        pass

__all__ = ['combine_inp_files', 'demag_gui_au', 'get_all_inp_files', 'debug_inp']
