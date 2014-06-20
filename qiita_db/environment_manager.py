# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from tempfile import mkdtemp
from tarfile import open as taropen
from gzip import open as gzopen
from os import remove
from os.path import abspath, dirname, join
from shutil import rmtree, move
from functools import partial
try:
    from urllib import urlretrieve
except ImportError:  # python3
    from urllib.request import urlretrieve

from psycopg2 import connect
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from qiita_db.util import get_db_files_base_dir

get_support_file = partial(join, join(dirname(abspath(__file__)),
                                      'support_files'))

DFLT_BASE_DATA_FOLDER = get_support_file('test_data')
DFLT_BASE_WORK_FOLDER = get_support_file('work_data')
SETTINGS_FP = get_support_file('qiita-db-settings.sql')
LAYOUT_FP = get_support_file('qiita-db.sql')
INITIALIZE_FP = get_support_file('initialize.sql')
POPULATE_FP = get_support_file('populate_test_db.sql')



def make_test_environment(base_data_dir, base_work_dir, user, password, host):
    r"""Creates a test database environment.

    Creates a new database called `qiita_test` tailored for testing purposes
    and initializes the `settings` table of such database

    Parameters
    ----------
    base_data_dir : str
    base_work_dir : str
    """
    # Connect to the postgres server
    conn = connect(user=user, host=host, password=password)
    # Set the isolation level to AUTOCOMMIT so we can execute a
    # create database sql query
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    # Create the database
    cur = conn.cursor()
    cur.execute('CREATE DATABASE qiita_test')
    cur.close()
    conn.close()

    # Connect to the postgres server, but this time to the just created db
    conn = connect(user=user, host=host, password=password,
                   database='qiita_test')
    cur = conn.cursor()

    # Build the SQL layout into the database
    with open(SETTINGS_FP, 'U') as f:
        cur.execute(f.read())

    # Insert the settings values to the database
    cur.execute("INSERT INTO settings (test, base_data_dir, base_work_dir) "
                "VALUES (TRUE, '%s', '%s')" % (base_data_dir, base_work_dir))

    conn.commit()
    cur.close()
    conn.close()


def clean_test_environment(user, password, host):
    r"""Cleans the test database environment.

    In case that the test database is dirty (i.e. the 'qiita' schema is
    present), this cleans it up by dropping the 'qiita' schema.

    Parameters
    ----------
    user : str
        The postgres user to connect to the server
    password : str
        The password of the user
    host : str
        The host where the postgres server is running
    """
    # Connect to the postgres server
    conn = connect(user=user, host=host, password=password,
                   database='qiita_test')
    # Get the cursor
    cur = conn.cursor()
    # Drop the qiita schema
    cur.execute("DROP SCHEMA qiita CASCADE")
    # Commit the changes
    conn.commit()
    # Close cursor and connections
    cur.close()
    conn.close()


def drop_test_environment(user, password, host):
    r"""Drops the test environment.

    If the `settings` table is modified, the test database environment should
    be rebuilt. This command allows to drop the old one.

    Parameters
    ----------
    user : str
        The postgres user to connect to the server
    password : str
        The password of the user
    host : str
        The host where the postgres server is running
    """
    # Connect to the postgres server
    conn = connect(user=user, host=host, password=password)
    # Set the isolation level to AUTOCOMMIT so we can execute a
    # drop database sql query
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    # Drop the database
    cur = conn.cursor()
    cur.execute('DROP DATABASE qiita_test')
    # Close cursor and connection
    cur.close()
    conn.close()


def make_demo_environment(base_data_dir, base_work_dir, user, password, host):
    r"""Creates a demo database environment.

    Creates a new database called `qiita` tailored for the HMP2 demo.
    """
    # Connect to the postgres server
    conn = connect(user=user, host=host, password=password)
    # Set the isolation level to AUTOCOMMIT so we can execute a
    # create database sql query
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    # Create the database
    cur = conn.cursor()
    cur.execute('CREATE DATABASE qiita_demo')
    cur.close()
    conn.close()

    # Connect to the postgres server, but this time to the just created db
    conn = connect(user=user, host=host, password=password,
                   database='qiita_demo')
    cur = conn.cursor()

    # Build the SQL layout into the database
    with open(SETTINGS_FP, 'U') as f:
        cur.execute(f.read())

    # Insert the settings values to the database
    cur.execute("INSERT INTO settings (test, base_data_dir, base_work_dir) "
                "VALUES (FALSE, '%s', '%s')" % (base_data_dir, base_work_dir))

    # Create the schema
    with open(LAYOUT_FP, 'U') as f:
        cur.execute(f.read())

    # Initialize the database
    with open(INITIALIZE_FP, 'U') as f:
        cur.execute(f.read())

    # Populate the database
    with open(POPULATE_FP, 'U') as f:
        cur.execute(f.read())

    # Commit all the changes and close the connections
    conn.commit()
    cur.close()
    conn.close()

    # download files from thebeast
    url = ("ftp://thebeast.colorado.edu/pub/QIIME_DB_Public_Studies/study_1001"
           "_split_library_seqs_and_mapping.tgz")
    outdir = mkdtemp()
    basedir = join(outdir, "study_1001_split_library_seqs_and_mapping/")
    try:
        urlretrieve(url, join(outdir, "study_1001.tar.gz"))
    except:
        raise IOError("Error: DOWNLOAD FAILED")
        rmtree(outdir)

    # untar the files
    with taropen(join(outdir, "study_1001.tar.gz")) as tar:
        tar.extractall(outdir)
    # un-gzip sequence file
    with gzopen(join(basedir, "study_1001_split_library_seqs.fna.gz")) as gz:
        with open(join(basedir, "seqs.fna"), 'w') as fout:
            fout.write(gz.read())

    # copy the preprocessed and procesed data to the study
    dbbase = get_db_files_base_dir()
    remove(join(dbbase, "processed_data/study_1001_closed_reference_otu"
           "_table.biom"))
    remove(join(dbbase, "preprocessed_data/seqs.fna"))
    move(join(basedir, "study_1001_closed_reference_otu_table.biom"),
         join(dbbase, "processed_data"))
    move(join(basedir, "seqs.fna"), join(dbbase, "preprocessed_data"))

    # clean up after ourselves
    rmtree(outdir)


def drop_demo_environment(user, password, host):
    r"""Drops the demo environment.

    Parameters
    ----------
    user : str
        The postgres user to connect to the server
    password : str
        The password of the user
    host : str
        The host where the postgres server is running
    """
    base = get_db_files_base_dir()
    # Connect to the postgres server
    conn = connect(user=user, host=host, password=password)
    # Set the isolation level to AUTOCOMMIT so we can execute a
    # drop database sql query
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    # Drop the database
    cur = conn.cursor()
    cur.execute('DROP DATABASE qiita_demo')
    # Close cursor and connection
    cur.close()
    conn.close()

    # wipe the overwriiten test files so empty as on repo
    with open(join(base, "preprocessed_data/seqs.fna"), 'w') as fout:
        fout.write("\n")
    with open(join(base, "processed_data/study_1001_closed_reference_otu_"
              "table.biom"), 'w') as fout:
        fout.write("\n")


def make_production_environment():
    """TODO: Not implemented"""
    raise NotImplementedError()
