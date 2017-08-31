
Qiita installation
==================

Qiita is pip installable, but depends on specific versions of python and non-python packages that must be installed first. We strongly recommend using virtual environments; a popular solution to manage them is [miniconda](http://conda.pydata.org/miniconda.html), a lightweight version of the virtual environment, python distribution, and package manager anaconda. These instructions will be based on miniconda.

These instructions were tested successfully by [@HannesHolste](github.com/HannesHolste) on Mac OS X El Capitan 10.11.4 and a clean installation of Ubuntu 12.04 LTS (precise) using conda v4.0.7 and cloning from [qiita master branch commit #a9e4e03](https://github.com/biocore/qiita/commit/a9e4e03ecd781d3985abc03d15f2248143e565d7) on 5/27/2016.

## Install and setup miniconda

Download the appropriate installer [here](http://conda.pydata.org/docs/install/quick.html) corresponding to your operating system and execute it.

Next, ensure conda is up-to-date.

```bash
conda update conda
```

### Create a conda environment for Qiita

Setup a virtual environment in conda named `qiita` by executing the following:

```bash
conda create --yes --name qiita python=2.7 pip nose flake8 pyzmq networkx pyparsing natsort mock future libgfortran seaborn 'pandas>=0.18' 'matplotlib>=1.1.0' 'scipy>0.13.0' 'numpy>=1.7' 'h5py>=2.3.1' hdf5
```

If you receive an error message about conda being unable to find one of the specified packages in its repository, you will have to manually find the appropriate conda channel that they belong to (see troubleshooting section below).

### Brief introduction to managing conda environments

Though these instructions use the newly created `qiita` conda environment, the concepts apply to managing conda environments in general.

Activate your newly created virtual environment for qiita whenever you want to run or develop for it:

```bash
source activate qiita
```

After activating your new environment, you should see this kind of output when you run `which python`, indicating that the `python` command now refers to the python binary in your new virtual environment, rather than a previous global default such as `/usr/bin/python`. For example, assuming you installed miniconda in `/Users/your_username/`:

```
$ which python
/Users/your_username/miniconda2/envs/qiita/bin/python
(qiita)
```

If you don't see this output, your `$PATH` variable was setup incorrectly or you haven't restarted your shell. Consult the [conda documentation](http://conda.pydata.org/docs/install/quick.html).

As long as you are in the active qiita environment, commands such as `pip install` or `python` will refer to and be contained within this virtual environment.

When you want to deactivate your current conda environment, e.g. to return to a different project or back to your global python and pip packages, run:

```bash
source deactivate
```


Install the non-python dependencies
-----------------------------------

* [PostgreSQL](http://www.postgresql.org/download/) (minimum required version 9.3.5, we have tested most extensively with 9.3.6)
* [redis-server](http://redis.io) (we have tested most extensively with 2.8.17)

There are several options to install these dependencies depending on your needs:

- **We suggest installing the exact versions in these instructions by following the instructions of the provided links and making them globally available in your machine. However, this might interfere with other apps that might require different versions.** 
- Alternatively, you could install them via conda. However, the conda repository may not have the exact versions of these dependencies that you want.
- You could setup a full development environment with [Vagrant](https://www.vagrantup.com/), and continue using conda under it to primarily manage python dependencies. Note that we don't cover Vagrant in these instructions.

### PostgreSQL installation on Mac OS X

For Mac OS X, you can either install postgres through the [Postgres.app](https://www.postgresql.org/download/macosx/). These instructions were tested with the Postgres.app v9.3.

You'll then need to ensure that the postgres binaries (for example, ``psql``) are in your executable search path (``$PATH`` environment variable). If you are using Postgres.app on OS X, you can do this by running the following, though you may have to replace`~/.bash_profile`with `~/.zshrc` if you're using zshell rather than the built-in bash, and you may have to change the version number `Versions/9.3/` to the exact one that you are installing:

```bash
echo 'export PATH="$PATH:/Applications/Postgres.app/Contents/Versions/9.3/bin/"' >> ~/.bash_profile
source ~/.bash_profile
```

### Redis-server installation on Mac OS X

Assuming you have [homebrew](http://www.brew.sh) installed, you can install redis-server v2.8.x as follows:

```bash
brew update
brew install homebrew/versions/redis28
```


Install Qiita development version and its python dependencies
-------------------------------------------------------------

Clone the git repository with the development version of Qiita into your current directory:

```bash
git clone https://github.com/biocore/qiita.git
```

Navigate to the cloned directory and ensure your conda environment is active:

```bash
cd qiita
source activate qiita
```

Install Qiita (this occurs through setuptools' `setup.py` file in the qiita directory):

```bash
pip install -e . --process-dependency-links
```

At this point, Qiita will be installed and the system will start. However,
you will need to install plugins in order to process any kind of data. For a list
of available plugins, visit the [Qiita Spots](https://github.com/qiita-spots)
github organization. Currently, the `Type Plugins`
[qtp-biom](https://github.com/qiita-spots/qtp-biom) and
[qtp-target-gene](https://github.com/qiita-spots/qtp-target-gene) as well as
the `Plugin` [qp-target-gene](https://github.com/qiita-spots/qp-target-gene) are
required. To install these plugins, simply execute

```bash
pip install git+https://github.com/qiita-spots/qiita_client
pip install git+https://github.com/qiita-spots/qtp-biom
pip install git+https://github.com/qiita-spots/qtp-target-gene
pip install git+https://github.com/qiita-spots/qp-target-gene
```

## Configure Qiita

After these commands are executed, you will need to:

Move the Qiita sample configuration file to a different directory by executing:

```bash
 cp ./qiita_core/support_files/config_test.cfg ~/.qiita_config_test.cfg
```

Set your `QIITA_CONFIG_FP` environment variable to point to that file (into `.bashrc` if using bash; `.zshrc` if using zshell):

```bash
  echo "export QIITA_CONFIG_FP=$HOME/.qiita_config_test.cfg" >> ~/.bashrc
  echo "export MOI_CONFIG_FP=$HOME/.qiita_config_test.cfg" >> ~/.bashrc
  source ~/.bashrc
  # Re-enable conda environment for qiita
  source activate qiita
```

Next, make a test environment:

```bash
qiita-env make --no-load-ontologies
```

## Start Qiita

Start postgres (instructions vary depending on operating system and install method).

Next, start redis server (the command may differ depending on your operating system and install location):

```bash
redis-server
```

Start the qiita server:

```bash
# this builds documentation before starting the server
# alternatively: qiita pet webserver --no-build-docs start
qiita pet webserver start
```
If all the above commands executed correctly, you should be able to go to http://localhost:21174 in your browser, to login use `test@foo.bar` and `password` as the credentials. (In the future, we will have a *single user mode* that will allow you to use a local Qiita server without logging in. You can track progress on this on issue [#920](https://github.com/biocore/qiita/issues/920).)



# Frequently Asked Questions and Troubleshooting

### `Error: database "qiita_test" already exists`

This usually happens after an incomplete run of the qiita-env setup procedure. Drop the postgres table named `qiita_test` and retry setting up qiita-env as per instructions above:

```bash
 $ psql
 DROP DATABASE qiita_test;\q
 # now re-run qiita-env make --no-load-ontologies
```
## Operating-system specific troubleshooting

### Ubuntu

#### `fe_sendauth: no password supplied`

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

#### `Error: You need to install postgresql-server-dev-X.Y for building a server-side extension or libpq-dev for building a client-side application.`

Run the following. Note that for older ubuntu versions (< 14), these commands may install an older version of postgres (< 9.3) which may cause trouble. Ensure you're downloading and installing postgresql 9.3 via a different apt repository as per [instructions here](https://www.postgresql.org/download/linux/ubuntu/).

```bash
sudo apt-get update
sudo apt-get install postgresql
sudo apt-get install postgresql-contrib
sudo apt-get install libpq-dev
```

#### ` c/_cffi_backend.c:15:17: fatal error: ffi.h: No such file or directory`

Missing dependency. Run the following and then re-run whatever command failed earlier:

```bash
sudo apt-get install -y libffi-dev
```

#### `from PyQt4 import QtCore, QtGui ImportError: libSM.so.6: cannot open shared object file: No such file or directory`

```bash
 sudo apt-get install -y python-qt4
```

#### `ERROR:  could not open extension control file "/usr/share/postgresql/9.3/extension/uuid-ossp.control": No such file or directory`

```bash
sudo apt-get install postgresql-contrib
# or: sudo apt-get install postgresql-contrib-9.3 depending on your OS and apt repository versions
```



## General Troubleshooting

Please note that the following notes are related to dependencies that Qiita does not maintain. As such, we strongly suggest you consult their official documentation to resolve issues. We cannot guarantee the accuracy of the suggestions below.

### xcode

If running on OS X you should make sure that the Xcode and the Xcode command line tools are installed.

### postgres

If you are using Postgres.app 9.3 on OSX, a database user will be created with your system username. If you want to use this user account, change the `USER` and `ADMIN_USER` settings to your username under the `[postgres]` section of your Qiita config file.

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

### python

As a general rule of thumb you will want to have an updated version of Python
2.7 and an updated version of pip (`pip install -U pip` will do the trick).

H5PY is known to cause a few problems, however their [installation
instructions](http://docs.h5py.org/en/latest/build.html) are a great resource
to troubleshoot your system in case any of the steps above fail.

### matplotlib

In the event that you get `_tkinter.TclError: no display name and no $DISPLAY environment variable` error while trying to generate figures that rely on matplotlib, you should create a matplotlib rc file. This configuration file should have `backend : agg`. For more information you should visit the [matplotlib configuration](http://matplotlib.org/users/customizing.html) and [troubleshooting](http://matplotlib.org/faq/troubleshooting_faq.html#locating-matplotlib-config-dir) page.
