# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import abspath, dirname, join
from psycopg2 import connect
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DFLT_BASE_DATA_FOLDER = join(dirname(abspath(__file__)),
                             'support_files/test_data')
SETTINGS_FP = join(dirname(abspath(__file__)),
                   'support_files/qiita-db-settings.sql')
LAYOUT_FP = join(dirname(abspath(__file__)), 'support_files/qiita-db.sql')
INITIALIZE_FP = join(dirname(abspath(__file__)),
                     'support_files/initialize.sql')
POPULATE_FP = join(dirname(abspath(__file__)),
                   'support_files/populate_test_db.sql')


def make_test_environment(base_data_dir, user, password, host):
    """Creates a test database environment.

    Creates a new database called `qiita_test` tailored for testing purposes
    and initializes the `settings` table of such database

    Parameters
    ----------
    base_data_dir : str
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
    cur.execute("INSERT INTO settings (test, base_data_dir) VALUES "
                "(TRUE, '%s')" % base_data_dir)

    conn.commit()
    cur.close()
    conn.close()


def make_production_environment():
    """TODO: Not implemented"""
    raise NotImplementedError()
