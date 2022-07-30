#!/usr/bin/env python
# -*- coding: UTF-8 -*-    
# Author: 王涛涛/16327
# FileName: setup
# DateTime: 7/31/2022 12:05 AM
import sys

from setuptools import setup

__title__ = 'loguru-ex'
__author__ = 'DoubleT.Wong'
__author_email__ = '15712012343@163.com'
__maintainer__ = __author__
__url__ = 'https://github.com/11ttwang2/loguru-ex'

if sys.version_info < (3, 6):
    raise RuntimeError('loguru-ex requires Python 3.6 or greater')

setup(
    setup_requires='setupmeta',
    python_requires='>=3.6.0',
    versioning='post',
)
