# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import gzip
from functools import partial
from glob import glob
from os import mkdir
from os.path import abspath, basename, dirname, exists, join, splitext
from shutil import copytree
from urllib.request import urlretrieve

from natsort import natsorted

import qiita_db as qdb
from qiita_core.exceptions import QiitaEnvironmentError
from qiita_core.qiita_settings import qiita_config, r_client

get_support_file = partial(join, join(dirname(abspath(__file__)), "support_files"))
reference_base_dir = join(qiita_config.base_data_dir, "reference")
get_reference_fp = partial(join, reference_base_dir)


SETTINGS_FP = get_support_file("qiita-db-settings.sql")
LAYOUT_FP = get_support_file("qiita-db-unpatched.sql")
POPULATE_FP = get_support_file("populate_test_db.sql")
PATCHES_DIR = get_support_file("patches")


def create_layout(test=False, verbose=False):
    r"""Builds the SQL layout

    Parameters
    ----------
    verbose : bool, optional
        If true, print the current step. Default: False.
    """
    with qdb.sql_connection.TRN:
        if verbose:
            print("Building SQL layout")
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
    print("Loading Ontology Data")
    if not exists(reference_base_dir):
        mkdir(reference_base_dir)

    fp = get_reference_fp("ontologies.sql.gz")

    if exists(fp):
        print(
            "SKIPPING download of ontologies: File already exists at %s. "
            "To download the file again, delete the existing file first." % fp
        )
    else:
        url = "ftp://ftp.microbio.me/pub/qiita/qiita_ontoandvocab.sql.gz"
        try:
            urlretrieve(url, fp)
        except Exception:
            raise IOError("Error: Could not fetch ontologies file from %s" % url)

    with qdb.sql_connection.TRN:
        with gzip.open(fp, "rb") as f:
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
    print("Downloading reference files")
    if not exists(reference_base_dir):
        mkdir(reference_base_dir)

    files = {
        "tree": (
            get_reference_fp("gg_13_8-97_otus.tree"),
            "ftp://ftp.microbio.me/greengenes_release/gg_13_8_otus/trees/97_otus.tree",
        ),
        "taxonomy": (
            get_reference_fp("gg_13_8-97_otu_taxonomy.txt"),
            "ftp://ftp.microbio.me/greengenes_release/"
            "gg_13_8_otus/taxonomy/97_otu_taxonomy.txt",
        ),
        "sequence": (
            get_reference_fp("gg_13_8-97_otus.fasta"),
            "ftp://ftp.microbio.me/greengenes_release/"
            "gg_13_8_otus/rep_set/97_otus.fasta",
        ),
    }

    for file_type, (local_fp, url) in files.items():
        # Do not download the file if it exists already
        if exists(local_fp):
            print(
                "SKIPPING %s: file already exists at %s. To "
                "download the file again, erase the existing file first"
                % (file_type, local_fp)
            )
        else:
            try:
                urlretrieve(url, local_fp)
            except Exception:
                raise IOError(
                    "Error: Could not fetch %s file from %s" % (file_type, url)
                )
    with qdb.sql_connection.TRN:
        ref = qdb.reference.Reference.create(
            "Greengenes",
            "13_8",
            files["sequence"][0],
            files["taxonomy"][0],
            files["tree"][0],
        )

        _insert_processed_params(ref)


