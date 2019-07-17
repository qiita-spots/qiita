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

__version__ = "072019"


classes = """
    Development Status :: 3 - Alpha
    License :: OSI Approved :: BSD License
    Topic :: Scientific/Engineering :: Bio-Informatics
    Topic :: Software Development :: Libraries :: Application Frameworks
    Topic :: Software Development :: Libraries :: Python Modules
    Programming Language :: Python
    Programming Language :: Python :: 3.6
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
              'support_files/config_portal.cfg',
              'support_files/doc/Makefile',
              'support_files/doc/README.md',
              'support_files/doc/source/conf.py',
              'support_files/doc/source/*.rst',
              'support_files/doc/source/tutorials/*.rst',
              'support_files/doc/source/admin/*.rst',
              'support_files/doc/source/dev/*.rst',
              'support_files/doc/source/qiita-philosophy/*.rst',
              'support_files/doc/source/admin/images/*.png',
              'support_files/doc/source/tutorials/images/*.png',
              'support_files/doc/source/qiita-philosophy/images/*.png',
              'support_files/doc/source/_static/*.png'
              ]},
      scripts=glob('scripts/*'),
      # making sure that numpy is installed before biom
      setup_requires=['numpy'],
      install_requires=['psycopg2', 'click', 'future', 'bcrypt', 'pandas',
                        'biom-format', 'tornado<6.0', 'toredis', 'redis',
                        'scp', 'pyparsing', 'h5py',  'natsort', 'nose', 'pep8',
                        'networkx', 'humanize', 'scikit-bio', 'wtforms',
                        'openpyxl', 'sphinx-bootstrap-theme', 'Sphinx', 'nltk',
                        'gitpython', 'redbiom', 'pyzmq', 'sphinx_rtd_theme',
                        'paramiko', 'seaborn',  'matplotlib', 'scipy', 'nose',
                        'flake8', 'six', 'qiita-files @ https://github.com/'
                        'qiita-spots/qiita-files/archive/master.zip', 'mock',
                        'supervisor @ https://github.com/Supervisor/'
                        'supervisor/archive/master.zip', 'joblib'],
      classifiers=classifiers
      )
