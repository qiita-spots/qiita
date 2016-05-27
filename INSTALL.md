
Qiita installation
==================

Qiita is pip installable, but depends on some non-python packages that must be installed first. We strongly recommend using virtual environments; the solution we recommend ot manage them is [miniconda](http://conda.pydata.org/miniconda.html), a lightweight version of the virtual environment, python distribution, and package manager anaconda.

## Install miniconda

Download the appropriate installer [here](http://conda.pydata.org/miniconda.html) corresponding to your operating system and execute it.

Ensure that your `~/.bash_profile` (for default bash users) and/or `~/.zshrc` (for zshell users) contains the following line, which prepends a path leading to miniconda's binaries to the `$PATH` variable.

```bash
# added by Miniconda2 installer
export PATH="/Users/hannes/miniconda2/bin:$PATH"
```

This essentially allows miniconda's binaries representing each of your virtual environments to take precedence over any custom, pre-existing installations of pip or python you might have installed through homebrew, for example – thus you do *not* have to uninstall them.

Next, ensure conda is up-to-date.

```bash
conda update conda
```

Finally, restart your shell or reload your profile/rc file to ensure your `$PATH` variable was updated:

````bash
source ~/.bash_profile
````

## Setup miniconda environment for QIITA

To ensure that QIITA can install its dependencies – some of which require older or specific distributions of pip packages – without interfering with any pre-existing, globally installed pip packages you might have, you will setup a virtual environment in conda that you must *activate* whenever you are working with or running QIITA.

```bash
conda create --yes --name qiita python=2.7 pip nose flake8 pyzmq networkx pyparsing natsort mock future libgfortran seaborn 'pandas>=0.18' 'matplotlib>=1.1.0' 'scipy>0.13.0' 'numpy>=1.7' 'h5py>=2.3.1' --channel https://conda.anaconda.org/OpenMDAO
```

If you receive an error message about conda being unable to find one of the specified packages in its repository, you will have to manually search for them (see troubleshooting miniconda below).

Next, activate your newly created virtual environment for qiita:

```bash
source activate qiita
```

(When you want to deactivate this environment, e.g. to return to a different project or back to your global python and pip packages, run `source deactivate`)

If your new conda environment is functioning correctly, you should see this kind of output when you run `which python`, indicating that the `python` command now refers to the python binary in your new virtual environment, rather than a previous global default such as `/usr/bin/python`:

```
▶ which python
/Users/your_username/miniconda2/envs/qiita/bin/python
(qiita)
```

If you don't see this output, your `$PATH` variable was setup incorrectly or you haven't restarted your shell.

As long as you are in the active qiita environment, commands such as `pip install` or `python` will refer to and be contained within this virtual environment.


Install the non-python dependencies
-----------------------------------

* [PostgreSQL](http://www.postgresql.org/download/) (minimum required version 9.3.0, we have tested most extensively with 9.3)
* [redis-server](http://redis.io) (we have tested most extensively with 2.8.17)
* [hdf5](https://www.hdfgroup.org/HDF5/)

There are several options to install these dependencies depending on your needs:

- You could install them via conda, however, the anaconda repository may not have the exact versions of these that you want. 
- You could install the exact versions we tested as per instructions on their websites, and thus make their available globally on your operating system. This may or may not cause problems if other software on your system requires a differing, specific version of the packages. These instructions were tested with this method.
- You could setup a full development environment with [Vagrant](https://www.vagrantup.com/), and continue using conda under it to primarily manage python dependencies.

Install both of these packages according to the instructions on their websites.
You'll then need to ensure that the postgres binaries (for example, ``psql``)
are in your executable search path (``$PATH`` environment variable). For
example if you are using Postgres.app on OS X, you can do this by addint
the following line to your `.bash_profile`:

```bash
export PATH=$PATH:/Applications/Postgres.app/Contents/Versions/9.3/bin/
```


Install Qiita and its python dependencies
-----------------------------------------

Then, you can use pip to install Qiita, which will also install its python dependencies.

```bash
pip install numpy
pip install https://github.com/biocore/mustached-octo-ironman/archive/master.zip --no-deps
pip install qiita-spots
```


Install Qiita development version and its python dependencies
-------------------------------------------------------------

You can also use pip to install the development version of Qiita:

```bash
pip install numpy
pip install https://github.com/biocore/mustached-octo-ironman/archive/master.zip --no-deps
```

Clone the git repository with the development version of Qiita:

```bash
git clone https://github.com/biocore/qiita.git
```

Install Qiita:
```bash
cd qiita
pip install .
```

You will also need to install the target gene plugin for Qiita to be fully functional.
However, the plugin is already included in the repository so to install it simply execute:
```bash
cd qiita_plugins/target_gene
pip install .
```


Qiita configuration
===================
After these commands are executed, you will need to:
1. Download a [sample Qiita configuration file](https://github.com/biocore/qiita/blob/master/qiita_core/support_files/config_test.cfg).

```bash
  cd
  curl -O https://raw.githubusercontent.com/biocore/qiita/master/qiita_core/support_files/config_test.cfg
```

1. Set your `QIITA_CONFIG_FP` environment variable to point to that file:

```bash
  echo "export QIITA_CONFIG_FP=$HOME/config_test.cfg" >> ~/.bashrc
  echo "export MOI_CONFIG_FP=$QIITA_CONFIG_FP" >> ~/.bashrc
  source ~/.bashrc
```

1. Start a test environment:

```bash
  qiita-env make --no-load-ontologies
```

1. Start the redis server:
```bash
  redis-server
```

1. Start the IPython cluster:

```bash
  qiita-env start_cluster qiita-general && sleep 30
```

1. Build the documentation (you may need to add `sudo` depending on your
   privileges and the installation location:

```bash
  qiita pet webserver
```

1. Start the server:

   ```bash
    qiita pet webserver start
   ```

If all the above commands executed correctly, you should be able to go to http://localhost:21174 in your browser, to login use `test@foo.bar` and `password` as the credentials. (In the future, we will have a *single user mode* that will allow you to use a local Qiita server without logging in. You can track progress on this on issue [#920](https://github.com/biocore/qiita/issues/920).)

## Installation issues on Ubuntu 14.04

### `fe_sendauth: no password supplied`

If you get a traceback similar to this one when starting up Qiita
```python
File "/home/jorge/code/qiita/scripts/qiita-env", line 71, in make
  make_environment(load_ontologies, download_reference, add_demo_user)
File "/home/jorge/code/qiita/qiita_db/environment_manager.py", line 180, in make_environment
  admin_conn = SQLConnectionHandler(admin='admin_without_database')
File "/home/jorge/code/qiita/qiita_db/sql_connection.py", line 120, in __init__
  self._open_connection()
File "/home/jorge/code/qiita/qiita_db/sql_connection.py", line 155, in _open_connection
  raise RuntimeError("Cannot connect to database: %s" % str(e))
RuntimeError: Cannot connect to database: fe_sendauth: no password supplied
```
it can be solved by setting a password for the database (replace `postgres` with the actual name of the database qiita is configured to use):
```
$ psql postgres
ALTER USER postgres PASSWORD 'supersecurepassword';
\q
```

It might be necessary to restart postgresql: `sudo service postgresql restart`.

Furthermore, the `pg_hba.conf` file can be modified to change authentication type for local users to trust (rather than, e.g., md5) but we haven't tested this solution.

## Troubleshooting installation on non-Ubuntu operating systems

### xcode

If running on OS X you should make sure that the Xcode and the Xcode command line tools are installed.

### postgres

If you are using Postgres.app on OSX, a database user will be created with your system username. If you want to use this user account, change the `USER` and `ADMIN_USER` settings to your username under the `[postgres]` section of your Qiita config file.

### conda

If you are getting an error message running `conda create`, complaining about missing packages, then you might have to locate the appropriate conda channels and re-run `conda create` with the `--channel` flag:

For example, if `libgfortran` is missing:

```
# Install anaconda-client to search repositories
conda install anaconda-client

# Now search for missing package
anaconda search -t conda libgfortran
Using Anaconda Cloud api site https://api.anaconda.org
Run 'anaconda show <USER/PACKAGE>' to get more details:
Packages:
     Name                      |  Version | Package Types   | Platforms
     ------------------------- |   ------ | --------------- | ---------------
     OpenMDAO/libgfortran      |    4.8.3 | conda           | linux-32, osx-64
     aetrial/libgfortran       |          | conda           | linux-64
     ....etc....
```

Install the the appropriate channel name that corresponds to your platform. For example, for Mac OS X 64-bit this would be:

`conda install --channel https://conda.anaconda.org/OpenMDAO libgfortran`

Now you can re-run your `conda create` command:

`conda create [previous parameters go here] --channel OpenMDAO/libgfortran`







## Troubleshooting installation issues with Python

As a general rule of thumb you will want to have an updated version of Python
2.7 and an updated version of pip (`pip install -U pip` will do the trick).

H5PY is known to cause a few problems, however their [installation
instructions](http://docs.h5py.org/en/latest/build.html) are a great resource
to troubleshoot your system in case any of the steps above fail.

## Troubleshooting installation issues with matplotlib

In the event that you get `_tkinter.TclError: no display name and no $DISPLAY environment variable` error while trying to generate figures that rely on matplotlib, you should create a matplotlib rc file. This configuration file should have `backend : agg`. For more information you should visit the [matplotlib configuration](http://matplotlib.org/users/customizing.html) and [troubleshooting](http://matplotlib.org/faq/troubleshooting_faq.html#locating-matplotlib-config-dir) page.
