#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def shortpath(abspath):
    """return shorter path name with '~' for display/logging"""
    return abspath.replace(os.path.expanduser('~') + os.sep, '~/', 1)
