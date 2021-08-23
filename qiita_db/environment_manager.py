# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import abspath, dirname, join, exists, basename, splitext
from functools import partial
from os import mkdir
import gzip
from glob import glob
from natsort import natsorted

from qiita_core.exceptions import QiitaEnvironmentError
from qiita_core.qiita_settings import qiita_config, r_client
import qiita_db as qdb

from urllib.request import urlretrieve


get_support_file = partial(join, join(dirname(abspath(__file__)),
                                      'support_files'))
reference_base_dir = join(qiita_config.base_data_dir, "reference")
get_reference_fp = partial(join, reference_base_dir)


SETTINGS_FP = get_support_file('qiita-db-settings.sql')
LAYOUT_FP = get_support_file('qiita-db-unpatched.sql')
POPULATE_FP = get_support_file('populate_test_db.sql')
PATCHES_DIR = get_support_file('patches')


def create_layout(test=False, verbose=False):
    r"""Builds the SQL layout

    Parameters
    ----------
    verbose : bool, optional
        If true, print the current step. Default: False.
    """
    with qdb.sql_connection.TRN:
        if verbose:
            print('Building SQL layout')
        # Create the schema
        with open(LAYOUT_FP, newline=None) as f:
            qdb.sql_connection.TRN.add(f.read())
        qdb.sql_connection.TRN.execute()


def _populate_test_db():
    with qdb.sql_connection.TRN:
        with open(POPULATE_FP, newline=None) as f:
            qdb.sql_connection.TRN.add(f.read())
        qdb.sql_connection.TRN.execute()


def _add_ontology_data():
    print('Loading Ontology Data')
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
        except Exception:
            raise IOError("Error: Could not fetch ontologies file from %s" %
                          url)

    with qdb.sql_connection.TRN:
        with gzip.open(fp, 'rb') as f:
            qdb.sql_connection.TRN.add(f.read())
        qdb.sql_connection.TRN.execute()


def _insert_processed_params(ref):
    with qdb.sql_connection.TRN:
        sortmerna_sql = """INSERT INTO qiita.processed_params_sortmerna
                           (reference_id, sortmerna_e_value, sortmerna_max_pos,
                            similarity, sortmerna_coverage, threads)
                           VALUES
                           (%s, 1, 10000, 0.97, 0.97, 1)"""
        qdb.sql_connection.TRN.add(sortmerna_sql, [ref._id])
        qdb.sql_connection.TRN.execute()


