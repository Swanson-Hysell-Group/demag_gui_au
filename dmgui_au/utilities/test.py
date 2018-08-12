#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import dmgui_au.config.user as user

path_conf = user.demaggui_user

if 'data_dir' in sys.argv:
    print(path_conf['data_dir'])
if 'inp_dir' in sys.argv:
    print(path_conf['inp_dir'])
if 'out_dir' in sys.argv:
    print(path_conf['magic_out'])
