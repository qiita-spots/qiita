#!/usr/bin/env python

# -----------------------------------------------------------------------------
# Copyright (c) 2013, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

__version__ = "0.1.0-dev"

from setuptools import setup
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

setup(name='qiita',
      version=__version__,
      long_description=long_description,
      license="BSD",
      description='Qiita',
      author="Qiita development team",
      author_email="mcdonadt@colorado.edu",
      url='http://biocore.github.io/qiita',
      test_suite='nose.collector',
      packages=['qiita_core',
                'qiita_db',
                'qiita_pet',
                'qiita_ware',
                'qiita_ware/core',
                'qiita_ware/api'
                ],
      package_data={'qiita_core': ['support_files/config_test.txt'],
                    'qiita_db': ['support_files/*sql',
                                 'support_files/test_data/*']},
      scripts=glob('scripts/*'),
      extras_require={'test': ["nose >= 0.10.1", "pep8"],
                      'doc': ["Sphinx >= 1.2.2", "sphinx-bootstrap-theme"]},
      install_requires=['psycopg2', 'click == 1.0'],
      classifiers=classifiers
      )
