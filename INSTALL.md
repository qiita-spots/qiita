Dependencies
------------

Qiita is a python package, with support for python 2.7 and 3.2, that depends on the following python libraries (all of them can be installed using pip):

<!--
* [pgbouncer](http://pgfoundry.org/projects/pgbouncer)
* [IPython](https://github.com/ipython/ipython)
-->

* [tornado 3.1.1](http://www.tornadoweb.org/en/stable/)
* [tornado-redis](https://pypi.python.org/pypi/tornado-redis)
* [Psycopg2](http://initd.org/psycopg/download/)
* [click](http://click.pocoo.org/)
* [NumPy](https://github.com/numpy/numpy)
* [Pandas](http://pandas.pydata.org/)
* [QIIME development version](https://github.com/biocore/qiime)
* [future](http://python-future.org/)
* [bcrypt](https://github.com/pyca/bcrypt/)
* [redis](https://github.com/andymccurdy/redis-py)
* [pyparsing 2.0.2](http://pyparsing.wikispaces.com/)

And on the following packages:

* [PostgresSQL 9.3](http://www.postgresql.org/download/)
* [redis 2.8.0](https://pypi.python.org/pypi/redis/)

<!--
* [redis-server](http://redis.io)
-->

Install
-------

Once you have [PostgresSQL](http://www.postgresql.org/download/) and [redis](https://pypi.python.org/pypi/redis/) installed (follow the instruction on their web site), simply run these commands to install qiita and configure the demo environment, replacing $QIITA_DIR for the path where qiita is installed
(note that if you are not using Ubuntu you might need to follow the instructions in the next section):

```bash
echo "export QIITA_CONFIG_FP=$QIITA_DIR/qiita_core/support_files/config_demo.txt" >> ~/.bashrc
source ~/.bashrc
pip install https://github.com/biocore/qiita/archive/master.zip
qiita_env make_env --env demo
```
## If using other operating systems that are not Ubuntu

You will need to add the postgres user to the database. In order to do this, run:

```bash
createuser -s postgres -d
```

If you receive the following error, you can ignore this step and continue with the qiita installation:
```bash
createuser: creation of new role failed: ERROR:  role "postgres" already exists
```