def create_mountpoints():
    r"""In a fresh qiita setup, sub-directories under
    qiita_config.base_data_dir might not yet exist. To avoid failing in
    later steps, they are created here.
    """
    with qdb.sql_connection.TRN:
        sql = """SELECT DISTINCT mountpoint FROM qiita.data_directory
                 WHERE active = TRUE"""
        qdb.sql_connection.TRN.add(sql)
        created_subdirs = []
        for mountpoint in qdb.sql_connection.TRN.execute_fetchflatten():
            for ddid, subdir in qdb.util.get_mountpoint(mountpoint, retrieve_all=True):
                if not exists(join(qiita_config.base_data_dir, subdir)):
                    if qiita_config.test_environment:
                        # if in test mode, we want to potentially fill the
                        # new directory with according test data
                        copytree(
                            get_support_file("test_data", mountpoint),
                            join(qiita_config.base_data_dir, subdir),
                        )
                    else:
                        # in production mode, an empty directory is created
                        mkdir(join(qiita_config.base_data_dir, subdir))
                    created_subdirs.append(subdir)

        if len(created_subdirs) > 0:
            print(
                "Created %i sub-directories as 'mount points':\n%s"
                % (
                    len(created_subdirs),
                    "".join(map(lambda x: " - %s\n" % x, created_subdirs)),
                )
            )


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
        raise EnvironmentError(
            "Cannot load ontologies in a test environment! "
            "Pass --no-load-ontologies, or set "
            "TEST_ENVIRONMENT = FALSE in your "
            "configuration"
        )

    # Connect to the postgres server
    with qdb.sql_connection.TRNADMIN:
        sql = "SELECT datname FROM pg_database WHERE datname = %s"
        qdb.sql_connection.TRNADMIN.add(sql, [qiita_config.database])

        if qdb.sql_connection.TRNADMIN.execute_fetchflatten():
            raise QiitaEnvironmentError(
                "Database {0} already present on the system. You can drop it "
                "by running 'qiita-env drop'".format(qiita_config.database)
            )

    # Create the database
    print("Creating database")
    create_settings_table = True
    try:
        with qdb.sql_connection.TRNADMIN:
            qdb.sql_connection.TRNADMIN.add(
                "CREATE DATABASE %s" % qiita_config.database
            )
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
                    print("Not a test database")
                    raise
                create_settings_table = False
        else:
            raise
    qdb.sql_connection.TRNADMIN.close()

    with qdb.sql_connection.TRN:
        print("Inserting database metadata")
        test = qiita_config.test_environment
        verbose = True
        if create_settings_table:
            # Build the SQL layout into the database
            with open(SETTINGS_FP, newline=None) as f:
                qdb.sql_connection.TRN.add(f.read())
            qdb.sql_connection.TRN.execute()
            # Insert the settings values to the database
            sql = """INSERT INTO settings
                     (test, base_data_dir, base_work_dir)
                     VALUES (%s, %s, %s)"""
            qdb.sql_connection.TRN.add(
                sql, [test, qiita_config.base_data_dir, qiita_config.working_dir]
            )
            qdb.sql_connection.TRN.execute()
            create_layout(test=test, verbose=verbose)
        patch(verbose=verbose, test=test)

        if load_ontologies:
            _add_ontology_data()

            # these values can only be added if the environment is being loaded
            # with the ontologies, thus this cannot exist inside intialize.sql
            # because otherwise loading the ontologies would be a requirement
            ontology = qdb.ontology.Ontology(qdb.util.convert_to_id("ENA", "ontology"))
            ontology.add_user_defined_term("Amplicon Sequencing")

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
            args = [
                [analysis_id, p_id]
                for p_id in qdb.sql_connection.TRN.execute_fetchflatten()
            ]
            sql = """INSERT INTO qiita.analysis_portal
                        (analysis_id, portal_type_id)
                     VALUES (%s, %s)"""
            qdb.sql_connection.TRN.add(sql, args, many=True)
            qdb.sql_connection.TRN.execute()

            print("Demo user successfully created")

        if qiita_config.test_environment:
            print("Test environment successfully created")
        else:
            print("Production environment successfully created")


