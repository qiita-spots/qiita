QiiTa
=====

Welcome to QiiTa, the QIIME databasing effort to enable rapid analysis of microbial ecology datasets. The QiiTa repository is responsible for defining the data model and the Python API for interacting with a QiiTa database.

Dependencies
------------

* [PostgresSQL 9.3](http://www.postgresql.org/download/)
* [Psycopg 2.5.1](http://initd.org/psycopg/download/)
* [pgbounder 1.5.4](http://pgfoundry.org/projects/pgbouncer)
* [Python 2.7 or Python 3.3](http://www.python.org)
* [pyqi 0.3](https://github.com/bipy/pyqi)

Install
-------

To get started, clone the repository, install and populate the database with the QiiTa schema:

    $ git clone git@github.com:qiime/QiiTa.git
    $ cd QiiTa
    $ python setup.py build
    $ python setup.py install
    $ qiita create-database
