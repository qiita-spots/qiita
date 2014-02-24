#!/usr/bin/env python

#-----------------------------------------------------------------------------
# Copyright (c) 2013, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
#-----------------------------------------------------------------------------

__author__ = "Daniel McDonald"
__copyright__ = "Copyright 2013, The Qiita project"
__credits__ = ["Daniel McDonald", "Adam Robbins-Pianka",
               "Antonio Gonzalez Pena", " Yoshiki Vazquez Baeza",
               "Jose Antonio Navas Molina", "Emily TerAvest"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Daniel McDonald"
__email__ = "mcdonadt@colorado.edu"

from distutils.core import setup
from glob import glob


classes = """
    Development Status :: 4 - Beta
    License :: OSI Approved :: BSD License
    Topic :: Scientific/Engineering :: Bio-Informatics
    Topic :: Software Development :: Libraries :: Application Frameworks
    Topic :: Software Development :: Libraries :: Python Modules
    Programming Language :: Python
    Programming Language :: Python :: 2.7
    Programming Language :: Python :: Implementation :: CPython
    Operating System :: OS Independent
    Operating System :: POSIX :: Linux
    Operating System :: MacOS :: MacOS X
"""

long_description = """Qiita is a databasing and UI effort for QIIME"""

classifiers = [s.strip() for s in classes.split('\n') if s]

# from https://wiki.python.org/moin/PortingPythonToPy3k
try:
    # python 3.x
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    # python 2.x
    from distutils.command.build_py import build_py

setup(name='qiita',
      cmdclass={'build_py': build_py},
      version=__version__,
      long_description = long_description,
      license = __license__,
      description='Qiita',
      author=__maintainer__,
      author_email=__email__,
      url='http://biocore.github.io/qiita',
      packages=['qiita_core',
                'qiita_core/commands',
                'qiita_core/interfaces',
                'qiita_core/interfaces/argparse',
                'qiita_core/interfaces/argparse/config',
                'qiita_db',
                'qiita_db/commands',
                'qiita_db/interfaces',
                'qiita_db/interfaces/optparse',
                'qiita_db/interfaces/optparse/config',
                'qiita_db/backends',
                'qiita_db/backends/fs',
                'qiita_db/backends/sql',
                'qiita_db/core',
                'qiita_pet',
                'qiita_ware',
                'qiita_ware/core',
                'qiita_ware/api'
                ],
      scripts=glob('scripts/*'),
      install_requires=['tornado == 3.1.1', 'redis == 2.8.0',
                        'tornado-redis == 2.4.15', 'psycopg2',
                        'pgbouncer', 'pyqi == 0.3' ,'ipython[all]',
                        'qiime == 1.8.0'],
      classifiers=classifiers
            )
