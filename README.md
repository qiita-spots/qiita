QiiTa
=====

Welcome to QiiTa, the QIIME databasing effort to enable rapid analysis of microbial ecology datasets. The QiiTa repository is responsible for defining the datamodel and the Python API for interacting with a QiiTa database.

Dependencies
------------

* PostgresSQL 9.3
* Psycopg 2.5.1
* Python 2.7 or Python 3.3
* pyqi 0.3

Install
-------

To get started, clone the repository, install and populate the database with the QiiTa schema:

    $ git clone git@github.com:qiime/QiiTa.git
    $ cd QiiTa
    $ python setup.py build
    $ python setup.py install
    $ qiita create-database
