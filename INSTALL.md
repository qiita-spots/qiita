Dependencies
------------

Qiita is a python package, with support for python 2.7, that depends on the following python libraries (all of them can be installed using pip):

<!--
* [pgbouncer](http://pgfoundry.org/projects/pgbouncer)
-->

* [IPython](https://github.com/ipython/ipython)
* [tornado 3.1.1](http://www.tornadoweb.org/en/stable/)
* [toredis](https://pypi.python.org/pypi/toredis)
* [Psycopg2](http://initd.org/psycopg/download/)
* [click](http://click.pocoo.org/)
* [NumPy](https://github.com/numpy/numpy)
* [Pandas >= 0.15](http://pandas.pydata.org/)
* [QIIME 1.8.0-dev](https://github.com/biocore/qiime)
* [future 0.13.0](http://python-future.org/)
* [bcrypt](https://github.com/pyca/bcrypt/)
* [redis](https://github.com/andymccurdy/redis-py)
* [pyparsing 2.0.2](http://pyparsing.wikispaces.com/)
* [networkx](http://networkx.lanl.gov/index.html)
* [WTForms 2.0.1](https://wtforms.readthedocs.org/en/latest/)
* [Mock](http://www.voidspace.org.uk/python/mock/)  For running test code only

And on the following packages:

* [PostgresSQL 9.3](http://www.postgresql.org/download/)
* [redis-server](http://redis.io)

Install
-------

Once you have [PostgresSQL](http://www.postgresql.org/download/) and [redis](https://pypi.python.org/pypi/redis/) installed (follow the instruction on their web site), simply run these commands to install qiita and configure the demo environment, replacing $QIITA_DIR for the path where qiita is installed
(note that if you are not using Ubuntu you might need to follow the instructions in the next section).

```bash
pip install numpy
pip install cogent burrito qcli emperor pyzmq
pip install https://github.com/biocore/qiime/archive/master.zip --no-deps
pip install qiita-spots
```

After these commands are executed, you will need (1) download a [sample Qiita configuration file](https://raw.githubusercontent.com/biocore/qiita/a0628e54aef85b1a064d40d57ca981aaf082a120/qiita_core/support_files/config_test.txt), (2) set the `QIITA_CONFIG_FP` environment variable and (3) proceed to initialize your environment:

```bash
# (1) use curl -O if using OS X
wget https://github.com/biocore/qiita/blob/a0628e54aef85b1a064d40d57ca981aaf082a120/qiita_core/support_files/config_test.txt
# (2) set the enviroment variable in your .bashrc
echo "export QIITA_CONFIG_FP=config_test.txt" >> ~/.bashrc
source ~/.bashrc
# (3) start a test environment
qiita_env make --no-load-ontologies
```

Finally you need to start the server:

```bash
# IPython takes a while to get initialized so wait 30 seconds
qiita_env start_cluster demo test reserved && sleep 30
qiita webserver start

```

If all the above commands executed correctly, you should be able to go to http://localhost:8888 in your browser, to login use `demo@microbio.me` and `password` as the credentials.


## If using other operating systems that are not Ubuntu

You will need to add the postgres user to the database. In order to do this, run:

```bash
createuser -s postgres -d
```

If you receive the following error, you can ignore this step and continue with the qiita installation:
```bash
createuser: creation of new role failed: ERROR:  role "postgres" already exists
```
