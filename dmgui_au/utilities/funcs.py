#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re


def shortpath(abspath):
    """return shorter path name with '~' for display/logging"""
    return abspath.replace(os.path.expanduser('~') + os.sep, '~/', 1)


def cache_site_files(data_path):
    """cache site-level magic files to de-clutter data folder"""
    if not os.path.exists(os.path.join(data_path, 'magic_cache')):
        os.makedirs(os.path.join(data_path, 'magic_cache'))
    filt = re.compile('.*_(specimens|samples|sites|locations).txt|.*\.magic')
    for s in os.listdir(data_path):
        if filt.match(s):
            os.rename(os.path.join(data_path, s),
                      os.path.join(data_path, 'magic_cache', s))
    return True


def uncache_site_files(data_path):
    """uncache site-level magic files to speed up magic conversion"""
    if not os.path.exists(os.path.join(data_path, 'magic_cache')):
        return False, 0
    num_cached_files = len(os.listdir(os.path.join(data_path, 'magic_cache')))
    for s in os.listdir(os.path.join(data_path, 'magic_cache')):
        os.rename(os.path.join(data_path, 'magic_cache', s), os.path.join(data_path, s))
    return True, num_cached_files
