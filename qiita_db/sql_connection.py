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

   Transaction
"""

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from contextlib import contextmanager
from functools import wraps
from itertools import chain

from psycopg2 import Error as PostgresError
from psycopg2 import OperationalError, ProgrammingError, connect, errorcodes
from psycopg2.extensions import TRANSACTION_STATUS_IDLE
from psycopg2.extras import DictCursor

from qiita_core.qiita_settings import qiita_config


def _checker(func):
    """Decorator to check that methods are executed inside the context"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._contexts_entered == 0:
            raise RuntimeError(
                "Operation not permitted. Transaction methods can only be "
                "invoked within the context manager."
            )
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

    def __init__(self, admin=False):
        self._queries = []
        self._results = []
        self._contexts_entered = 0
        self._connection = None
        self._post_commit_funcs = []
        self._post_rollback_funcs = []
        self.admin = admin

    def _open_connection(self):
        # If the connection already exists and is not closed, don't do anything
        if self._connection is not None and self._connection.closed == 0:
            return

        try:
            if self.admin:
                self._connection = connect(
                    user=qiita_config.admin_user,
                    password=qiita_config.admin_password,
                    host=qiita_config.host,
                    port=qiita_config.port,
                )
                self._connection.autocommit = True
            else:
                self._connection = connect(
                    user=qiita_config.user,
                    password=qiita_config.password,
                    database=qiita_config.database,
                    host=qiita_config.host,
                    port=qiita_config.port,
                )
        except OperationalError as e:
            # catch three known common exceptions and raise runtime errors
            try:
                etype = str(e).split(":")[1].split()[0]
            except IndexError:
                # we recieved a really unanticipated error without a colon
                etype = ""
            if etype == "database":
                etext = (
                    "This is likely because the database `%s` has not "
                    "been created or has been dropped." % qiita_config.database
                )
            elif etype == "role":
                etext = (
                    "This is likely because the user string `%s` "
                    "supplied in your configuration file `%s` is "
                    "incorrect or not an authorized postgres user."
                    % (qiita_config.user, qiita_config.conf_fp)
                )
            elif etype == "Connection":
                etext = (
                    "This is likely because postgres isn't "
                    "running. Check that postgres is correctly "
                    "installed and is running."
                )
            else:
                # we recieved a really unanticipated error with a colon
                etext = ""
            ebase = (
                "An OperationalError with the following message occured"
                "\n\n\t%s\n%s For more information, review `INSTALL.md`"
                " in the Qiita installation base directory."
            )
            raise RuntimeError(ebase % (str(e), etext))

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
        elif self._connection.get_transaction_status() != TRANSACTION_STATUS_IDLE:
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

        try:
            ec_lu = errorcodes.lookup(error.pgcode)
            raise ValueError("Error running SQL: %s. MSG: %s\n" % (ec_lu, str(error)))
        # the order of except statements is important, do not change
        except (KeyError, AttributeError, TypeError) as error:
            raise ValueError("Error running SQL query: %s" % str(error))
        except ValueError as error:
            raise ValueError("Error running SQL query: %s" % str(error))

    @_checker
    def add(self, sql, sql_args=None, many=False):
        """Add a sql query to the transaction

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
                    raise TypeError(
                        "sql_args should be a list, tuple or dict."
                        " Found %s" % type(args)
                    )
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
                except ProgrammingError:
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
                % (func_str, "\n".join(error_msg))
            )

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

        if self._connection is not None and self._connection.closed == 0:
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
TRNADMIN = Transaction(admin=True)


def perform_as_transaction(sql, parameters=None):
    """Opens, adds and executes sql as a single transaction

    Parameters
    ----------
    sql : str
        The SQL to execute
    parameters: object, optional
        The object of parameters to pass to the TRN.add command
    """
    with TRN:
        if parameters:
            TRN.add(sql, parameters)
        else:
            TRN.add(sql)
        TRN.execute()


def create_new_transaction():
    """Creates a new global transaction

    This is needed when using multiprocessing
    """
    global TRN
    TRN = Transaction()
