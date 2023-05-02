
Qiita installation
==================

Qiita is pip installable, but depends on specific versions of python and non-python packages that must be installed first. We strongly recommend using virtual environments; a popular solution to manage them is [miniconda](http://conda.pydata.org/miniconda.html), a lightweight version of the virtual environment, python distribution, and package manager anaconda. These instructions will be based on miniconda.

## Install and setup miniconda

Download the appropriate installer [here](https://repo.anaconda.com/miniconda/) corresponding to your operating system and execute it.

Next, ensure conda is up-to-date.

```bash
conda update conda
```

### Create a conda environment for Qiita

Setup a virtual environment in conda named `qiita` by executing the following:

```bash
conda config --add channels conda-forge
conda create -q --yes -n qiita python=3.9 pip libgfortran numpy nginx
```

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

If you don't see this output, your `$PATH` variable was setup incorrectly or you haven't restarted your shell. Consult the [conda documentation](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html).

As long as you are in the active qiita environment, commands such as `pip install` or `python` will refer to and be contained within this virtual environment.

When you want to deactivate your current conda environment, e.g. to return to a different project or back to your global python and pip packages, run:

```bash
source deactivate
```


Install the non-python dependencies
-----------------------------------

* [PostgreSQL](http://www.postgresql.org/download/) (currently using v13)
* [redis-server](http://redis.io) (we have tested most extensively with 2.8.17)
* [webdis] (https://github.com/nicolasff/webdis) (latest version should be fine but we have tested the most with 9ee6fe2 - Feb 6, 2016)

There are several options to install these dependencies depending on your needs:

- **We suggest installing the exact versions in these instructions by following the instructions of the provided links and making them globally available in your machine. However, this might interfere with other apps that might require different versions.** 
- Alternatively, you could install them via conda. However, the conda repository may not have the exact versions of these dependencies that you want.
- You could setup a full development environment with [Vagrant](https://www.vagrantup.com/), and continue using conda under it to primarily manage python dependencies. Note that we don't cover Vagrant in these instructions.

### PostgreSQL installation on Linux
The following instructions have been adapted from [this site](https://computingforgeeks.com/how-to-install-postgresql-13-on-ubuntu/) and tested on Ubuntu v20.04.4 for Postgres v13.

First, ensure that you have updated packages and reboot the system with:
```bash
sudo apt update && sudo apt -y full-upgrade
[ -f /var/run/reboot-required ] && sudo reboot -f
```
You can reboot the system with `sudo reboot` in case any packages were updated.

Next, we need to add the Postgres repository to our system:
```bash
sudo apt update
sudo apt install curl gpg gnupg2 software-properties-common apt-transport-https lsb-release ca-certificates
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc|sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" |sudo tee  /etc/apt/sources.list.d/pgdg.list
```
Adding the repository has added many different packages, which allows us to now install Postgres v13 with the following commands:
```bash
sudo apt update
sudo apt install postgresql-13 postgresql-client-13
```
Now, we need to reconfigure the `pg_hba.conf` file and change all occurrences of `md5` and `peer` to `trust`. You can access the file with:
```bash
sudo vim /etc/postgresql/13/main/pg_hba.conf
```
To make sure all changes have been reflected, restart the Postgres server:
```bash
sudo service postgresql restart
```
Installing Postgres is now complete. Note that you will need to start the Postgres server every time you start the Qiita server. You can do this with the following command:
```bash
sudo service postgresql start
```
### PostgreSQL installation on Mac OS X

For Mac OS X, you can install postgres through the [Postgres.app](https://postgresapp.com/downloads.html). These instructions were tested with the Postgres.app v9.5 and v13.

You'll then need to ensure that the postgres binaries (for example, ``psql``) are in your executable search path (``$PATH`` environment variable). If you are using Postgres.app on OS X, you can do this by running the following, though you may have to replace`~/.bash_profile`with `~/.zshrc` if you're using zshell rather than the built-in bash, and you may have to change the version number `Versions/9.3/` to the exact one that you are installing:

```bash
echo 'export PATH="$PATH:/Applications/Postgres.app/Contents/Versions/9.5/bin/"' >> ~/.bash_profile
source ~/.bash_profile
```

### Redis-server installation using Homebrew (Mac OS X, Linux)

Assuming you have [homebrew](http://brew.sh) installed, you can install the latest version of the redis-server as follows:

```bash
brew update
brew install homebrew/versions/redis28
```
### Redis-server installation using apt-get (Linux)

Alternatively, you can sudo install redis:
```bash
sudo apt-get install redis-server
```

### webdis

Note that this package is OPTIONAL and this is the only package that assumes that Qiita is already installed (due to library dependencies). Also, that the general suggestion is to have 2 redis servers running, one for webdis/redbiom and the other for Qiita. The reason for multiple redis servers is so that the redbiom cache can be flushed without impacting the operation of the qiita server itself.

The following instructions install, compile and pre-populates the redbiom redis DB so we assume that redis is running on the default port and that Qiita is fully installed as the redbiom package is installed with Qiita.

```
git clone https://github.com/nicolasff/webdis
pushd webdis
make
./webdis &
popd
# note that this assumes that Qiita is already installed
fp=`python -c 'import qiita_db; print qiita_db.__file__'`
qdbd=`dirname $fp`
redbiom admin scripts-writable
redbiom admin create-context --name "qiita-test" --description "qiita-test context"
redbiom admin load-sample-metadata --metadata ${qdbd}/support_files/test_data/templates/1_19700101-000000.txt
redbiom admin load-sample-metadata-search --metadata ${qdbd}/support_files/test_data/templates/1_19700101-000000.txt
redbiom admin load-sample-data --table ${qdbd}/support_files/test_data/processed_data/1_study_1001_closed_reference_otu_table.biom --context qiita-test --tag 1
```

Install Qiita development version and its python dependencies
-------------------------------------------------------------

Clone the git repository with the development version of Qiita into your current directory:

```bash
git clone https://github.com/qiita-spots/qiita.git
```

Navigate to the cloned directory and ensure your conda environment is active:

```bash
cd qiita
source activate qiita
```
If you are using Ubuntu or a Windows Subsystem for Linux (WSL), you will need to ensure that you have a C++ compiler and that development libraries and include files for PostgreSQL are available. Type `cc` into your system to ensure that it doesn't result in `program not found`. The following commands will install a C++ compiler and  `libpq-dev`:
```bash
sudo apt install gcc              # alternatively, you can install clang instead
sudo apt-get install libpq-dev
```
Install Qiita (this occurs through setuptools' `setup.py` file in the qiita directory):

```bash
pip install . --no-binary redbiom
```
Note that if you get any errors or warnings with 'certifi', you can add the `--ignore-installed` tag to the command above.

At this point, Qiita will be installed and the system will start. However,
you will need to install plugins in order to process any kind of data. For a list
of available plugins, visit the [Qiita Spots](https://github.com/qiita-spots)
github organization. Each of the plugins have their own installation instructions, we
suggest looking at each individual .travis.yml file to see detailed installation
instructions. Note that the most common plugins are:
- [qtp-biom](https://github.com/qiita-spots/qtp-biom)
- [qtp-target-gene](https://github.com/qiita-spots/qtp-target-gene)
- [qp-target-gene](https://github.com/qiita-spots/qp-target-gene)

## Configure Qiita

After these commands are executed, you will need to:

Move the Qiita sample configuration file to a different directory by executing:

```bash
 cp ./qiita_core/support_files/config_test.cfg ~/.qiita_config_test.cfg
```

Note that you will need to change `BASE_URL = https://localhost:8383` to `BASE_URL = https://localhost:21174` in the new copy of the configuration file if you are not using NGINX. Additionally, you will also need to change all URLs that start with `/home/runner/work/qiita/qiita/...` into wherever your qiita directory is (e.g. `/home/<username>/qiita/...`).


Set your `QIITA_CONFIG_FP` environment variable to point to that file (into `.bashrc` if using bash; `.zshrc` if using zshell):

```bash
  echo "export QIITA_CONFIG_FP=$HOME/.qiita_config_test.cfg" >> ~/.bashrc
  source ~/.bashrc
  # Re-enable conda environment for qiita
  source activate qiita
```

Update paths in the newly copied configuration file to match your settings, e.g. replace /home/travis/ with your user home directory.

If you are working on WSL, you will need to start the redis server with the following command before making a test environment:
```bash
redis-server --daemonize yes --port 7777
```
Next, make a test environment:

```bash
qiita-env make --no-load-ontologies
```

Finally, redbiom relies on the REDBIOM_HOST environment variable to set the URL to query. By default is set to Qiita redbiom public repository. To change it you could do:

```bash
export REDBIOM_HOST=http://my_host.com:7379
```

## Confirgure NGINX and supervisor

(NGINX)[https://www.nginx.com/] is not a requirement for Qiita development but it's highly recommended for deploys as this will allow us
to have multiple workers. Note that we are already installing (NGINX)[https://www.nginx.com/] within the Qiita conda environment; also,
that Qiita comes with an example (NGINX)[https://www.nginx.com/]  config file: `qiita_pet/nginx_example.conf`, which is used in the Travis builds.

Now, (supervisor)[https://github.com/Supervisor/supervisor] will allow us to start all the workers we want based on its configuration file; and we
need that both the (NGINX)[https://www.nginx.com/] and (supervisor)[https://github.com/Supervisor/supervisor] config files to match. For our Travis
testing we are creating 3 workers: 21174 for master and 21175-6 as a regular workers.

If you are using (NGINX)[https://www.nginx.com/] via conda, you are going to need to create the NGINX folder within the environment; thus run:

```bash
mkdir -p ${CONDA_PREFIX}/var/run/nginx/
```

## Start Qiita

Start postgres (instructions vary depending on operating system and install method).

Next, start redis server (the command may differ depending on your operating system and install location):

```bash
redis-server --port 7777
```

Start the qiita server:

```bash
# this builds documentation before starting the server
# alternatively: qiita pet webserver --no-build-docs start
qiita pet webserver start
```

If all the above commands executed correctly, you should be able to access Qiita by going in your browser to https://localhost:21174 if you are not using NGINX, or https://localhost:8383 if you are using NGINX, to login use `test@foo.bar` and `password` as the credentials. (In the future, we will have a *single user mode* that will allow you to use a local Qiita server without logging in. You can track progress on this on issue [#920](https://github.com/biocore/qiita/issues/920).)



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

### Apple Silicon Mac (M1/M2)

#### `no such file or directory` or `fatal error: file not found`

M1 and M2 macs have a new feature for homebrew where homebrew is not installed to the path `usr/local/bin` like Intel Macs are, but to `opt/homebrew/bin`. Since some old code likely hasn't been updated yet, this error could possibly be from the code looking into the old Intel Mac path. Make that homebrew libraries are being searched for in the `opt/homebrew/lib` path.

More information on this error can be found [here](https://earthly.dev/blog/homebrew-on-m1/).


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

Install the appropriate channel name that corresponds to your platform. For example, for Mac OS X 64-bit this would be:

`conda install --channel https://conda.anaconda.org/OpenMDAO libgfortran`

Now you can re-run your `conda create` command:

`conda create [previous parameters go here] --channel OpenMDAO/libgfortran`

### python

As a general rule of thumb you will want to have an updated version of Python 3.6.

H5PY is known to cause a few problems, however their [installation
instructions](http://docs.h5py.org/en/latest/build.html) are a great resource
to troubleshoot your system in case any of the steps above fail.

### matplotlib

In the event that you get `_tkinter.TclError: no display name and no $DISPLAY environment variable` error while trying to generate figures that rely on matplotlib, you should create a matplotlib rc file. This configuration file should have `backend : agg`. For more information you should visit the [matplotlib configuration](http://matplotlib.org/users/customizing.html) and [troubleshooting](http://matplotlib.org/faq/troubleshooting_faq.html#locating-matplotlib-config-dir) page.
