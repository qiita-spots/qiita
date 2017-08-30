r"""
SQL Connection object (:mod:`qiita_db.sql_connection`)
======================================================

.. currentmodule:: qiita_db.sql_connection

This modules provides wrappers for the psycopg2 module to allow easy use of
transaction blocks and SQL execution/data retrieval.

This module provides the variable TRN, which is the transaction available
to use in the system. The singleton pattern is applied and this works as long
as the system remains single-threaded.

Classes
-------

.. autosummary::
   :toctree: generated/

   SQLConnectionHandler
   Transaction

Examples
--------

* Querying

In order to perform any query in the database you first need to import the
`TRN` variable available in this module:

>>> from qiita_db.sql_connection import TRN

The `TRN` variable is an instance of the `Transaction` object. All queries
should be executed through this object to ensure atomicity. To perform any
query you first need to add the query to the transaction and then execute the
transaction:

>>> with TRN:
...     TRN.add("SELECT 42")
...     res = TRN.execute()
>>> res
[[[42]]]

The `execute` function returns the values of all the queries in the transaction
object. This requires three layers of nesting: (1) the query (2) the result
rows in a given query and (3) the result columns in a given row.

* Data retrieval

Multiple auxiliary functions exist for easy SQL result retrieval:

Getting the first value of the last SQL query
>>> with TRN:
...     TRN.add("SELECT 42")
...     res = TRN.execute_fetchlast()
>>> res
42

Getting the results of the last SQL query
>>> with TRN:
...     TRN.add("SELECT 42")
...     res = TRN.execute_fetchindex()
>>> res
[[42]]

Getting the results of the specified SQL query
>>> with TRN:
...     TRN.add("SELECT 42")
...     TRN.add("SELECT 43")
...     # The index 0 corresponds to the first query in the transaction
...     res = TRN.execute_fetchindex(0)
>>> res
[[42]]

Getting the results of the last SQL query flattened
>>> with TRN:
...     TRN.add("SELECT 42, 43, 44")
...     res = TRN.execute_fetchflatten()
>>> res
[42, 43, 44]

Getting the results of the specified SQL query flattened
>>> with TRN:
...     TRN.add("SELECT 42, 43, 44")
...     TRN.add("SELECT 42")
...     res = TRN.execute_fetchflatten(0)
>>> res
[42, 43, 44]

* Transactions

Transaction blocks are created through the same `TRN` variable exported in this
module. You can add as many SQL commands as you want and execute all of them at
once, and it will return the results of all the SQL commands. `TRN` should be
used as a context manager, and it autocommits the transaction once the last
context is exited, as long as no error was generated inside the context, in
which case a rollback is executed.

>>> with TRN:
...     TRN.add("SELECT 42")
...     TRN.add("SELECT 43")
...     res = TRN.execute()  # The transaction is not committed here
>>> # The transaction committed here
>>> res
[[[42]], [[43]]]

You can have nested transactions and they will not commit until the first
transaction (represented by entering to the context) is exited:

>>> with TRN:
...     TRN.add("SELECT 42")
...     with TRN:
...         TRN.add("SELECT 43")
...         res = TRN.execute()
...     # The transaction is still not committed
...     TRN.add("SELECT 44")
...     res = TRN.execute()
>>> # The transactions committed here
>>> res
[[[42]], [[43]], [[44]]]
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
from functools import partial, wraps
from datetime import date, time, datetime

from psycopg2 import (connect, ProgrammingError, Error as PostgresError,
                      OperationalError, errorcodes)
from psycopg2.extras import DictCursor
from psycopg2.extensions import (
    ISOLATION_LEVEL_AUTOCOMMIT, ISOLATION_LEVEL_READ_COMMITTED,
    TRANSACTION_STATUS_IDLE)

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
                raise ValueError("Error running SQL: %s. MSG: %s\n" % (
                    errorcodes.lookup(e.pgcode), e.message))
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


def _checker(func):
    """Decorator to check that methods are executed inside the context"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._contexts_entered == 0:
            raise RuntimeError(
                "Operation not permitted. Transaction methods can only be "
                "invoked within the context manager.")
        return func(self, *args, **kwargs)
    return wrapper


