r"""
SQL Connection object (:mod:`qiita_db.sql_connection`)
==================================

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

from psycopg2 import connect, ProgrammingError, Error as PostgresError
from psycopg2.extras import DictCursor
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from .exceptions import QiitaDBExecutionError, QiitaDBConnectionError
from qiita_core.qiita_settings import qiita_config


class SQLConnectionHandler(object):
    """Encapsulates the DB connection with the Postgres DB"""
    def __init__(self, admin=False):
        self.admin = admin
        self._open_connection()
        # queues for transaction blocks. Format is {str: list} where the str
        # is the queue name and the list is the queue of SQL commands
        self.queues = {}

    def __del__(self):
        # make sure if connection close fails it doesn't raise error
        # should only error if connection already closed
        try:
            self._connection.close()
        except:
            pass

    def _open_connection(self):
        # connection string arguments for a normal user
        args = {
            'user': qiita_config.user,
            'password': qiita_config.password,
            'database': qiita_config.database,
            'host': qiita_config.host,
            'port': qiita_config.port}

        # if this is an admin user, do not connect to a particular database,
        # and use the admin credentials
        if self.admin:
            args['user'] = qiita_config.admin_user
            args['password'] = qiita_config.admin_password
            del args['database']

        try:
            self._connection = connect(**args)
        except Exception as e:
            # catch any exception and raise as runtime error
            raise RuntimeError("Cannot connect to database: %s" % str(e))

        if self.admin:
            # Set the isolation level to AUTOCOMMIT so we can execute a create
            # or drop database sql query
            self._connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    @contextmanager
    def get_postgres_cursor(self):
        """ Returns a Postgres cursor

        Returns
        -------
        pgcursor : psycopg2.cursor

        Raises a QiitaDBConnectionError if the cursor cannot be created
        """
        if self._connection.closed:
            # Currently defaults to non-admin connection
            self._open_connection()

        try:
            with self._connection.cursor(cursor_factory=DictCursor) as cur:
                yield cur
        except PostgresError as e:
            raise QiitaDBConnectionError("Cannot get postgres cursor! %s" % e)

    def _check_sql_args(self, sql_args):
        """ Checks that sql_args have the correct type

        Inputs:
            sql_args: SQL arguments

        Raises a TypeError if sql_args does not have the correct type,
            otherwise it just returns the execution to the caller
        """
        # Check that sql arguments have the correct type
        if sql_args and type(sql_args) not in [tuple, list, dict]:
            raise TypeError("sql_args should be tuple, list or dict. Found %s "
                            % type(sql_args))

    @contextmanager
    def _sql_executor(self, sql, sql_args=None, many=False, commit=True):
        """Executes an SQL query

        Parameters
        ----------
        sql: str
            The SQL query
        sql_args: tuple or list, optional
            The arguments for the SQL query
        many: bool, optional
            If true, performs an execute many call
        commit : bool, optional
            Whether to commit or not after executing. Default True

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
                if commit:
                    self._connection.commit()
            except PostgresError as e:
                self._connection.rollback()
                raise QiitaDBExecutionError(("\nError running SQL query: %s"
                                             "\nARGS: %s"
                                             "\nError: %s" %
                                             (sql, str(sql_args), e)))

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
        def chain(item):
            # itertools chain not playing nicely, use my own
            for i in item:
                for x in i:
                    yield x

        with self.get_postgres_cursor() as cur:
            results = []
            clear_res = False
            for sql, sql_args in self.queues[queue]:
                # wipe out results list if needed
                for pos, arg in enumerate(sql_args):
                    # check if previous results needed and replace if necessary
                    if isinstance(arg, str) and \
                            arg[0] == "{" and arg[-1] == "}":
                        result_pos = int(arg[1:-1])
                        sql_args[pos] = results[result_pos]
                        clear_res = True
                # wipe out results if needed and reset clear_res
                if clear_res:
                    results = []
                clear_res = False
                try:
                    self._check_sql_args(sql_args)
                    cur.execute(sql, sql_args)
                    try:
                        res = cur.fetchall()
                        # append all results linearly
                        results.extend(chain(res))
                    except ProgrammingError:
                        # ignore error if nothing to fetch
                        pass
                except Exception as e:
                    self._connection.rollback()
                    # wipe out queue since it has an error in it
                    del self.queues[queue]
                    raise QiitaDBExecutionError(
                        ("\nError running SQL query in queue %s: %s"
                         "\nARGS: %s\nError: %s" % (queue, sql,
                                                    str(sql_args), e)))
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

    def add_to_queue(self, queue, sql, sql_args=None):
        """Add an sql command to the end of a queue

        Parameters
        ----------
        queue : str
            name of queue adding to
        sql : str
            sql command to run
        sql_args : list or tuple, optional
            the arguments to fill sql command with

        Raises
        ------
        KeyError
            queue does not exist

        Notes
        -----
        Currently does not support executemany command

        Queues are executed in FIFO order
        """
        if sql_args is None:
            sql_args = []
        else:
            self._check_sql_args(sql_args)
        self.queues[queue].append((sql, sql_args))

    def execute_fetchall(self, sql, sql_args=None):
        """ Executes a fetchall SQL query

        Parameters
        ----------
        sql: str
            The SQL query
        sql_args: tuple or list, optional
            The arguments for the SQL query

        Returns
        ------
        list of tuples
            The results of the fetchall query

        Raises
        ------
        QiitaDBExecutionError
            If there is some error executing the SQL query

        Note: from psycopg2 documentation, only variable values should be bound
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
        sql: str
            The SQL query
        sql_args: tuple or list, optional
            The arguments for the SQL query

        Returns
        -------
        Tuple
            The results of the fetchone query

        Raises
        ------
        QiitaDBExecutionError
            if there is some error executing the SQL query

        Note: from psycopg2 documentation, only variable values should be bound
            via sql_args, it shouldn't be used to set table or field names. For
            those elements, ordinary string formatting should be used before
            running execute.
        """
        with self._sql_executor(sql, sql_args) as pgcursor:
            result = pgcursor.fetchone()
        return result

    def execute(self, sql, sql_args=None):
        """ Executes an SQL query with no results

        Parameters
        ----------
        sql: str
            The SQL query
        sql_args: tuple or list, optional
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
        sql: str
            The SQL query
        sql_args: list of tuples
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
