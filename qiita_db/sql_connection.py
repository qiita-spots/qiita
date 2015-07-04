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
Transaction blocks are created by first creating a queue of SQL commands, then
adding commands to it. Finally, the execute command is called to execute the
entire queue of SQL commands. A single command is made up of SQL and sql_args.
SQL is the sql string in psycopg2 format with \%s markup, and sql_args is the
list or tuple of replacement items.
An example of a basic queue with two SQL commands in a single transaction:

from qiita_db.sql_connection import SQLConnectionHandler
conn_handler = SQLConnectionHandler # doctest: +SKIP
conn_handler.create_queue("example_queue") # doctest: +SKIP
conn_handler.add_to_queue(
    "example_queue", "INSERT INTO qiita.qiita_user (email, name, password,"
    "phone) VALUES (%s, %s, %s, %s)",
    ['insert@foo.bar', 'Toy', 'pass', '111-111-11112']) # doctest: +SKIP
conn_handler.add_to_queue(
    "example_queue", "UPDATE qiita.qiita_user SET user_level_id = 1, "
    "phone = '222-222-2221' WHERE email = %s",
    ['insert@foo.bar']) # doctest: +SKIP
conn_handler.execute_queue("example_queue") # doctest: +SKIP
conn_handler.execute_fetchall(
    "SELECT * from qiita.qiita_user WHERE email = %s",
    ['insert@foo.bar']) # doctest: +SKIP
[['insert@foo.bar', 1, 'pass', 'Toy', None, None, '222-222-2221', None, None,
  None]] # doctest: +SKIP

