r"""
SQL Connection object (:mod:`qiita_db.sql_connection`)
======================================================

.. currentmodule:: qiita_db.sql_connection

This modules provides wrappers for the psycopg2 module to allow easy use of
transaction blocks and SQL execution/data retrieval.

Classes
-------

.. autosummary::
   :toctree: generated/

   SQLConnectionHandler
   Transaction
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from contextlib import contextmanager
from itertools import chain
from functools import partial
from tempfile import mktemp
from datetime import date, time, datetime
import re

from psycopg2 import (connect, ProgrammingError, Error as PostgresError,
                      OperationalError)
from psycopg2.extras import DictCursor
from psycopg2.extensions import (
    ISOLATION_LEVEL_AUTOCOMMIT, ISOLATION_LEVEL_READ_COMMITTED)

from qiita_core.qiita_settings import qiita_config


class SQLConnectionHandler(object):
    """Postgres DB connection object

    Parameters
    ----------
    admin : {'no_admin', 'admin_with_database', 'admin_without_database'},
             optional
        Whether or not to connect as the admin user. Options other than
        `no_admin` depend on admin credentials in the qiita configuration. If
        `admin_without_database`, the connection will be made to the server
        specified in the qiita configuration, but not to a specific database.
        If `admin_with_database`, then a connection will be made to the server
        and database specified in the qiita config.
    """
    # From http://osdir.com/ml/sqlalchemy/2011-05/msg00094.html
    TYPE_CODES = pg_types = {
        16: bool,
        17: bytes,
        19: str,  # name type
        20: int,
        21: int,
        23: int,
        25: str,  # TEXT type
        26: float,  # oid type
        700: float,
        701: float,
        829: str,  # MACADDR type
        1042: str,  # CHAR type
        1043: str,  # VARCHAR type
        1082: date,
        1083: time,
        1114: datetime,
        1184: datetime,  # timestamp w/ tz
        1700: float,
        2275: str,  # cstring
    }

    _user_args = {
        'user': qiita_config.user,
        'password': qiita_config.password,
        'database': qiita_config.database,
        'host': qiita_config.host,
        'port': qiita_config.port}

    _admin_args = {
        'user': qiita_config.admin_user,
        'password': qiita_config.admin_password,
        'database': qiita_config.database,
        'host': qiita_config.host,
        'port': qiita_config.port}

    _admin_nodb_args = {
        'user': qiita_config.admin_user,
        'password': qiita_config.admin_password,
        'host': qiita_config.host,
        'port': qiita_config.port}

    _user_conn = None
    _admin_conn = None
    _admin_nodb_conn = None

    _conn_map = {'no_admin': '_user_conn',
                 'admin_with_database': '_admin_conn',
                 'admin_without_database': '_admin_nodb_conn'}

    _args_map = {'no_admin': '_user_args',
                 'admin_with_database': '_admin_args',
                 'admin_without_database': '_admin_nodb_args'}

    def __init__(self, admin='no_admin'):
        if admin not in ('no_admin', 'admin_with_database',
                         'admin_without_database'):
            raise ValueError("admin takes only {'no_admin', "
                             "'admin_with_database', or "
                             "'admin_without_database'}")

        self.admin = admin

        self._conn_attr = self._conn_map[self.admin]
        self._args_attr = self._args_map[self.admin]
        self._conn_args = getattr(SQLConnectionHandler, self._args_attr)
        self._connection = getattr(SQLConnectionHandler, self._conn_attr)
        self._open_connection()

        # queues for transaction blocks. Format is {str: list} where the str
        # is the queue name and the list is the queue of SQL commands
        self.queues = {}

    def _open_connection(self):
        # if the connection has been created and is not closed
        if self._connection is not None and self._connection.closed == 0:
            return

        try:
            setattr(SQLConnectionHandler, self._conn_attr,
                    connect(**self._conn_args))
        except OperationalError as e:
            # catch threee known common exceptions and raise runtime errors
            try:
                etype = e.message.split(':')[1].split()[0]
            except IndexError:
                # we recieved a really unanticipated error without a colon
                etype = ''
            if etype == 'database':
                etext = ('This is likely because the database `%s` has not '
                         'been created or has been dropped.' %
                         qiita_config.database)
            elif etype == 'role':
                etext = ('This is likely because the user string `%s` '
                         'supplied in your configuration file `%s` is '
                         'incorrect or not an authorized postgres user.' %
                         (qiita_config.user, qiita_config.conf_fp))
            elif etype == 'Connection':
                etext = ('This is likely because postgres isn\'t '
                         'running. Check that postgres is correctly '
                         'installed and is running.')
            else:
                # we recieved a really unanticipated error with a colon
                etext = ''
            ebase = ('An OperationalError with the following message occured'
                     '\n\n\t%s\n%s For more information, review `INSTALL.md`'
                     ' in the Qiita installation base directory.')
            raise RuntimeError(ebase % (e.message, etext))
        else:
            self._connection = getattr(SQLConnectionHandler, self._conn_attr)

    @staticmethod
    def close():
        if SQLConnectionHandler._user_conn is not None:
            SQLConnectionHandler._user_conn.close()

        if SQLConnectionHandler._admin_conn is not None:
            SQLConnectionHandler._admin_conn.close()

        if SQLConnectionHandler._admin_nodb_conn is not None:
            SQLConnectionHandler._admin_nodb_conn.close()

    @contextmanager
    def get_postgres_cursor(self):
        """ Returns a Postgres cursor

        Returns
        -------
        pgcursor : psycopg2.cursor

        Raises
        ------
        RuntimeError
            if the cursor cannot be created
        """
        self._open_connection()

        try:
            with self._connection.cursor(cursor_factory=DictCursor) as cur:
                yield cur
        except PostgresError as e:
            raise RuntimeError("Cannot get postgres cursor! %s" % e)

    @property
    def autocommit(self):
        """If the isolation level of the DB connection is autocommit"""
        return self._connection.isolation_level == ISOLATION_LEVEL_AUTOCOMMIT

    @autocommit.setter
    def autocommit(self, value):
        """(De)activate the autocommit isolation level of the DB connection

        Parameters
        ----------
        value : bool
            If true, the isolation level of the DB connection is set to
            autocommit. Otherwise, it is set to read committed.

        Raises
        ------
        TypeError
            If `value` is not a boolean
        """
        if not isinstance(value, bool):
            raise TypeError("The value for autocommit should be a boolean")
        level = (ISOLATION_LEVEL_AUTOCOMMIT if value
                 else ISOLATION_LEVEL_READ_COMMITTED)
        self._connection.set_isolation_level(level)

    def _check_sql_args(self, sql_args):
        """ Checks that sql_args have the correct type

        Parameters
        ----------
        sql_args : object
            The SQL arguments

        Raises
        ------
        TypeError
            If sql_args does not have the correct type
        """
        # Check that sql arguments have the correct type
        if sql_args and type(sql_args) not in [tuple, list, dict]:
            raise TypeError("sql_args should be tuple, list or dict. Found %s "
                            % type(sql_args))

    @contextmanager
    def _sql_executor(self, sql, sql_args=None, many=False):
        """Executes an SQL query

        Parameters
        ----------
        sql : str
            The SQL query
        sql_args : tuple, list or dict, optional
            The arguments for the SQL query
        many : bool, optional
            If true, performs an execute many call

        Returns
        -------
        pgcursor : psycopg2.cursor
            The cursor in which the SQL query was executed

        Raises
        ------
        ValueError
            If there is some error executing the SQL query
        """
        # Check that sql arguments have the correct type
        if many:
            for args in sql_args:
                self._check_sql_args(args)
        else:
            self._check_sql_args(sql_args)

        # Execute the query
        with self.get_postgres_cursor() as cur:
            executor = partial(cur.executemany if many else cur.execute,
                               sql, sql_args)
            try:
                executor()
                yield cur
            except PostgresError as e:
                self._connection.rollback()
                raise ValueError("Error running SQL query: %s\nARGS: %s\n"
                                 "Error: %s" % (sql, str(sql_args), e))
            else:
                self._connection.commit()

    def execute(self, sql, sql_args=None):
        """Executes an SQL query with no results

        Parameters
        ----------
        sql : str
            The SQL query
        sql_args : tuple, list or dict, optional
            The arguments for the SQL query

        Notes
        -----
        From psycopg2 documentation, only variable values should be bound
        via sql_args, it shouldn't be used to set table or field names. For
        those elements, ordinary string formatting should be used before
        running execute.

        References
        ----------
        http://initd.org/psycopg/docs/usage.html
        """
        with self._sql_executor(sql, sql_args):
            pass

    def executemany(self, sql, sql_args_list):
        """Executes an executemany SQL query with no results

        Parameters
        ----------
        sql : str
            The SQL query
        sql_args : list of tuples, lists or dicts
            The arguments for the SQL query

        Notes
        -----
        From psycopg2 documentation, only variable values should be bound
        via sql_args, it shouldn't be used to set table or field names. For
        those elements, ordinary string formatting should be used before
        running execute.

        References
        ----------
        http://initd.org/psycopg/docs/usage.html
        """
        with self._sql_executor(sql, sql_args_list, True):
            pass

    def execute_fetchone(self, sql, sql_args=None):
        """Executes a fetchone SQL query

        Parameters
        ----------
        sql : str
            The SQL query
        sql_args : tuple, list or dict, optional
            The arguments for the SQL query

        Returns
        -------
        Tuple
            The results of the fetchone query

        Notes
        -----
        From psycopg2 documentation, only variable values should be bound
        via sql_args, it shouldn't be used to set table or field names. For
        those elements, ordinary string formatting should be used before
        running execute.

        References
        ----------
        http://initd.org/psycopg/docs/usage.html
        """
        with self._sql_executor(sql, sql_args) as pgcursor:
            result = pgcursor.fetchone()

        return result

    def execute_fetchall(self, sql, sql_args=None):
        """Executes a fetchall SQL query

        Parameters
        ----------
        sql : str
            The SQL query
        sql_args : tuple, list or dict, optional
            The arguments for the SQL query

        Returns
        ------
        list of tuples
            The results of the fetchall query

        Notes
        -----
        From psycopg2 documentation, only variable values should be bound
        via sql_args, it shouldn't be used to set table or field names. For
        those elements, ordinary string formatting should be used before
        running execute.

        References
        ----------
        http://initd.org/psycopg/docs/usage.html
        """
        with self._sql_executor(sql, sql_args) as pgcursor:
            result = pgcursor.fetchall()

        return result


class Transaction(object):
    """Encapsulates a DB transaction

    A transaction is defined by a series of consecutive queries that need to
    be applied to the database as a single block.

    Parameters
    ----------
    name : str
        Name of the transaction.
    """

    _regex = re.compile("^{(\d+):(\d+):(\d+)}$")

    def __init__(self, name):
        # The name is useful for debugging, since we can identify the
        # failed queue in errors
        self._name = name
        self._queries = []
        self._results = []
        self._index = 0
        self._conn_handler = SQLConnectionHandler()

    def _raise_execution_error(self, sql, sql_args, error):
        """Rollbacks the current transaction and raises a useful error

        The error message contains the name of the transaction, the failed
        query, the arguments of the failed query and the error generated.

        Raises
        ------
        ValueError
        """
        self.rollback()
        raise ValueError(
            "Error running SQL query in transaction %s:\n"
            "Query: %s\nArguments: %s\nError: %s\n"
            % (self._name, sql, str(sql_args), str(error)))

    def _replace_placeholders(self, sql, sql_args):
        """Replaces the placeholder in `sql_args` with the actual value

        Parameters
        ----------
        sql : str
            The SQL query
        sql_args : list or None
            The arguments of the SQL query

        Returns
        -------
        tuple of (str, list of objects)
            The input SQL query (unmodified) and the SQL arguments with the
            placeholder (if any) substituted with the actual value of the
            previous query
        """
        if sql_args is not None:
            for pos, arg in enumerate(sql_args):
                # Check if we have a placeholder
                if isinstance(arg, str):
                    placeholder = self._regex.search(arg)
                    if placeholder:
                        # We do have a placeholder, get the indexes
                        # Query index
                        q_idx = int(placeholder.group(1))
                        # Row index
                        r_idx = int(placeholder.group(2))
                        # Value index
                        v_idx = int(placeholder.group(3))
                        try:
                            sql_args[pos] = self._results[q_idx][r_idx][v_idx]
                        except IndexError:
                            # A previous query that was expected to retrieve
                            # some data from the DB did not return as many
                            # values as expected
                            self._raise_execution_error(
                                sql, sql_args,
                                "The placeholder {%d:%d:%d} does not match to "
                                "any previous result"
                                % (q_idx, r_idx, v_idx))
                        except TypeError:
                            # The query that the placeholder is pointing to
                            # is not expected to retrieve any value
                            # (e.g. an INSERT w/o RETURNING clause)
                            self._raise_execution_error(
                                sql, sql_args,
                                "The placeholder {%d:%d:%d} is referring to "
                                "an SQL query that does not retrieve data"
                                % (q_idx, r_idx, v_idx))
        return sql, sql_args

    def add(self, sql, sql_args=None, many=False):
        """Add an sql query to the transaction

        If the current query needs a result of a previous query in the
        transaction, a placeholder of the form '{#:#:#}' can be used. The first
        number is the index of the previous SQL query in the transaction, the
        second number is the row from that query result and the third number is
        the index of the value within the query result row.
        The placeholder will be replaced by the actual value at execution time.

        Parameters
        ----------
        sql : str
            The sql query
        sql_args : list of objects, optional
            The arguments to the sql query
        many : bool, optional
            Whether or not we should add the query multiple times to the
            transaction

        Raises
        ------
        TypeError
            If `sql_args` is provided and is not a list

        Notes
        -----
        If `many` is true, `sql_args` should be a list of lists, in which each
        list contains the parameters for the sql query
        """
        if not many:
            sql_args = [sql_args]

        for args in sql_args:
            if args and isinstance(args, list):
                raise TypeError("sql_args should be a list. Found %s"
                                % type(args))
            self._queries.append((sql, args))

    def execute(self, commit=True):
        """Executes the transaction

        Parameters
        ----------
        commit : bool, optional
            Whether if the transaction should be committed or not. Defaults
            to true.

        Returns
        -------
        list of DictCursor
            The results of all the SQL queries in the transaction
        """
        with self._conn_handler.get_postgres_cursor() as cur:
            for sql, sql_args in self._queries:
                sql, sql_args = self._replace_placeholders(sql, sql_args)

                # Execute the current SQL command
                try:
                    cur.execute(sql, sql_args)
                except Exception as e:
                    # We catch any exception as we want to make sure that we
                    # rollback every time that something went wrong
                    self._raise_execution_error(sql, sql_args, e)

                try:
                    res = cur.fetchall()
                except ProgrammingError as e:
                    # At this execution point, we don't know if the sql query
                    # that we executed should retrieve values from the database
                    # If the query was not supposed to retrieve any value
                    # (e.g. an INSERT without a RETURNING clause), it will
                    # raise a ProgrammingError. Otherwise it will just return
                    # an empty list
                    res = None
                except PostgresError as e:
                    # Some other error happened during the execution of the
                    # query, so we need to rollback
                    self._raise_execution_error(sql, sql_args, e)

                # Store the results of the current query
                self._results.append(res)

        # wipe out the already executed queries
        self._index += len(self._queries)
        self._queries = []

        if commit:
            self.commit()

        return self._results

    def commit(self):
        """Commits the transaction"""
        self._conn_handler._connection.commit()

    def rollback(self):
        """Rollbacks the transaction"""
        self._conn_handler._connection.rollback()

    @property
    def index(self):
        """Returns the index of the next query that will be added"""
        return self._index + len(self._queries)
