# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from os.path import abspath, dirname, join
from functools import partial
from os import remove, close
from os.path import exists
from tempfile import mkstemp
from ftplib import FTP
import gzip

from future import standard_library
from future.utils import viewitems
with standard_library.hooks():
    from urllib.request import urlretrieve
from psycopg2 import connect
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from qiita_core.exceptions import QiitaEnvironmentError
from qiita_core.qiita_settings import qiita_config

get_support_file = partial(join, join(dirname(abspath(__file__)),
                                      'support_files'))
get_reference_fp = partial(join, qiita_config.base_data_dir, "reference")


DFLT_BASE_WORK_FOLDER = get_support_file('work_data')
SETTINGS_FP = get_support_file('qiita-db-settings.sql')
LAYOUT_FP = get_support_file('qiita-db.sql')
INITIALIZE_FP = get_support_file('initialize.sql')
POPULATE_FP = get_support_file('populate_test_db.sql')
ENVIRONMENTS = {'demo': 'qiita_demo', 'test': 'qiita_test',
                'production': 'qiita'}
CLUSTERS = ['demo', 'reserved', 'general']


def _check_db_exists(db, cursor):
    r"""Checks if the database db exists on the postgres server

    Parameters
    ----------
    db : str
        The database
    cursor : psycopg2.cursor
        The cursor connected to the database
    """
    cursor.execute('SELECT datname FROM pg_database')
    # It's a list of tuples, so just create the tuple to check if exists
    return (db,) in cursor.fetchall()


def _create_layout_and_init_db(cur):
    print('Building SQL layout')
    # Create the schema
    with open(LAYOUT_FP, 'U') as f:
        cur.execute(f.read())

    print('Initializing database')
    # Initialize the database
    with open(INITIALIZE_FP, 'U') as f:
        cur.execute(f.read())


def _populate_test_db(cur):
    print('Populating database with demo data')
    with open(POPULATE_FP, 'U') as f:
        cur.execute(f.read())


def _add_ontology_data(cur):
    print ('Loading Ontology Data')
    ontos_fp, f = download_and_unzip_file(
        host='thebeast.colorado.edu',
        filename='/pub/qiita/qiita_ontoandvocab.sql.gz')

    # f will be None if the file already exists
    if f is None:
        print("SKIPPING ontologies: File already exists at %s. To download "
              "the file again, delete the existing file first.")
    else:
        cur.execute(f.read())
        f.close()
        remove(ontos_fp)


def _download_reference_files(cur, base_data_dir):
    print('Downloading reference files')

    files = {'tree': (get_reference_fp('gg_13_8-97_otus.tree'),
                      'ftp://thebeast.colorado.edu/greengenes_release/'
                      'gg_13_8_otus/trees/97_otus.tree'),
             'taxonomy': (get_reference_fp('gg_13_8-97_otu_taxonomy.txt'),
                          'ftp://thebeast.colorado.edu/greengenes_release/'
                          'gg_13_8_otus/taxonomy/97_otu_taxonomy.txt'),
             'sequence': (get_reference_fp('gg_13_8-97_otus.fasta'),
                          'ftp://thebeast.colorado.edu/greengenes_release/'
                          'gg_13_8_otus/rep_set/97_otus.fasta')}

    for file_type, (local_fp, url) in viewitems(files):
        # Do not download the file if it exists already
        if exists(local_fp):
            print("SKIPPING %s: file already exists at %s. To "
                  "download the file again, erase the existing file first" %
                  (file_type, local_fp))
        else:
            try:
                urlretrieve(url, local_fp)
            except:
                raise IOError("Error: Could not fetch %s file from %s" %
                              (file_type, url))