You can also use results from a previous command in the queue in a later
command. If an item in the queue depends on a previous sql command's output,
use {#} notation as a placeholder for the value. The \# must be the
position of the result, e.g. if you return two things you can use \{0\}
to reference the first and \{1\} to referece the second. The results list
will continue to grow until one of the references is reached, then it
will be cleaned out.
Modifying the previous example to show this ability (Note the RETURNING added
to the first SQL command):

from qiita_db.sql_connection import SQLConnectionHandler
conn_handler = SQLConnectionHandler # doctest: +SKIP
conn_handler.create_queue("example_queue") # doctest: +SKIP
conn_handler.add_to_queue(
    "example_queue", "INSERT INTO qiita.qiita_user (email, name, password,"
    "phone) VALUES (%s, %s, %s, %s) RETURNING email, password",
    ['insert@foo.bar', 'Toy', 'pass', '111-111-11112']) # doctest: +SKIP
conn_handler.add_to_queue(
    "example_queue", "UPDATE qiita.qiita_user SET user_level_id = 1, "
    "phone = '222-222-2221' WHERE email = %s AND password = %s",
    ['{0}', '{1}']) # doctest: +SKIP
conn_handler.execute_queue("example_queue") # doctest: +SKIP
conn_handler.execute_fetchall(
    "SELECT * from qiita.qiita_user WHERE email = %s", ['insert@foo.bar'])
[['insert@foo.bar', 1, 'pass', 'Toy', None, None, '222-222-2221', None, None,
  None]] # doctest: +SKIP
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
from tempfile import mktemp
from datetime import date, time, datetime
import re

from psycopg2 import (connect, ProgrammingError, Error as PostgresError,
                      OperationalError)
from psycopg2.extras import DictCursor
from psycopg2.extensions import (
    ISOLATION_LEVEL_AUTOCOMMIT, ISOLATION_LEVEL_READ_COMMITTED,
    TRANSACTION_STATUS_IDLE)

from qiita_core.qiita_settings import qiita_config


def flatten(listOfLists):
    # https://docs.python.org/2/library/itertools.html
    # TODO: Issue #551  Use skbio.util.flatten instead of this
    return chain.from_iterable(listOfLists)


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

    _regex = re.compile("{(\d+)}")

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

    def _check_queue_exists(self, queue_name):
        """Checks if queue `queue_name` exists in the handler

        Parameters
        ----------
        queue_name : str
            The name of the queue

        Returns
        -------
        bool
            True if queue `queue_name` exist in the handler. False otherwise.
        """
        return queue_name in self.queues

    def create_queue(self, queue_name):
        """Add a new queue to the connection

        Parameters
        ----------
        queue_name : str
            Name of the new queue

        Raises
        ------
        KeyError
            Queue name already exists
        """
        if self._check_queue_exists(queue_name):
            raise KeyError("Queue %s already exists" % queue_name)

        self.queues[queue_name] = []

    def list_queues(self):
        """Returns list of all queue names currently in handler

        Returns
        -------
        list of str
            names of queues in handler
        """
        return self.queues.keys()

    def add_to_queue(self, queue, sql, sql_args=None, many=False):
        """Add an sql command to the end of a queue

        Parameters
        ----------
        queue : str
            name of queue adding to
        sql : str
            sql command to run
        sql_args : list, tuple or dict, optional
            the arguments to fill sql command with
        many : bool, optional
            Whether or not this should be treated as an executemany command.
            Default False

        Raises
        ------
        KeyError
            queue does not exist
        """
        if not self._check_queue_exists(queue):
            raise KeyError("Queue '%s' does not exist" % queue)

        if not many:
            sql_args = [sql_args]

        for args in sql_args:
            self._check_sql_args(args)
            self.queues[queue].append((sql, args))

    def _rollback_raise_error(self, queue, sql, sql_args, e):
        self._connection.rollback()
        # wipe out queue since it has an error in it
        del self.queues[queue]
        raise ValueError(
            "Error running SQL query in queue %s: %s\nARGS: %s\nError: %s"
            % (queue, sql, str(sql_args), e))

    def execute_queue(self, queue):
        """Executes all sql in a queue in a single transaction block

        Parameters
        ----------
        queue : str
            Name of queue to execute

        Notes
        -----
        Does not support executemany command. Instead, enter the multiple
        SQL commands as multiple entries in the queue.

        Raises
        ------
        KetError
            If queue does not exist
        IndexError
            If a sql argument placeholder does not correspond to the result of
            any previously-executed query.
        """
        if not self._check_queue_exists(queue):
            raise KeyError("Queue '%s' does not exist" % queue)

        with self.get_postgres_cursor() as cur:
            results = []
            clear_res = False
            for sql, sql_args in self.queues[queue]:
                if sql_args is not None:
                    # The user can provide a tuple, make sure that it is a
                    # list, so we can assign the item
                    sql_args = list(sql_args)
                    for pos, arg in enumerate(sql_args):
                        # check if previous results needed and replace
                        if isinstance(arg, str):
                            result = self._regex.search(arg)
                            if result:
                                result_pos = int(result.group(1))
                                try:
                                    sql_args[pos] = results[result_pos]
                                except IndexError:
                                    self._rollback_raise_error(
                                        queue, sql, sql_args,
                                        "The index provided as a placeholder "
                                        "%d does not correspond to any "
                                        "previous result" % result_pos)
                                clear_res = True
                # wipe out results if needed and reset clear_res
                if clear_res:
                    results = []
                    clear_res = False
                # Fire off the SQL command
                try:
                    cur.execute(sql, sql_args)
                except Exception as e:
                    self._rollback_raise_error(queue, sql, sql_args, e)

                # fetch results if available and append to results list
                try:
                    res = cur.fetchall()
                except ProgrammingError as e:
                    # At this execution point, we don't know if the sql query
                    # that we executed was a INSERT or a SELECT. If it was a
                    # SELECT and there is nothing to fetch, it will return an
                    # empty list. However, if it was a INSERT it will raise a
                    # ProgrammingError, so we catch that one and pass.
                    pass
                except PostgresError as e:
                    self._rollback_raise_error(queue, sql, sql_args, e)
                else:
                    # append all results linearly
                    results.extend(flatten(res))
        self._connection.commit()
        # wipe out queue since finished
        del self.queues[queue]
        return results

    def get_temp_queue(self):
        """Get a queue name that did not exist when this function was called

        Returns
        -------
        str
            The name of the queue
        """
        temp_queue_name = mktemp()
        while temp_queue_name in self.queues:
            temp_queue_name = mktemp()

        self.create_queue(temp_queue_name)

        return temp_queue_name


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

    _regex = re.compile("^{(\d+):(\d+):(\d+)}$")

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
            "Error running SQL query:\n"
            "Query: %s\nArguments: %s\nError: %s\n"
            % (sql, str(sql_args), str(error)))

    def _replace_placeholders(self, sql, sql_args):
        """Replaces the placeholder in `sql_args` with the actual value

        Parameters
        ----------
        sql : str
            The SQL query
        sql_args : list
            The arguments of the SQL query

        Returns
        -------
        tuple of (str, list of objects)
            The input SQL query (unmodified) and the SQL arguments with the
            placeholder (if any) substituted with the actual value of the
            previous query

        Raises
        ------
        ValueError
            If a placeholder does not match any previous result
            If a placeholder points to a query that do not produce any result
        """
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
                            "a SQL query that does not retrieve data"
                            % (q_idx, r_idx, v_idx))
        return sql, sql_args

    @_checker
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
        RuntimeError
            If invoked outside a context

        Notes
        -----
        If `many` is true, `sql_args` should be a list of lists, in which each
        list of the list contains the parameters for one SQL query of the many.
        Each element on the list is all the parameters for a single one of the
        many queries added. The amount of SQL queries added to the list is
        len(sql_args).
        """
        if not many:
            sql_args = [sql_args]

        for args in sql_args:
            if args:
                if not isinstance(args, list):
                    raise TypeError("sql_args should be a list. Found %s"
                                    % type(args))
            else:
                args = []
            self._queries.append((sql, args))

    def _execute(self):
        """Internal function that actually executes the transaction
        The `execute` function exposed in the API wraps this one to make sure
        that we catch any exception that happens in here and we rollback the
        transaction
        """
        with self._get_cursor() as cur:
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

        This is a convenient function that is equivalen to
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
        for f in funcs:
            try:
                f()
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
    def add_post_commit_func(self, func):
        """Adds a post commit function

        The function added will be executed after the next commit in the
        transaction, unless a rollback is executed. This is useful, for
        example, to perform some filesystem clean up once the transaction is
        committed.

        Parameters
        ----------
        func : function
            The function to add for the post commit functions

        Notes
        -----
        func should not accept any parameter, i.e. it should allow to be
        invoked as `func()`
        """
        self._post_commit_funcs.append(func)

    @_checker
    def add_post_rollback_func(self, func):
        """Adds a post rollback function

        The function added will be executed after the next rollback in the
        transaction, unless a commit is executed. This is useful, for example,
        to restore the filesystem in case a rollback occurs, avoiding leaving
        the database and the filesystem in an out of sync state.

        Parameters
        ----------
        func : function
            The function to add for the post rollback functions

        Notes
        -----
        func should not accept any parameter, i.e. it should allow to be
        invoked as `func()`
        """
        self._post_rollback_funcs.append(func)

# Singleton pattern, create the transaction for the entire system
TRN = Transaction()
