#!/usr/bin/env python

# -----------------------------------------------------------------------------
# Copyright (c) 2013, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from setuptools import setup
from glob import glob

__version__ = "0.2.0-dev"


classes = """
    Development Status :: 3 - Alpha
    License :: OSI Approved :: BSD License
    Topic :: Scientific/Engineering :: Bio-Informatics
    Topic :: Software Development :: Libraries :: Application Frameworks
    Topic :: Software Development :: Libraries :: Python Modules
    Programming Language :: Python
    Programming Language :: Python :: 2.7
    Programming Language :: Python :: Implementation :: CPython
    Operating System :: POSIX :: Linux
    Operating System :: MacOS :: MacOS X
"""

with open('README.rst') as f:
    long_description = f.read()

classifiers = [s.strip() for s in classes.split('\n') if s]

setup(name='qiita-spots',
      version=__version__,
      long_description=long_description,
      license="BSD",
      description='Qiita: Spot Patterns',
      author="Qiita development team",
      author_email="qiita.help@gmail.com",
      url='https://github.com/biocore/qiita',
      test_suite='nose.collector',
      packages=['qiita_core',
                'qiita_db',
                'qiita_db/handlers',
                'qiita_db/metadata_template',
                'qiita_pet',
                'qiita_pet/uimodules',
                'qiita_pet/handlers',
                'qiita_pet/handlers/study_handlers',
                'qiita_pet/handlers/api_proxy',
                'qiita_ware'
                ],
      include_package_data=True,
      package_data={
          'qiita_core': [
              'support_files/config_test.cfg'
              'support_files/server.crt',
              'support_files/server.csr',
              'support_files/server.key'
            ],
          'qiita_db': [
              'support_files/*.sql',
              'support_files/patches/*.sql',
              'support_files/patches/python_patches/*.py',
              'support_files/test_data/preprocessed_data/*',
              'support_files/test_data/processed_data/*',
              'support_files/test_data/raw_data/*',
              'support_files/test_data/analysis/*',
              'support_files/test_data/reference/*',
              'support_files/test_data/job/*.txt',
              'support_files/test_data/job/2_test_folder/*',
              'support_files/test_data/uploads/1/a_folder/*.txt',
              'support_files/test_data/uploads/1/.hidden_file.txt',
              'support_files/test_data/uploads/1/uploaded_file.txt',
              'support_files/test_data/templates/*',
              'support_files/work_data/*'],
          'qiita_pet': [
              'static/css/*.css', 'static/img/*.png',
              'static/img/*.gif', 'static/img/*.ico',
              'static/js/*.js', 'static/vendor/css/*.css',
              'static/vendor/css/images/*.png',
              'static/vendor/css/*.png',
              'static/vendor/fonts/glyphicons*.*',
              'static/vendor/images/*.png',
              'static/vendor/js/*.js',
              'results/admin/jobname/*.html',
              'templates/*.html',
              'templates/study_description_templates/*.html',
              'support_files/config_portal.cfg',
              'support_files/doc/Makefile',
              'support_files/doc/README.md',
              'support_files/doc/source/conf.py',
              'support_files/doc/source/*.rst',
              'support_files/doc/source/tutorials/*.rst',
              'support_files/doc/source/admin/*.rst',
              'support_files/doc/source/qiita-philosophy/*.rst',
              'support_files/doc/source/admin/images/*.png',
              'support_files/doc/source/tutorials/images/*.png',
              'support_files/doc/source/qiita-philosophy/images/*.png',
              'support_files/doc/source/_static/*.png'
              ]},
      scripts=glob('scripts/*'),
      extras_require={'test': ["nose >= 0.10.1", "pep8", 'mock']},
      install_requires=['psycopg2', 'click >= 3.3', 'future',
                        'bcrypt', 'pandas >= 0.17', 'numpy >= 1.7',
                        'tornado==3.1.1', 'toredis', 'redis', 'six',
                        'ipython[all] >= 2.4.1, < 2.5', 'pyparsing',
                        'h5py >= 2.3.1', 'biom-format', 'natsort', 'networkx',
                        'scikit-bio >= 0.2.3, < 0.3.0', 'wtforms == 2.0.1',
                        'qiime >= 1.9.0, < 1.10.0', 'moi',
                        'sphinx-bootstrap-theme', 'Sphinx >= 1.2.2',
                        'gitpython', 'coveralls'],
      classifiers=classifiers
      )
