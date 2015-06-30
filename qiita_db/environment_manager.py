# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from qiita_db.ontology import Ontology
from qiita_db.util import convert_to_id
from os.path import abspath, dirname, join, exists, basename, splitext
from functools import partial
from os import mkdir
import gzip
from glob import glob

from future import standard_library
from future.utils import viewitems

from qiita_core.exceptions import QiitaEnvironmentError
from qiita_core.qiita_settings import qiita_config
from .sql_connection import SQLConnectionHandler
from .reference import Reference
from natsort import natsorted

with standard_library.hooks():
    from urllib.request import urlretrieve


get_support_file = partial(join, join(dirname(abspath(__file__)),
                                      'support_files'))
reference_base_dir = join(qiita_config.base_data_dir, "reference")
get_reference_fp = partial(join, reference_base_dir)


SETTINGS_FP = get_support_file('qiita-db-settings.sql')
LAYOUT_FP = get_support_file('qiita-db-unpatched.sql')
POPULATE_FP = get_support_file('populate_test_db.sql')
PATCHES_DIR = get_support_file('patches')


def _check_db_exists(db, conn_handler):
    r"""Checks if the database db exists on the postgres server

    Parameters
    ----------
    db : str
        The database
    conn_handler : SQLConnectionHandler
        The connection to the database
    """
    dbs = conn_handler.execute_fetchall('SELECT datname FROM pg_database')

    # It's a list of tuples, so just create the tuple to check if exists
    return (db,) in dbs


def create_layout_and_patch(conn, verbose=False):
    r"""Builds the SQL layout and applies all the patches

    Parameters
    ----------
    conn : SQLConnectionHandler
        The handler connected to the DB
    verbose : bool, optional
        If true, print the current step. Default: False.
    """
    if verbose:
        print('Building SQL layout')
    # Create the schema
    with open(LAYOUT_FP, 'U') as f:
        conn.execute(f.read())

    if verbose:
        print('Patching Database...')
    patch(verbose=verbose)


def _populate_test_db(conn):
    print('Populating database with demo data')
    with open(POPULATE_FP, 'U') as f:
        conn.execute(f.read())


def _add_ontology_data(conn):
    print ('Loading Ontology Data')
    if not exists(reference_base_dir):
        mkdir(reference_base_dir)

    fp = get_reference_fp('ontologies.sql.gz')

    if exists(fp):
        print("SKIPPING download of ontologies: File already exists at %s. "
              "To download the file again, delete the existing file first."
              % fp)
    else:
        url = 'ftp://ftp.microbio.me/pub/qiita/qiita_ontoandvocab.sql.gz'
        try:
            urlretrieve(url, fp)
        except:
            raise IOError("Error: Could not fetch ontologies file from %s" %
                          url)

    with gzip.open(fp, 'rb') as f:
        conn.execute(f.read())


def _insert_processed_params(conn, ref):
    sortmerna_sql = """INSERT INTO qiita.processed_params_sortmerna
                       (reference_id, sortmerna_e_value, sortmerna_max_pos,
                        similarity, sortmerna_coverage, threads)
                       VALUES
                       (%s, 1, 10000, 0.97, 0.97, 1)"""

    conn.execute(sortmerna_sql, [ref._id])


