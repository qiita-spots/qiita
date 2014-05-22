# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import abspath, dirname, join

from qiita_db.sql_connection import SQLConnectionHandler
from qiita_core.config import qiita_config


def build_test_database(setup_fn):
    """Decorator that initializes the test database with the schema and initial
    test data and executes setup_fn
    """
    conn_handler = SQLConnectionHandler()

    # Get the paths to the SQL files with the schema layout, the database
    # initialization and the test data
    setup_dp = join(dirname(abspath(__file__)), '../qiita_db/setup')
    layout_fp = join(setup_dp, 'qiita-db.sql')
    init_fp = join(setup_dp, 'initialize.sql')
    populate_fp = join(setup_dp, 'populate_test_db.sql')

    def decorated_setup_fn(*args, **kwargs):
        # Create the schema
        with open(layout_fp, 'U') as f:
            conn_handler.execute(f.read())
        # Initialize the database
        with open(init_fp, 'U') as f:
            conn_handler.execute(f.read())
        # Populate the database
        with open(populate_fp, 'U') as f:
            conn_handler.execute(f.read())
        # Execute the setup function
        return setup_fn(*args, **kwargs)

    return decorated_setup_fn


def drop_test_database(teardown_fn):
    """Decorator that drops the qiita schema, leaving the test database in its
    initial state, and then executes teardown_fn
    """
    conn_handler = SQLConnectionHandler()

    def decorated_teardown_fn(*args, **kwargs):
        # Drop the schema
        conn_handler.execute("DROP SCHEMA qiita CASCADE")
        # Execute the teardown function
        return teardown_fn(*args, **kwargs)

    return decorated_teardown_fn


def qiita_test_checker():
    """Decorator that allows the execution of all methods in a test class only
    and only if Qiita is set up to work in a test environment.

    Raises
    ------
    RuntimeError
        If Qiita is set up to work in a production environment
    """
    def class_modifier(cls):
        # First, we check that we are not in a production environment
        conn_handler = SQLConnectionHandler()
        # It is possible that we are connecting to a production database
        test_db = conn_handler.execute_fetchone("SELECT test FROM settings")[0]
        # Or the loaded configuration file belongs to a production environment
        if not qiita_config.test_environment or not test_db:
            raise RuntimeError("Working in a production environment. Not "
                               "executing the tests to keep the production "
                               "database safe.")

        # Now, we decorate the setup and teardown functions
        class DecoratedClass(cls):
            @build_test_database
            def setUp(self):
                super(DecoratedClass, self).setUp()

            @drop_test_database
            def tearDown(self):
                super(DecoratedClass, self).tearDown()

        return DecoratedClass
    return class_modifier