def drop_environment(ask_for_confirmation):
    """Drops the database specified in the configuration"""
    # The transaction has an open connection to the database, so we need
    # to close it in order to drop the environment
    qdb.sql_connection.TRN.close()
    # Connect to the postgres server
    with qdb.sql_connection.TRN:
        qdb.sql_connection.TRN.add("SELECT test FROM settings")
        try:
            is_test_environment = qdb.sql_connection.TRN.execute_fetchflatten()[0]
        except ValueError as e:
            # if settings doesn't exist then is fine to treat this as a test
            # environment and clean up
            if 'UNDEFINED_TABLE. MSG: relation "settings"' in str(e):
                is_test_environment = True
            else:
                raise
    qdb.sql_connection.TRN.close()

    if is_test_environment:
        do_drop = True
    else:
        if ask_for_confirmation:
            confirm = ""
            while confirm not in ("Y", "y", "N", "n"):
                confirm = input(
                    "THIS IS NOT A TEST ENVIRONMENT.\nProceed with drop? (y/n)"
                )

            do_drop = confirm in ("Y", "y")
        else:
            do_drop = True

    if do_drop:
        with qdb.sql_connection.TRNADMIN:
            qdb.sql_connection.TRNADMIN.add("DROP DATABASE %s" % qiita_config.database)
            qdb.sql_connection.TRNADMIN.execute()
    else:
        print("ABORTING")


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
        qdb.sql_connection.TRN.add("UPDATE settings SET current_patch = 'unpatched'")
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
        raise RuntimeError(
            "Working in a production environment. Not "
            "executing the test cleanup to keep the production "
            "database safe."
        )

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
    with qdb.sql_connection.TRN:
        qdb.sql_connection.TRN.add("SELECT current_patch FROM settings")
        current_patch = qdb.sql_connection.TRN.execute_fetchlast()
        current_sql_patch_fp = join(patches_dir, current_patch)
        corresponding_py_patch = partial(join, patches_dir, "python_patches")
        corresponding_test_sql = partial(join, patches_dir, "test_db_sql")

        sql_glob = join(patches_dir, "*.sql")
        sql_patch_files = natsorted(glob(sql_glob))

        if current_patch == "unpatched":
            next_patch_index = 0
        elif current_sql_patch_fp not in sql_patch_files:
            raise RuntimeError("Cannot find patch file %s" % current_patch)
        else:
            next_patch_index = sql_patch_files.index(current_sql_patch_fp) + 1

    if test:
        with qdb.sql_connection.TRN:
            _populate_test_db()

    # create mountpoints as subdirectories in BASE_DATA_DIR
    create_mountpoints()

    patch_update_sql = "UPDATE settings SET current_patch = %s"
    for sql_patch_fp in sql_patch_files[next_patch_index:]:
        sql_patch_filename = basename(sql_patch_fp)

        patch_prefix = splitext(basename(sql_patch_fp))[0]
        py_patch_fp = corresponding_py_patch(f"{patch_prefix}.py")
        test_sql_fp = corresponding_test_sql(f"{patch_prefix}.sql")

        with qdb.sql_connection.TRN:
            with open(sql_patch_fp, newline=None) as patch_file:
                if verbose:
                    print("\tApplying patch %s..." % sql_patch_filename)
                qdb.sql_connection.TRN.add(patch_file.read())
                qdb.sql_connection.TRN.add(patch_update_sql, [sql_patch_filename])

            if test and exists(test_sql_fp):
                if verbose:
                    print("\t\tApplying test SQL %s..." % basename(test_sql_fp))
                with open(test_sql_fp) as test_sql:
                    qdb.sql_connection.TRN.add(test_sql.read())

            qdb.sql_connection.TRN.execute()

            if exists(py_patch_fp):
                if verbose:
                    print("\t\tApplying python patch %s..." % basename(py_patch_fp))
                with open(py_patch_fp) as py_patch:
                    exec(py_patch.read(), globals())

        # before moving to jsonb for sample/prep info files (patch 69.sql),
        # one of the patches used to regenerate the sample information file
        # for the test Study (1) so a lot of the tests actually expect this.
        # Now, trying to regenerate directly in the populate_test_db might
        # require too many dev hours so the easiest is just do it here
    if test:
        qdb.study.Study(1).sample_template.generate_files()
