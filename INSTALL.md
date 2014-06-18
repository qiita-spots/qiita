Dependencies
------------

Qiita is a python package, with support for python 2.7 and 3.2, that depends on the following python libraries:

<!--
* [pgbouncer](http://pgfoundry.org/projects/pgbouncer)
* [IPython](https://github.com/ipython/ipython)
* [QIIME](https://github.com/qiime/qiime)
-->

* [tornado 3.1.1](http://www.tornadoweb.org/en/stable/)
* [tornado-redis](https://pypi.python.org/pypi/tornado-redis)
* [Psycopg2](http://initd.org/psycopg/download/)
* [pyqi 0.3](https://github.com/bipy/pyqi)
* [NumPy](https://github.com/numpy/numpy)

And on the following packages:

* [PostgresSQL 9.3](http://www.postgresql.org/download/)
* [redis 2.8.0](https://pypi.python.org/pypi/redis/)

<!--
* [redis-server](http://redis.io)
-->

Install
-------

Once you have Postgres and redis installed (we recommend to follow the instruction on their web page), you can install Qiita by running the following commands:

```bash
pip install https://github.com/biocore/qiita/archive/master.zip
```

In MacOS X, you will need to add the postgres user to the database, since it is not added by default, and grant him all privileges. In order to do that, you can execute:

```bash
createuser -s postgres -d
```

Then, in order to setup the environment, run:

```bash
qiita_db make_demo_env
```