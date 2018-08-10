from __future__ import absolute_import
import sys
# utility packages
from . import combine_inp_files
from . import demag_gui_au
from . import get_all_inp_files
from . import debug_inp
from . import find_dropbox
# if they exist, declare path names to be used globally
try:
    from config import user
    from_usr = user.demaggui_user
    data_output_path = from_usr["magic_out"]
    data_dir = from_usr["data_dir"]
    inp_dir = from_usr["inp_dir"]
except:
    # if setup.py is running, don't issue warning
    if sys.argv[0] != 'setup.py':
        print("User configuration/local path names not loaded. Please run setup.py")
    else:
        pass

__all__ = ['combine_inp_files', 'demag_gui_au', 'get_all_inp_files', 'debug_inp', 'find_dropbox']
