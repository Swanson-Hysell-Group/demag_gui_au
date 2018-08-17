import sys
import os
import configparser

try:
    configfile = os.path.join(os.path.dirname(__file__),"dmgui_au.conf")
    configs = configparser.ConfigParser()
    configs.read_file(open(configfile))
    configs.read(configfile)
    top_dir = configs['PathNames']['top_dir']
    pkg_dir = configs['PathNames']['pkg_dir']
    data_dir = configs['PathNames']['data_dir']
    data_src = configs['PathNames']['data_src']
    inp_dir = configs['PathNames']['inp_dir']
except:
    # if setup.py is running, don't issue warning
    if sys.argv[0] != 'setup.py':
        print("-W- Local path names have not been set. Please run setup.py")
    else:
        pass