def _download_reference_files(conn):
    print('Downloading reference files')
    if not exists(reference_base_dir):
        mkdir(reference_base_dir)

    files = {'tree': (get_reference_fp('gg_13_8-97_otus.tree'),
                      'ftp://ftp.microbio.me/greengenes_release/'
                      'gg_13_8_otus/trees/97_otus.tree'),
             'taxonomy': (get_reference_fp('gg_13_8-97_otu_taxonomy.txt'),
                          'ftp://ftp.microbio.me/greengenes_release/'
                          'gg_13_8_otus/taxonomy/97_otu_taxonomy.txt'),
             'sequence': (get_reference_fp('gg_13_8-97_otus.fasta'),
                          'ftp://ftp.microbio.me/greengenes_release/'
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

    ref = Reference.create('Greengenes', '13_8', files['sequence'][0],
                           files['taxonomy'][0], files['tree'][0])

    _insert_processed_params(conn, ref)


def make_environment(load_ontologies, download_reference, add_demo_user):
    r"""Creates the new environment specified in the configuration

    Parameters
    ----------
    load_ontologies : bool
        Whether or not to retrieve and unpack ontology information
    download_reference : bool
        Whether or not to download greengenes reference files
    add_demo_user : bool
        Whether or not to add a demo user to the database with username
        demo@microbio.me and password "password"

    Raises
    ------
    IOError
        If `download_reference` is true but one of the files cannot be
        retrieved
    QiitaEnvironmentError
        If the environment already exists
    """
    if load_ontologies and qiita_config.test_environment:
        raise EnvironmentError("Cannot load ontologies in a test environment! "
                               "Pass --no-load-ontologies, or set "
                               "TEST_ENVIRONMENT = FALSE in your "
                               "configuration")

    # Connect to the postgres server
    admin_conn = SQLConnectionHandler(admin='admin_without_database')

    # Check that it does not already exists
    if _check_db_exists(qiita_config.database, admin_conn):
        raise QiitaEnvironmentError(
            "Database {0} already present on the system. You can drop it "
            "by running 'qiita-env drop'".format(qiita_config.database))

    # Create the database
    print('Creating database')
    admin_conn.autocommit = True
    admin_conn.execute('CREATE DATABASE %s' % qiita_config.database)
    admin_conn.autocommit = False

    del admin_conn

    # Connect to the postgres server, but this time to the just created db
    conn = SQLConnectionHandler()

    print('Inserting database metadata')
    # Build the SQL layout into the database
    with open(SETTINGS_FP, 'U') as f:
        conn.execute(f.read())

    # Insert the settings values to the database
    conn.execute("INSERT INTO settings (test, base_data_dir, base_work_dir) "
                 "VALUES (%s, %s, %s)",
                 (qiita_config.test_environment, qiita_config.base_data_dir,
                  qiita_config.working_dir))

    create_layout_and_patch(conn, verbose=True)

    if load_ontologies:
        _add_ontology_data(conn)

        # these values can only be added if the environment is being loaded
        # with the ontologies, thus this cannot exist inside intialize.sql
        # because otherwise loading the ontologies would be a requirement
        ontology = Ontology(convert_to_id('ENA', 'ontology'))
        ontology.add_user_defined_term('Amplicon Sequencing')

    if download_reference:
        _download_reference_files(conn)

    # we don't do this if it's a test environment because populate.sql
    # already adds this user...
    if add_demo_user and not qiita_config.test_environment:
        conn.execute("""
            INSERT INTO qiita.qiita_user (email, user_level_id, password,
                                          name, affiliation, address, phone)
            VALUES
            ('demo@microbio.me', 4,
             '$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe',
             'Demo', 'Qitta Dev', '1345 Colorado Avenue', '303-492-1984')""")
        analysis_id = conn.execute_fetchone("""
            INSERT INTO qiita.analysis (email, name, description, dflt,
                                        analysis_status_id)
            VALUES
            ('demo@microbio.me', 'demo@microbio.me-dflt', 'dflt', 't', 1)
            RETURNING analysis_id
        """)[0]

        # Add default analysis to all portals
        args = []
        sql = "SELECT portal_type_id FROM qiita.portal_type"
        for portal_id in conn.execute_fetchall(sql):
            args.append([analysis_id, portal_id[0]])

        sql = """INSERT INTO qiita.analysis_portal
                 (analysis_id, portal_type_id)
                 VALUES (%s, %s)"""
        conn.execute_many(sql, args)

        print('Demo user successfully created')

    if qiita_config.test_environment:
        _populate_test_db(conn)
        print('Test environment successfully created')
    else:
        print('Production environment successfully created')


def drop_environment(ask_for_confirmation):
    """Drops the database specified in the configuration
    """
    # Connect to the postgres server
    conn = SQLConnectionHandler()
    settings_sql = "SELECT test FROM settings"
    is_test_environment = conn.execute_fetchone(settings_sql)[0]

    del conn

    if is_test_environment:
        do_drop = True
    else:
        if ask_for_confirmation:
            confirm = ''
            while confirm not in ('Y', 'y', 'N', 'n'):
                confirm = raw_input("THIS IS NOT A TEST ENVIRONMENT.\n"
                                    "Proceed with drop? (y/n)")

            do_drop = confirm in ('Y', 'y')
        else:
            do_drop = True

    if do_drop:
        SQLConnectionHandler.close()
        admin_conn = SQLConnectionHandler(admin='admin_without_database')
        admin_conn.autocommit = True
        admin_conn.execute('DROP DATABASE %s' % qiita_config.database)
        admin_conn.autocommit = False
    else:
        print('ABORTING')


def drop_and_rebuild_tst_database(conn_handler):
    """Drops the qiita schema and rebuilds the test database

    Parameters
    ----------
    conn_handler : SQLConnectionHandler
        The handler connected to the database
    """
    # Drop the schema
    conn_handler.execute("DROP SCHEMA IF EXISTS qiita CASCADE")
    # Set the database to unpatched
    conn_handler.execute("UPDATE settings SET current_patch = 'unpatched'")
    # Create the database and apply patches
    create_layout_and_patch(conn_handler)
    # Populate the database
    with open(POPULATE_FP, 'U') as f:
        conn_handler.execute(f.read())


def reset_test_database(wrapped_fn):
    """Decorator that drops the qiita schema, rebuilds and repopulates the
    schema with test data, then executes wrapped_fn
    """
    conn_handler = SQLConnectionHandler()

    def decorated_wrapped_fn(*args, **kwargs):
        # Reset the test database
        drop_and_rebuild_tst_database(conn_handler)
        # Execute the wrapped function
        return wrapped_fn(*args, **kwargs)

    return decorated_wrapped_fn


def clean_test_environment():
    r"""Cleans the test database environment.

    In case that the test database is dirty (i.e. the 'qiita' schema is
    present), this cleans it up by dropping the 'qiita' schema and
    re-populating it.
    """
    # First, we check that we are not in a production environment
    conn_handler = SQLConnectionHandler()
    # It is possible that we are connecting to a production database
    test_db = conn_handler.execute_fetchone("SELECT test FROM settings")[0]
    # Or the loaded configuration file belongs to a production environment
    if not qiita_config.test_environment or not test_db:
        raise RuntimeError("Working in a production environment. Not "
                           "executing the test cleanup to keep the production "
                           "database safe.")

    # wrap the dummy function and execute it
    @reset_test_database
    def dummyfunc():
        pass
    dummyfunc()


def patch(patches_dir=PATCHES_DIR, verbose=False):
    """Patches the database schema based on the SETTINGS table

    Pulls the current patch from the settings table and applies all subsequent
    patches found in the patches directory.
    """
    conn = SQLConnectionHandler()

    current_patch = conn.execute_fetchone(
        "select current_patch from settings")[0]
    current_sql_patch_fp = join(patches_dir, current_patch)
    corresponding_py_patch = partial(join, patches_dir, 'python_patches')

    sql_glob = join(patches_dir, '*.sql')
    sql_patch_files = natsorted(glob(sql_glob))

    if current_patch == 'unpatched':
        next_patch_index = 0
    elif current_sql_patch_fp not in sql_patch_files:
        raise RuntimeError("Cannot find patch file %s" % current_patch)
    else:
        next_patch_index = sql_patch_files.index(current_sql_patch_fp) + 1

    patch_update_sql = "update settings set current_patch = %s"

    for sql_patch_fp in sql_patch_files[next_patch_index:]:
        sql_patch_filename = basename(sql_patch_fp)
        py_patch_fp = corresponding_py_patch(
            splitext(basename(sql_patch_fp))[0] + '.py')
        py_patch_filename = basename(py_patch_fp)
        conn.create_queue(sql_patch_filename)
        with open(sql_patch_fp, 'U') as patch_file:
            if verbose:
                print('\tApplying patch %s...' % sql_patch_filename)
            conn.add_to_queue(sql_patch_filename, patch_file.read())
            conn.add_to_queue(sql_patch_filename, patch_update_sql,
                              [sql_patch_filename])

        conn.execute_queue(sql_patch_filename)

        if exists(py_patch_fp):
            if verbose:
                print('\t\tApplying python patch %s...' % py_patch_filename)
            execfile(py_patch_fp)
