Qiita installation
==================

Qiita is pip installable, but depends on some non-python packages that must be installed first.

Install non-python dependencies (install these first)
-----------------------------------------------------

* [PostgreSQL](http://www.postgresql.org/download/) (we have tested most extensively with 9.3)
* [redis-server](http://redis.io) (we have tested most extensively with 2.8.17)

Install both of these packages according to the instructions on their websites. You'll then need to ensure that the postgres binaries (for example, ``psql``) are in your executable search path (``$PATH`` environment variable).

Install Qiita and its python dependencies
-----------------------------------------

Then, just ``pip install qiita-spots``, which will include installation of its python dependencies following:

```bash
pip install numpy
pip install https://github.com/biocore/mustached-octo-ironman/archive/master.zip --no-deps
pip install qiita-spots
```

Qiita configuration
===================
After these commands are executed, you will need to:
1. Download a [sample Qiita configuration file](https://github.com/biocore/qiita/blob/master/qiita_core/support_files/config_test.txt).

  ```bash
  cd
  curl -O https://raw.githubusercontent.com/biocore/qiita/master/qiita_core/support_files/config_test.txt > config_test.txt
  ```

2. Set your `QIITA_CONFIG_FP` environment variable to point to that file:

  ```bash
  echo "export QIITA_CONFIG_FP=$HOME/config_test.txt" >> ~/.bashrc
  echo "export MOI_CONFIG_FP=$QIITA_CONFIG_FP" >> ~/.bashrc
  source ~/.bashrc
  ```

3. Start a test environment:

  ```bash
  qiita_env make --no-load-ontologies
  ```

4. Finally you can start the server:

  ```bash
  qiita_env start_cluster demo test reserved && sleep 30
  qiita webserver start
  ```

If all the above commands executed correctly, you should be able to open http://localhost:8888 in your web browser. You can login with `demo@microbio.me` and `password` as your credentials. (In the future, we will have a *single user mode* that will allow you to use a local Qiita server without logging in. You can track progress on this on issue [#920](https://github.com/biocore/qiita/issues/920).)


## Troubleshooting installation on non-Ubuntu operating systems

### xcode

If running on OS X you should make sure that the Xcode and the Xcode command line tools are installed.

### postgres

If you are using Postgres.app on OSX, a database user will be created with your system username. If you want to use this user account, change the `USER` and `ADMIN_USER` settings to your username under the `[postgres]` section of your Qiita config file.