def _download_reference_files():
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

    for file_type, (local_fp, url) in files.items():
        # Do not download the file if it exists already
        if exists(local_fp):
            print("SKIPPING %s: file already exists at %s. To "
                  "download the file again, erase the existing file first" %
                  (file_type, local_fp))
        else:
            try:
                urlretrieve(url, local_fp)
            except Exception:
                raise IOError("Error: Could not fetch %s file from %s" %
                              (file_type, url))
    with qdb.sql_connection.TRN:
        ref = qdb.reference.Reference.create(
            'Greengenes', '13_8', files['sequence'][0],
            files['taxonomy'][0], files['tree'][0])

        _insert_processed_params(ref)


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
    with qdb.sql_connection.TRNADMIN:
        sql = 'SELECT datname FROM pg_database WHERE datname = %s'
        qdb.sql_connection.TRNADMIN.add(sql, [qiita_config.database])

        if qdb.sql_connection.TRNADMIN.execute_fetchflatten():
            raise QiitaEnvironmentError(
                "Database {0} already present on the system. You can drop it "
                "by running 'qiita-env drop'".format(qiita_config.database))

    # Create the database
    print('Creating database')
    create_settings_table = True
    try:
        with qdb.sql_connection.TRNADMIN:
            qdb.sql_connection.TRNADMIN.add(
                'CREATE DATABASE %s' % qiita_config.database)
            qdb.sql_connection.TRNADMIN.execute()
        qdb.sql_connection.TRN.close()
    except ValueError as error:
        # if database exists ignore
        msg = 'database "%s" already exists' % qiita_config.database
        if msg in str(error):
            print("Database exits, let's make sure it's test")
            with qdb.sql_connection.TRN:
                # Insert the settings values to the database
                sql = """SELECT test FROM settings"""
                qdb.sql_connection.TRN.add(sql)
                is_test = qdb.sql_connection.TRN.execute_fetchlast()
                if not is_test:
                    print('Not a test database')
                    raise
                create_settings_table = False
        else:
            raise
    qdb.sql_connection.TRNADMIN.close()

    with qdb.sql_connection.TRN:
        print('Inserting database metadata')
        test = qiita_config.test_environment
        verbose = True
        if create_settings_table:
            # Build the SQL layout into the database
            with open(SETTINGS_FP, newline=None) as f:
                qdb.sql_connection.TRN.add(f.read())
            qdb.sql_connection.TRN.execute()

            # Insert the settings values to the database
            sql = """INSERT INTO settings
                     (test, base_data_dir, base_work_dir, trq_owner,
                     trq_poll_val, trq_dependency_q_cnt)
                     VALUES (%s, %s, %s, %s, %s, %s)"""
            qdb.sql_connection.TRN.add(
                sql, [test,
                      qiita_config.base_data_dir,
                      qiita_config.working_dir,
                      qiita_config.trq_owner,
                      qiita_config.trq_poll_val,
                      qiita_config.trq_dependency_q_cnt])
            qdb.sql_connection.TRN.execute()
            create_layout(test=test, verbose=verbose)

        patch(verbose=verbose, test=test)

        if load_ontologies:
            _add_ontology_data()

            # these values can only be added if the environment is being loaded
            # with the ontologies, thus this cannot exist inside intialize.sql
            # because otherwise loading the ontologies would be a requirement
            ontology = qdb.ontology.Ontology(
                qdb.util.convert_to_id('ENA', 'ontology'))
            ontology.add_user_defined_term('Amplicon Sequencing')

        if download_reference:
            _download_reference_files()

        # we don't do this if it's a test environment because populate.sql
        # already adds this user...
        if add_demo_user and not qiita_config.test_environment:
            sql = """INSERT INTO qiita.qiita_user (email, user_level_id,
                                                   password, name, affiliation,
                                                   address, phone)
                VALUES
                ('demo@microbio.me', 4,
                '$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe',
                'Demo', 'Qiita Dev', '1345 Colorado Avenue', '303-492-1984')"""
            qdb.sql_connection.TRN.add(sql)
            sql = """INSERT INTO qiita.analysis (email, name, description,
                                                 dflt, analysis_status_id)
                     VALUES ('demo@microbio.me', 'demo@microbio.me-dflt',
                             'dflt', 't', 1)
                     RETURNING analysis_id"""
            qdb.sql_connection.TRN.add(sql)
            analysis_id = qdb.sql_connection.TRN.execute_fetchlast()

            # Add default analysis to all portals
            sql = "SELECT portal_type_id FROM qiita.portal_type"
            qdb.sql_connection.TRN.add(sql)
            args = [[analysis_id, p_id]
                    for p_id in qdb.sql_connection.TRN.execute_fetchflatten()]
            sql = """INSERT INTO qiita.analysis_portal
                        (analysis_id, portal_type_id)
                     VALUES (%s, %s)"""
            qdb.sql_connection.TRN.add(sql, args, many=True)
            qdb.sql_connection.TRN.execute()

            print('Demo user successfully created')

        if qiita_config.test_environment:
            print('Test environment successfully created')
        else:
            print('Production environment successfully created')


def drop_environment(ask_for_confirmation):
    """Drops the database specified in the configuration
    """
    # The transaction has an open connection to the database, so we need
    # to close it in order to drop the environment
    qdb.sql_connection.TRN.close()
    # Connect to the postgres server
    with qdb.sql_connection.TRN:
        qdb.sql_connection.TRN.add("SELECT test FROM settings")
        is_test_environment = qdb.sql_connection.TRN.execute_fetchflatten()[0]
    qdb.sql_connection.TRN.close()

    if is_test_environment:
        do_drop = True
    else:
        if ask_for_confirmation:
            confirm = ''
            while confirm not in ('Y', 'y', 'N', 'n'):
                confirm = input("THIS IS NOT A TEST ENVIRONMENT.\n"
                                "Proceed with drop? (y/n)")

            do_drop = confirm in ('Y', 'y')
        else:
            do_drop = True

    if do_drop:
        with qdb.sql_connection.TRNADMIN:
            qdb.sql_connection.TRNADMIN.add(
                'DROP DATABASE %s' % qiita_config.database)
            qdb.sql_connection.TRNADMIN.execute()
    else:
        print('ABORTING')