class Transaction(object):
    """A context manager that encapsulates a DB transaction

    A transaction is defined by a series of consecutive queries that need to
    be applied to the database as a single block.

    Raises
    ------
    RuntimeError
        If the transaction methods are invoked outside a context.

    Notes
    -----
    When the execution leaves the context manager, any remaining queries in
    the transaction will be executed and committed.
    """
    def __init__(self):
        self._queries = []
        self._results = []
        self._contexts_entered = 0
        self._connection = None
        self._post_commit_funcs = []
        self._post_rollback_funcs = []

    def _open_connection(self):
        # If the connection already exists and is not closed, don't do anything
        if self._connection is not None and self._connection.closed == 0:
            return

        try:
            self._connection = connect(user=qiita_config.user,
                                       password=qiita_config.password,
                                       database=qiita_config.database,
                                       host=qiita_config.host,
                                       port=qiita_config.port)
        except OperationalError as e:
            # catch three known common exceptions and raise runtime errors
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

    def close(self):
        if self._connection is not None:
            self._connection.close()

    @contextmanager
    def _get_cursor(self):
        """Returns a postgres cursor

        Returns
        -------
        psycopg2.cursor
            The psycopg2 cursor

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
            raise RuntimeError("Cannot get postgres cursor: %s" % e)

    def __enter__(self):
        self._open_connection()
        self._contexts_entered += 1
        return self

    def _clean_up(self, exc_type):
        print '\n\n\n\n-->', exc_type '\n\n\n'
        if exc_type is not None:
            # An exception occurred during the execution of the transaction
            # Make sure that we leave the DB w/o any modification
            self.rollback()
        elif self._queries:
            # There are still queries to be executed, execute them
            # It is safe to use the execute method here, as internally is
            # wrapped in a try/except and rollbacks in case of failure
            self.execute()
            self.commit()
        elif self._connection.get_transaction_status() != \
                TRANSACTION_STATUS_IDLE:
            # There are no queries to be executed, however, the transaction
            # is still not committed. Commit it so the changes are not lost
            self.commit()

    def __exit__(self, exc_type, exc_value, traceback):
        # We only need to perform some action if this is the last context
        # that we are entering
        if self._contexts_entered == 1:
            # We need to wrap the entire function in a try/finally because
            # at the end we need to decrement _contexts_entered
            try:
                self._clean_up(exc_type)
            finally:
                self._contexts_entered -= 1
        else:
            self._contexts_entered -= 1

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
            "Error running SQL: %s. MSG: %s\n" % (
                errorcodes.lookup(error.pgcode), error.message))

    @_checker
    def add(self, sql, sql_args=None, many=False):
        """Add an sql query to the transaction

        Parameters
        ----------
        sql : str
            The sql query
        sql_args : list, tuple or dict of objects, optional
            The arguments to the sql query
        many : bool, optional
            Whether or not we should add the query multiple times to the
            transaction

        Raises
        ------
        TypeError
            If `sql_args` is provided and is not a list, tuple or dict
        RuntimeError
            If invoked outside a context

        Notes
        -----
        If `many` is true, `sql_args` should be a list of lists, tuples or
        dicts, in which each element of the list contains the parameters for
        one SQL query of the many. Each element on the list is all the
        parameters for a single one of the many queries added. The amount of
        SQL queries added to the list is len(sql_args).
        """
        if not many:
            sql_args = [sql_args]

        for args in sql_args:
            if args:
                if not isinstance(args, (list, tuple, dict)):
                    raise TypeError("sql_args should be a list, tuple or dict."
                                    " Found %s" % type(args))
            self._queries.append((sql, args))

    def _execute(self):
        """Internal function that actually executes the transaction
        The `execute` function exposed in the API wraps this one to make sure
        that we catch any exception that happens in here and we rollback the
        transaction
        """
        with self._get_cursor() as cur:
            for sql, sql_args in self._queries:
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
        self._queries = []

        return self._results

    @_checker
    def execute(self):
        """Executes the transaction

        Returns
        -------
        list of DictCursor
            The results of all the SQL queries in the transaction

        Raises
        ------
        RuntimeError
            If invoked outside a context

        Notes
        -----
        If any exception occurs during the execution transaction, a rollback
        is executed and no changes are reflected in the database.
        When calling execute, the transaction will never be committed, it will
        be automatically committed when leaving the context

        See Also
        --------
        execute_fetchlast
        execute_fetchindex
        execute_fetchflatten
        """
        try:
            return self._execute()
        except Exception:
            self.rollback()
            raise

    @_checker
    def execute_fetchlast(self):
        """Executes the transaction and returns the last result

        This is a convenient function that is equivalent to
        `self.execute()[-1][0][0]`

        Returns
        -------
        object
            The first value of the last SQL query executed

        See Also
        --------
        execute
        execute_fetchindex
        execute_fetchflatten
        """
        return self.execute()[-1][0][0]

    @_checker
    def execute_fetchindex(self, idx=-1):
        """Executes the transaction and returns the results of the `idx` query

        This is a convenient function that is equivalent to
        `self.execute()[idx]

        Parameters
        ----------
        idx : int, optional
            The index of the query to return the result. It defaults to -1, the
            last query.

        Returns
        -------
        DictCursor
            The results of the `idx` query in the transaction

        See Also
        --------
        execute
        execute_fetchlast
        execute_fetchflatten
        """
        return self.execute()[idx]

    @_checker
    def execute_fetchflatten(self, idx=-1):
        """Executes the transaction and returns the flattened results of the
        `idx` query

        This is a convenient function that is equivalent to
        `chain.from_iterable(self.execute()[idx])`

        Parameters
        ----------
        idx : int, optional
            The index of the query to return the result. It defaults to -1, the
            last query.

        Returns
        -------
        list of objects
            The flattened results of the `idx` query

        See Also
        --------
        execute
        execute_fetchlast
        execute_fetchindex
        """
        return list(chain.from_iterable(self.execute()[idx]))

    def _funcs_executor(self, funcs, func_str):
        error_msg = []
        for f, args, kwargs in funcs:
            try:
                f(*args, **kwargs)
            except Exception as e:
                error_msg.append(str(e))
        # The functions in these two lines are mutually exclusive. When one of
        # them is executed, we can restore both of them.
        self._post_commit_funcs = []
        self._post_rollback_funcs = []
        if error_msg:
            raise RuntimeError(
                "An error occurred during the post %s commands:\n%s"
                % (func_str, "\n".join(error_msg)))

    @_checker
    def commit(self):
        """Commits the transaction and reset the queries

        Raises
        ------
        RuntimeError
            If invoked outside a context
        """
        # Reset the queries, the results and the index
        self._queries = []
        self._results = []
        try:
            self._connection.commit()
        except Exception:
            self._connection.close()
            raise
        # Execute the post commit functions
        self._funcs_executor(self._post_commit_funcs, "commit")

    @_checker
    def rollback(self):
        """Rollbacks the transaction and reset the queries

        Raises
        ------
        RuntimeError
            If invoked outside a context
        """
        # Reset the queries, the results and the index
        self._queries = []
        self._results = []
        try:
            self._connection.rollback()
        except Exception:
            self._connection.close()
            raise
        # Execute the post rollback functions
        self._funcs_executor(self._post_rollback_funcs, "rollback")

    @property
    def index(self):
        return len(self._queries) + len(self._results)

    @_checker
    def add_post_commit_func(self, func, *args, **kwargs):
        """Adds a post commit function

        The function added will be executed after the next commit in the
        transaction, unless a rollback is executed. This is useful, for
        example, to perform some filesystem clean up once the transaction is
        committed.

        Parameters
        ----------
        func : function
            The function to add for the post commit functions
        args : tuple
            The arguments of the function
        kwargs : dict
            The keyword arguments of the function
        """
        self._post_commit_funcs.append((func, args, kwargs))

    @_checker
    def add_post_rollback_func(self, func, *args, **kwargs):
        """Adds a post rollback function

        The function added will be executed after the next rollback in the
        transaction, unless a commit is executed. This is useful, for example,
        to restore the filesystem in case a rollback occurs, avoiding leaving
        the database and the filesystem in an out of sync state.

        Parameters
        ----------
        func : function
            The function to add for the post rollback functions
        args : tuple
            The arguments of the function
        kwargs : dict
            The keyword arguments of the function
        """
        self._post_rollback_funcs.append((func, args, kwargs))


# Singleton pattern, create the transaction for the entire system
TRN = Transaction()