def make_environment(env, base_data_dir, base_work_dir, user, password, host,
                     load_ontologies, download_reference):
    r"""Creates the new environment `env`

    Parameters
    ----------
    env : {demo, test, production}
        The environment to create
    base_data_dir : str
        the path to the directory where all user data is stored
    base_work_dir : str
        The path to the directory to use for working space
    user : str
        The postgres user to use
    password : str
        The password for the above postgres user
    host : str
        The postgrs host
    load_ontologies : bool
        Whether or not to retrieve and unpack ontology information
    download_reference : bool
        Whether or not to download greengenes reference files

    Raises
    ------
    ValueError
        If `env` not recognized
    IOError
        If `download_reference` is true but one of the files cannot be
        retrieved
    QiitaEnvironmentError
        If the environment already exists
    """
    if env not in ENVIRONMENTS:
        raise ValueError("Environment %s not recognized. Available "
                         "environments are %s" % (env, ENVIRONMENTS.keys()))
    # Connect to the postgres server
    conn = connect(user=user, host=host, password=password)
    # Set the isolation level to AUTOCOMMIT so we can execute a create database
    # sql quary
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    # Get the cursor
    cur = conn.cursor()
    # Check that it does not already exists
    if _check_db_exists(ENVIRONMENTS[env], cur):
        raise QiitaEnvironmentError(
            "Environment {0} already present on the system. You can drop it "
            "by running qiita_env drop {0}".format(env))

    # Create the database
    print('Creating database')
    cur.execute('CREATE DATABASE %s' % ENVIRONMENTS[env])
    cur.close()
    conn.close()

    # Connect to the postgres server, but this time to the just created db
    conn = connect(user=user, host=host, password=password,
                   database=ENVIRONMENTS[env])
    cur = conn.cursor()

    print('Inserting database metadata')
    # Build the SQL layout into the database
    with open(SETTINGS_FP, 'U') as f:
        cur.execute(f.read())

    # Insert the settings values to the database
    cur.execute("INSERT INTO settings (test, base_data_dir, base_work_dir) "
                "VALUES (%s, %s, %s)",
                (qiita_config.test_environment, base_data_dir,
                 base_work_dir))

    _create_layout_and_init_db(cur)

    if load_ontologies:
        _add_ontology_data(cur)

    if download_reference:
        _download_reference_files(cur, base_data_dir)

    if env == 'demo':
        # add demo user
        cur.execute("""
            INSERT INTO qiita.qiita_user (email, user_level_id, password,
                                          name, affiliation, address, phone)
            VALUES
            ('demo@microbio.me', 4,
             '$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe',
             'Demo', 'Qitta Dev', '1345 Colorado Avenue', '303-492-1984')""")

        print('Demo environment successfully created')
    elif env == "test":
        _populate_test_db(cur)
        print('Test environment successfully created')
    elif env == "production":
        print('Production environment successfully created')

    # Commit all the changes and close the connections
    conn.commit()
    cur.close()
    conn.close()


def drop_environment(admin_user, admin_password, host):
    r"""Drops the database specified in the configuration

    Parameters
    ----------
    admin_user : str
        The admin postgres user to use
    admin_password : str
        The password for the admin postgres user
    host : str
        The host where the postgres server is running

    Raises
    ------
    QiitaEnvironmentError
        The If the environment is not present on the system
    """
    # Connect to the postgres server
    conn = connect(user=admin_user, host=host, password=admin_password)
    # Set the isolation level to AUTOCOMMIT so we can execute a
    # drop database sql query
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    # Drop the database
    cur = conn.cursor()

    if not _check_db_exists(qiita_config.database, cur):
        raise QiitaEnvironmentError(
            "Database {0} not present on the system. You can create it "
            "by running 'qiita_env make'".format(qiita_config.database))

    settings_sql = "SELECT test FROM qiita.settings"
    cur.execute(settings_sql)
    is_test_environment = cur.fetchone(settings_sql)[0]

    if is_test_environment:
        do_drop=True
    else:
        confirm = ''
        while confirm not in ('Y', 'y', 'N', 'n'):
            confirm = raw_input("THIS IS NOT A TEST ENVIRONMENT.\n"
                                "Proceed with drop? (y/n)")

        do_drop = confirm in ('Y', 'y')

    if do_drop:
        cur.execute('DROP DATABASE %s' % qiita_config.database)
    else:
        print('ABORTING')

    # Close cursor and connection
    cur.close()
    conn.close()


def clean_test_environment(user, password, host):
    r"""Cleans the test database environment.

    In case that the test database is dirty (i.e. the 'qiita' schema is
    present), this cleans it up by dropping the 'qiita' schema and
    re-populating it.

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


def download_and_unzip_file(host, filename):
    """Function downloads though ftp and unzips a file

    Parameters
    -----------
    host : str
        the location of the ftp server that is hosting the file
    filename : str
        the location of the file on the ftp server to download
    """
    fp = get_reference_fp('ontologies.tgz')

    if exists(fp):
        return fp, None

    ftp = FTP(host)
    ftp.login()
    cmd = 'RETR %s' % filename
    ftp.retrbinary(cmd, open(fp, 'wb').write)
    f = gzip.open(fp, 'rb')

    return fp, f