def drop_and_rebuild_tst_database(drop_labcontrol=False):
    """Drops the qiita schema and rebuilds the test database

       Parameters
       ----------
       drop_labcontrol : bool
           Whether or not to drop labcontrol
    """
    with qdb.sql_connection.TRN:
        r_client.flushdb()
        # Drop the schema, note that we are also going to drop labman because
        # if not it will raise an error if you have both systems on your
        # computer due to foreing keys
        if drop_labcontrol:
            qdb.sql_connection.TRN.add("DROP SCHEMA IF EXISTS labman CASCADE")
        qdb.sql_connection.TRN.add("DROP SCHEMA IF EXISTS qiita CASCADE")
        # Set the database to unpatched
        qdb.sql_connection.TRN.add(
            "UPDATE settings SET current_patch = 'unpatched'")
        # Create the database and apply patches
        create_layout(test=True)
        patch(test=True)

        qdb.sql_connection.TRN.execute()


def reset_test_database(wrapped_fn):
    """Decorator that drops the qiita schema, rebuilds and repopulates the
    schema with test data, then executes wrapped_fn
    """

    def decorated_wrapped_fn(*args, **kwargs):
        # Reset the test database
        drop_and_rebuild_tst_database(True)
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
    with qdb.sql_connection.TRN:
        qdb.sql_connection.TRN.add("SELECT test FROM settings")
        test_db = qdb.sql_connection.TRN.execute_fetchflatten()[0]

    if not qiita_config.test_environment or not test_db:
        raise RuntimeError("Working in a production environment. Not "
                           "executing the test cleanup to keep the production "
                           "database safe.")

    # wrap the dummy function and execute it
    @reset_test_database
    def dummyfunc():
        pass
    dummyfunc()


def patch(patches_dir=PATCHES_DIR, verbose=False, test=False):
    """Patches the database schema based on the SETTINGS table

    Pulls the current patch from the settings table and applies all subsequent
    patches found in the patches directory.
    """
    # we are going to open and close 2 main transactions; this is a required
    # change since patch 68.sql where we transition to jsonb for all info
    # files. The 2 main transitions are: (1) get the current settings,
    # (2) each patch in their independent transaction
    with qdb.sql_connection.TRN:
        qdb.sql_connection.TRN.add("SELECT current_patch FROM settings")
        current_patch = qdb.sql_connection.TRN.execute_fetchlast()
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

    patch_update_sql = "UPDATE settings SET current_patch = %s"

    for sql_patch_fp in sql_patch_files[next_patch_index:]:
        sql_patch_filename = basename(sql_patch_fp)

        py_patch_fp = corresponding_py_patch(
            splitext(basename(sql_patch_fp))[0] + '.py')
        py_patch_filename = basename(py_patch_fp)

        # patch 43.sql is when we started testing patches, then in patch
        # 68.sql is when we transitioned to jsonb for the info files; let's do
        # this in its own transition
        if sql_patch_filename == '68.sql' and test:
            with qdb.sql_connection.TRN:
                _populate_test_db()

        with qdb.sql_connection.TRN:
            with open(sql_patch_fp, newline=None) as patch_file:
                if verbose:
                    print('\tApplying patch %s...' % sql_patch_filename)
                qdb.sql_connection.TRN.add(patch_file.read())
                qdb.sql_connection.TRN.add(
                    patch_update_sql, [sql_patch_filename])

            qdb.sql_connection.TRN.execute()

            if exists(py_patch_fp):
                if verbose:
                    print('\t\tApplying python patch %s...'
                          % py_patch_filename)
                with open(py_patch_fp) as py_patch:
                    exec(py_patch.read(), globals())

        # before moving to jsonb for sample/prep info files (patch 69.sql),
        # one of the patches used to regenerate the sample information file
        # for the test Study (1) so a lot of the tests actually expect this.
        # Now, trying to regenerate directly in the populate_test_db might
        # require too many dev hours so the easiest is just do it here
        # UPDATE 01/25/2021: moving to 81.sql as we added timestamps to
        #                    prep info files
        if test and sql_patch_filename == '81.sql':
            qdb.study.Study(1).sample_template.generate_files()
