# from . import utilities
from . import config
from .config import user

# if they exist, declare path names to be used globally
try:
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
