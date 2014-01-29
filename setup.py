#!/usr/bin/env python

#-----------------------------------------------------------------------------
# Copyright (c) 2013, The QIIME Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
#-----------------------------------------------------------------------------

__author__ = "Daniel McDonald"
__copyright__ = "Copyright 2013, The Qiita project"
__credits__ = ["Daniel McDonald", "Adam Robbins-Pianka",
               "Antonio Gonzalez Pena", " Yoshiki Vazquez Baeza",
               "Jose Antonio Navas Molina"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Daniel McDonald"
__email__ = "mcdonadt@colorado.edu"

from distutils.core import setup

try:
    import pyqi
except ImportError:
    raise ImportError("pyqi cannot be found. Can't continue")

try:
    import psycopg2
except ImportError:
    raise ImportError("psycopg2 cannot be found. Can't continue")

# from https://wiki.python.org/moin/PortingPythonToPy3k
try:
    # python 3.x
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    # python 2.x
    from distutils.command.build_py import build_py

setup(name='Qiita',
      cmdclass={'build_py': build_py},
      version=__version__,
      description='Qiita',
      author=__maintainer__,
      author_email=__email__,
      url='http://qiime.github.io/QiiTa',
      packages=['qiita',
                'qiita/commands',
                'qiita/interfaces',
                'qiita/interfaces/argparse',
                'qiita/interfaces/argparse/config']
      )
