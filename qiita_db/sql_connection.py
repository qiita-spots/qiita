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
from tempfile import mktemp
from datetime import date, time, datetime

from psycopg2 import (connect, ProgrammingError, Error as PostgresError,
                      OperationalError)
from psycopg2.extras import DictCursor
from psycopg2.extensions import (
    ISOLATION_LEVEL_AUTOCOMMIT, ISOLATION_LEVEL_READ_COMMITTED)

from .exceptions import QiitaDBExecutionError, QiitaDBConnectionError
from qiita_core.qiita_settings import qiita_config


def flatten(listOfLists):
    # https://docs.python.org/2/library/itertools.html
    # TODO: Issue #551  Use skbio.util.flatten instead of this
    return chain.from_iterable(listOfLists)


class SQLConnectionHandler(object):
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

    """Encapsulates the DB connection with the Postgres DB

    Parameters
    ----------
    admin : {'no_admin', 'no_database', 'database'}, optional
        Whether or not to connect as the admin user. Options other than
        `no_admin` depend on admin credentials in the qiita configuration. If
        'admin_without_database', the connection will be made to the server
        specified in the qiita configuration, but not to a specific database.
        If 'admin_with_database', then a connection will be made to the server
        and database specified in the qiita config.
    """
    def __init__(self, admin='no_admin'):
        if admin not in ('no_admin', 'admin_with_database',
                         'admin_without_database'):
            raise RuntimeError("admin takes only {'no_admin', "
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

        Raises a QiitaDBConnectionError if the cursor cannot be created
        """
        self._open_connection()

        try:
            with self._connection.cursor(cursor_factory=DictCursor) as cur:
                yield cur
        except PostgresError as e:
            raise QiitaDBConnectionError("Cannot get postgres cursor! %s" % e)

    def set_autocommit(self, on_or_off):
        """Sets the isolation level to autocommit or default (read committed)

        Parameters
        ----------
        on_or_off : {'on', 'off'}
            If 'on', isolation level will be set to autocommit. Otherwise,
            it will be set to read committed.
        """
        if on_or_off not in {'on', 'off'}:
            raise ValueError("set_autocommit takes only 'on' or 'off'")

        if on_or_off == 'on':
            level = ISOLATION_LEVEL_AUTOCOMMIT
        else:
            level = ISOLATION_LEVEL_READ_COMMITTED

        self._connection.set_isolation_level(level)

    def _check_sql_args(self, sql_args):
        """ Checks that sql_args have the correct type

        Inputs:
            sql_args : SQL arguments

        Raises a TypeError if sql_args does not have the correct type,
            otherwise it just returns the execution to the caller
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
        sql_args : tuple or list, optional
            The arguments for the SQL query
        many : bool, optional
            If true, performs an execute many call

        Returns
        -------
        pgcursor : psycopg2.cursor
            The cursor in which the SQL query was executed

        Raises
        ------
        QiitaDBExecutionError
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
            try:
                if many:
                    cur.executemany(sql, sql_args)
                else:
                    cur.execute(sql, sql_args)
                yield cur
                self._connection.commit()
            except PostgresError as e:
                self._connection.rollback()
                raise QiitaDBExecutionError(("\nError running SQL query: %s"
                                             "\nARGS: %s"
                                             "\nError: %s" %
                                             (sql, str(sql_args), e)))

    def _rollback_raise_error(self, queue, sql, sql_args, e):
        self._connection.rollback()
        # wipe out queue since it has an error in it
        del self.queues[queue]
        raise QiitaDBExecutionError(
            ("\nError running SQL query in queue %s: %s"
             "\nARGS: %s\nError: %s" % (queue, sql,
                                        str(sql_args), e)))

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

        Queues are executed in FIFO order
        """
        with self.get_postgres_cursor() as cur:
            results = []
            clear_res = False
            for sql, sql_args in self.queues[queue]:
                if sql_args is not None:
                    for pos, arg in enumerate(sql_args):
                        # check if previous results needed and replace
                        if isinstance(arg, str) and \
                                arg[0] == "{" and arg[-1] == "}":
                            result_pos = int(arg[1:-1])
                            sql_args[pos] = results[result_pos]
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
                    # ignore error if nothing to fetch
                    pass
                except Exception as e:
                    self._rollback_raise_error(queue, sql, sql_args, e)
                else:
                    # append all results linearly
                    results.extend(flatten(res))
        self._connection.commit()
        # wipe out queue since finished
        del self.queues[queue]
        return results

    def list_queues(self):
        """Returns list of all queue names currently in handler

        Returns
        -------
        list
            names of queues in handler
        """
        return self.queues.keys()

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
        if queue_name in self.queues:
            raise KeyError("Queue already contains %s" % queue_name)

        self.queues[queue_name] = []

    def add_to_queue(self, queue, sql, sql_args=None, many=False):
        """Add an sql command to the end of a queue

        Parameters
        ----------
        queue : str
            name of queue adding to
        sql : str
            sql command to run
        sql_args : list or tuple, optional
            the arguments to fill sql command with
        many : bool, optional
            Whether or not this should be treated as an executemany command.
            Default False

        Raises
        ------
        KeyError
            queue does not exist

        Notes
        -----
        Queues are executed in FIFO order
        """
        if many:
            for args in sql_args:
                self._check_sql_args(args)
                self.queues[queue].append((sql, args))
        else:
            self._check_sql_args(sql_args)
            self.queues[queue].append((sql, sql_args))

    def execute_fetchall(self, sql, sql_args=None):
        """ Executes a fetchall SQL query

        Parameters
        ----------
        sql : str
            The SQL query
        sql_args : tuple or list, optional
            The arguments for the SQL query

        Returns
        ------
        list of tuples
            The results of the fetchall query

        Raises
        ------
        QiitaDBExecutionError
            If there is some error executing the SQL query

        Notes
        -----
        from psycopg2 documentation, only variable values should be bound
        via sql_args, it shouldn't be used to set table or field names. For
        those elements, ordinary string formatting should be used before
        running execute.
        """
        with self._sql_executor(sql, sql_args) as pgcursor:
            result = pgcursor.fetchall()

        return result

    def execute_fetchone(self, sql, sql_args=None):
        """ Executes a fetchone SQL query

        Parameters
        ----------
        sql : str
            The SQL query
        sql_args : tuple or list, optional
            The arguments for the SQL query

        Returns
        -------
        Tuple
            The results of the fetchone query

        Raises
        ------
        QiitaDBExecutionError
            if there is some error executing the SQL query

        Notes
        -----
        from psycopg2 documentation, only variable values should be bound
        via sql_args, it shouldn't be used to set table or field names. For
        those elements, ordinary string formatting should be used before
        running execute.
        """
        with self._sql_executor(sql, sql_args) as pgcursor:
            result = pgcursor.fetchone()

        return result

    def fetchall_with_types(self, sql, sql_args=None):
        """Executes a fetchall SQL query with column information

        Parameters
        ----------
        sql : str
            The SQL query
        sql_args : tuple or list, optional
            The arguments for the SQL query

        Returns
        ------
        list of tuples
            The results of the fetchall query
        dict
            dictionary in the form of {column: type}

        Raises
        ------
        QiitaDBExecutionError
            If there is some error executing the SQL query

        Notes
        -----
        from psycopg2 documentation, only variable values should be bound
        via sql_args, it shouldn't be used to set table or field names. For
        those elements, ordinary string formatting should be used before
        running execute.
        """
        with self._sql_executor(sql, sql_args) as pgcursor:
            result = pgcursor.fetchall()
            types = {desc[0]: self.TYPE_CODES[desc[1]]
                     for desc in pgcursor.description}

        return result, types

    def fetchone_with_types(self, sql, sql_args=None):
        """Executes a fetchone SQL query with column information

        Parameters
        ----------
        sql : str
            The SQL query
        sql_args : tuple or list, optional
            The arguments for the SQL query

        Returns
        -------
        Tuple
            The results of the fetchone query
        dict
            dictionary in the form of {column: type}

        Raises
        ------
        QiitaDBExecutionError
            if there is some error executing the SQL query

        Notes
        -----
        from psycopg2 documentation, only variable values should be bound
        via sql_args, it shouldn't be used to set table or field names. For
        those elements, ordinary string formatting should be used before
        running execute.
        """
        with self._sql_executor(sql, sql_args) as pgcursor:
            result = pgcursor.fetchone()
            types = {desc[0]: self.TYPE_CODES[desc[1]]
                     for desc in pgcursor.description}

        return result, types

    def execute(self, sql, sql_args=None):
        """ Executes an SQL query with no results

        Parameters
        ----------
        sql : str
            The SQL query
        sql_args : tuple or list, optional
            The arguments for the SQL query

        Raises
        ------
        QiitaDBExecutionError
            if there is some error executing the SQL query

        Note: from psycopg2 documentation, only variable values should be bound
            via sql_args, it shouldn't be used to set table or field names. For
            those elements, ordinary string formatting should be used before
            running execute.
        """
        with self._sql_executor(sql, sql_args):
            pass

    def executemany(self, sql, sql_args_list):
        """ Executes an executemany SQL query with no results

        Parameters
        ----------
        sql : str
            The SQL query
        sql_args : list of tuples
            The arguments for the SQL query

        Raises
        ------
        QiitaDBExecutionError
            If there is some error executing the SQL query

        Note: from psycopg2 documentation, only variable values should be bound
            via sql_args, it shouldn't be used to set table or field names. For
            those elements, ordinary string formatting should be used before
            running execute.
        """
        with self._sql_executor(sql, sql_args_list, True):
            pass

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
