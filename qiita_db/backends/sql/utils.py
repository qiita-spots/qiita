__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita project"
__credits__ = ["Jose Antonio Navas Molina", "Adam Robbins-Pianka",
               "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.com"

from qiita_db.backends.sql.connections import postgres
from qiita_db.backends.sql.exceptions import QiitaDBSQLExecutionError
from psycopg2 import Error as PostgresError


def get_postgres_cursor():
    """ Returns a Postgres cursor

    Inputs: None

    Returns:
        pgcursor: the postgres.cursor()

    Raises a RuntimeError if the cursor cannot be created
    """
    try:
        pgcursor = postgres.cursor()
    except PostgresError, e:
        raise RuntimeError("Cannot get postgres cursor! %s" % e)
    return pgcursor


def _check_sql_args(sql_args):
    """ Checks that sql_args have the correct type

    Inputs:
        sql_args: SQL arguments

    Raises a TypeError if sql_args does not have the correct type, otherwise
        it just returns the execution to the caller
    """
    # Check that sql arguments have the correct type
    if sql_args and type(sql_args) is not tuple:
        raise TypeError("sql_args should be tuple. Found %s " % type(sql_args))


def sql_execute_fetchall(pgcursor, sql, sql_args):
    """ Executes a fetchall SQL query

    Inputs:
        pgcursor: the postgres cursor
        sql: string with the SQL query
        sql_args: tuple with the arguments for the SQL query

    Returns:
        The results of the fetchall query as a list of tuples

    Raises a QiitaDBSQLExecutionError if there is some error executing the
        SQL query

    Note: from psycopg2 documentation, only variable values should be bound via
        sql_args, it shouldn't be used to set table or field names. For those
        elements, ordinary string formatting should be used before running
        execute.
    """
    # Check that sql arguments have the correct type
    _check_sql_args(sql_args)
    # Execute the query
    try:
        pgcursor.execute(sql, sql_args)
        result = pgcursor.fetchall()
        postgres.commit()
    except PostgresError, e:
        postgres.rollback()
        raise QiitaDBSQLExecutionError("Error running SQL query: %s", e)
    return result


def sql_execute_fetchone(pgcursor, sql, sql_args):
    """ Executes a fetchone SQL query

    Inputs:
        pgcursor: the postgres cursor
        sql: string with the SQL query
        sql_args: tuple with the arguments for the SQL query

    Returns:
        The results of the fetchone query as a tuple

    Raises a QiitaDBSQLExecutionError if there is some error executing the
        SQL query

    Note: from psycopg2 documentation, only variable values should be bound via
        sql_args, it shouldn't be used to set table or field names. For those
        elements, ordinary string formatting should be used before running
        execute.
    """
    # Check that sql arguments have the correct type
    _check_sql_args(sql_args)
    # Execute the query
    try:
        pgcursor.execute(sql, sql_args)
        result = pgcursor.fetchone()
        postgres.commit()
    except PostgresError, e:
        postgres.rollback()
        raise QiitaDBSQLExecutionError("Error running SQL query: %s", e)
    return result


def sql_execute(pgcursor, sql, sql_args):
    """ Executes an SQL query with no results

    Inputs:
        pgcursor: the postgres cursor
        sql: string with the SQL query
        sql_args: tuple with the arguments for the SQL query

    Raises a QiitaDBSQLExecutionError if there is some error executing the
        SQL query

    Note: from psycopg2 documentation, only variable values should be bound via
        sql_args, it shouldn't be used to set table or field names. For those
        elements, ordinary string formatting should be used before running
        execute.
    """
    # Check that sql arguments have the correct type
    _check_sql_args(sql_args)
    # Execute the query
    try:
        pgcursor.execute(sql, sql_args)
        postgres.commit()
    except PostgresError, e:
        postgres.rollback()
        raise QiitaDBSQLExecutionError("Error running SQL query: %s", e)


def sql_executemany(pgcursor, sql, sql_args_list):
    """ Executes an executemany SQL query with no results

    Inputs:
        pgcursor: the postgres cursor
        sql: string with the SQL query
        sql_args_list: list with tuples with the arguments for the SQL query

    Raises a QiitaDBSQLExecutionError if there is some error executing the
        SQL query

    Note: from psycopg2 documentation, only variable values should be bound via
        sql_args, it shouldn't be used to set table or field names. For those
        elements, ordinary string formatting should be used before running
        execute.
    """
    # Check that sql arguments have the correct type
    for sql_args in sql_args_list:
        _check_sql_args(sql_args)
    # Execute the query
    try:
        pgcursor.executemany(sql, sql_args_list)
        postgres.commit()
    except PostgresError, e:
        postgres.rollback()
        raise QiitaDBSQLExecutionError("Error running SQL query: %s", e)
