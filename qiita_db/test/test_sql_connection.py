from unittest import TestCase, main

from psycopg2._psycopg import connection
from psycopg2.extras import DictCursor
from psycopg2 import connect
from psycopg2.extensions import (ISOLATION_LEVEL_AUTOCOMMIT,
                                 ISOLATION_LEVEL_READ_COMMITTED,
                                 TRANSACTION_STATUS_IDLE)

from qiita_db.sql_connection import SQLConnectionHandler, Transaction
from qiita_core.util import qiita_test_checker
from qiita_core.qiita_settings import qiita_config


DB_TEST_TABLE = """CREATE TABLE qiita.test_table (
    str_column      varchar DEFAULT 'foo' NOT NULL,
    bool_column     bool DEFAULT True NOT NULL,
    int_column      bigint NOT NULL);"""


@qiita_test_checker()
class TestBase(TestCase):
    def setUp(self):
        # Add the test table to the database, so we can use it in the tests
        with connect(user=qiita_config.user, password=qiita_config.password,
                     host=qiita_config.host, port=qiita_config.port,
                     database=qiita_config.database) as con:
            with con.cursor() as cur:
                cur.execute(DB_TEST_TABLE)

    def _populate_test_table(self):
        """Aux function that populates the test table"""
        sql = """INSERT INTO qiita.test_table
                    (str_column, bool_column, int_column)
                 VALUES (%s, %s, %s)"""
        sql_args = [('test1', True, 1), ('test2', True, 2),
                    ('test3', False, 3), ('test4', False, 4)]
        with connect(user=qiita_config.user, password=qiita_config.password,
                     host=qiita_config.host, port=qiita_config.port,
                     database=qiita_config.database) as con:
            with con.cursor() as cur:
                cur.executemany(sql, sql_args)
            con.commit()

    def _assert_sql_equal(self, exp):
        """Aux function for testing"""
        with connect(user=qiita_config.user, password=qiita_config.password,
                     host=qiita_config.host, port=qiita_config.port,
                     database=qiita_config.database) as con:
            with con.cursor() as cur:
                cur.execute("SELECT * FROM qiita.test_table")
                obs = cur.fetchall()
            con.commit()

        self.assertEqual(obs, exp)


class TestConnHandler(TestBase):
    def test_init(self):
        obs = SQLConnectionHandler()
        self.assertEqual(obs.admin, 'no_admin')
        self.assertEqual(obs.queues, {})
        self.assertTrue(isinstance(obs._connection, connection))
        self.assertEqual(self.conn_handler._user_conn.closed, 0)

        # Let's close the connection and make sure that it gets reopened
        obs.close()
        obs = SQLConnectionHandler()
        self.assertEqual(self.conn_handler._user_conn.closed, 0)

    def test_init_admin_error(self):
        with self.assertRaises(ValueError):
            SQLConnectionHandler(admin='not a valid value')

    def test_init_admin_with_database(self):
        obs = SQLConnectionHandler(admin='admin_with_database')
        self.assertEqual(obs.admin, 'admin_with_database')
        self.assertEqual(obs.queues, {})
        self.assertTrue(isinstance(obs._connection, connection))
        self.assertEqual(self.conn_handler._user_conn.closed, 0)

    def test_init_admin_without_database(self):
        obs = SQLConnectionHandler(admin='admin_without_database')
        self.assertEqual(obs.admin, 'admin_without_database')
        self.assertEqual(obs.queues, {})
        self.assertTrue(isinstance(obs._connection, connection))
        self.assertEqual(self.conn_handler._user_conn.closed, 0)

    def test_close(self):
        self.assertEqual(self.conn_handler._user_conn.closed, 0)
        self.conn_handler.close()
        self.assertNotEqual(self.conn_handler._user_conn.closed, 0)

    def test_get_postgres_cursor(self):
        with self.conn_handler.get_postgres_cursor() as cur:
            self.assertEqual(type(cur), DictCursor)

    def test_autocommit(self):
        self.assertFalse(self.conn_handler.autocommit)
        self.conn_handler._connection.set_isolation_level(
            ISOLATION_LEVEL_AUTOCOMMIT)
        self.assertTrue(self.conn_handler.autocommit)
        self.conn_handler._connection.set_isolation_level(
            ISOLATION_LEVEL_READ_COMMITTED)
        self.assertFalse(self.conn_handler.autocommit)

    def test_autocommit_setter(self):
        self.assertEqual(self.conn_handler._connection.isolation_level,
                         ISOLATION_LEVEL_READ_COMMITTED)
        self.conn_handler.autocommit = True
        self.assertEqual(self.conn_handler._connection.isolation_level,
                         ISOLATION_LEVEL_AUTOCOMMIT)
        self.conn_handler.autocommit = False
        self.assertEqual(self.conn_handler._connection.isolation_level,
                         ISOLATION_LEVEL_READ_COMMITTED)

    def test_autocommit_setter_error(self):
        with self.assertRaises(TypeError):
            self.conn_handler.autocommit = 'not a valid value'

    def test_check_sql_args(self):
        self.conn_handler._check_sql_args(['a', 'list'])
        self.conn_handler._check_sql_args(('a', 'tuple'))
        self.conn_handler._check_sql_args({'a': 'dict'})
        self.conn_handler._check_sql_args(None)

    def test_check_sql_args_error(self):
        with self.assertRaises(TypeError):
            self.conn_handler._check_sql_args("a string")

        with self.assertRaises(TypeError):
            self.conn_handler._check_sql_args(1)

        with self.assertRaises(TypeError):
            self.conn_handler._check_sql_args(1.2)

    def test_sql_executor_no_sql_args(self):
        sql = "INSERT INTO qiita.test_table (int_column) VALUES (1)"
        with self.conn_handler._sql_executor(sql) as cur:
            self.assertEqual(type(cur), DictCursor)

        self._assert_sql_equal([('foo', True, 1)])

    def test_sql_executor_with_sql_args(self):
        sql = "INSERT INTO qiita.test_table (int_column) VALUES (%s)"
        with self.conn_handler._sql_executor(sql, sql_args=(1,)) as cur:
            self.assertEqual(type(cur), DictCursor)

        self._assert_sql_equal([('foo', True, 1)])

    def test_sql_executor_many(self):
        sql = "INSERT INTO qiita.test_table (int_column) VALUES (%s)"
        sql_args = [(1,), (2,)]
        with self.conn_handler._sql_executor(sql, sql_args=sql_args,
                                             many=True) as cur:
            self.assertEqual(type(cur), DictCursor)

        self._assert_sql_equal([('foo', True, 1), ('foo', True, 2)])

    def test_execute_no_sql_args(self):
        sql = "INSERT INTO qiita.test_table (int_column) VALUES (1)"
        self.conn_handler.execute(sql)
        self._assert_sql_equal([('foo', True, 1)])

    def test_execute_with_sql_args(self):
        sql = "INSERT INTO qiita.test_table (int_column) VALUES (%s)"
        self.conn_handler.execute(sql, (1,))
        self._assert_sql_equal([('foo', True, 1)])

    def test_executemany(self):
        sql = "INSERT INTO qiita.test_table (int_column) VALUES (%s)"
        self.conn_handler.executemany(sql, [(1,), (2,)])
        self._assert_sql_equal([('foo', True, 1), ('foo', True, 2)])

    def test_execute_fetchone_no_sql_args(self):
        self._populate_test_table()
        sql = "SELECT str_column FROM qiita.test_table WHERE int_column = 1"
        obs = self.conn_handler.execute_fetchone(sql)
        self.assertEqual(obs, ['test1'])

    def test_execute_fetchone_with_sql_args(self):
        self._populate_test_table()
        sql = "SELECT str_column FROM qiita.test_table WHERE int_column = %s"
        obs = self.conn_handler.execute_fetchone(sql, (2,))
        self.assertEqual(obs, ['test2'])

    def test_execute_fetchall_no_sql_args(self):
        self._populate_test_table()
        sql = "SELECT * FROM qiita.test_table WHERE bool_column = False"
        obs = self.conn_handler.execute_fetchall(sql)
        self.assertEqual(obs, [['test3', False, 3], ['test4', False, 4]])

    def test_execute_fetchall_with_sql_args(self):
        self._populate_test_table()
        sql = "SELECT * FROM qiita.test_table WHERE bool_column = %s"
        obs = self.conn_handler.execute_fetchall(sql, (True,))
        self.assertEqual(obs, [['test1', True, 1], ['test2', True, 2]])


class TestTransaction(TestBase):
    def test_init(self):
        obs = Transaction("test_init")
        self.assertEqual(obs._name, "test_init")
        self.assertEqual(obs._queries, [])
        self.assertEqual(obs._results, [])
        self.assertEqual(obs.index, 0)
        self.assertTrue(
            isinstance(obs._conn_handler, SQLConnectionHandler))
        self.assertEqual(obs._contexts_entered, 0)

    def test_replace_placeholders(self):
        with Transaction("test_replace_placeholders") as trans:
            trans._results = [[["res1", 1]], [["res2a", 2], ["res2b", 3]],
                              None, None, [["res5", 5]]]
            sql = "SELECT 42"
            obs_sql, obs_args = trans._replace_placeholders(sql, ["{0:0:0}"])
            self.assertEqual(obs_sql, sql)
            self.assertEqual(obs_args, ["res1"])

            obs_sql, obs_args = trans._replace_placeholders(sql, ["{1:0:0}"])
            self.assertEqual(obs_sql, sql)
            self.assertEqual(obs_args, ["res2a"])

            obs_sql, obs_args = trans._replace_placeholders(sql, ["{1:1:1}"])
            self.assertEqual(obs_sql, sql)
            self.assertEqual(obs_args, [3])

            obs_sql, obs_args = trans._replace_placeholders(sql, ["{4:0:0}"])
            self.assertEqual(obs_sql, sql)
            self.assertEqual(obs_args, ["res5"])

            obs_sql, obs_args = trans._replace_placeholders(
                sql, ["foo", "{0:0:1}", "bar", "{1:0:1}"])
            self.assertEqual(obs_sql, sql)
            self.assertEqual(obs_args, ["foo", 1, "bar", 2])

    def test_replace_placeholders_index_error(self):
        with Transaction("test_replace_placeholders_index_error") as trans:
            trans._results = [[["res1", 1]], [["res2a", 2], ["res2b", 2]]]

            error_regex = ('The placeholder {0:0:3} does not match to any '
                           'previous result')
            with self.assertRaisesRegexp(ValueError, error_regex):
                trans._replace_placeholders("SELECT 42", ["{0:0:3}"])

            error_regex = ('The placeholder {0:2:0} does not match to any '
                           'previous result')
            with self.assertRaisesRegexp(ValueError, error_regex):
                trans._replace_placeholders("SELECT 42", ["{0:2:0}"])

            error_regex = ('The placeholder {2:0:0} does not match to any '
                           'previous result')
            with self.assertRaisesRegexp(ValueError, error_regex):
                trans._replace_placeholders("SELECT 42", ["{2:0:0}"])

    def test_replace_placeholders_type_error(self):
        with Transaction("test_replace_placeholders_type_error") as trans:
            trans._results = [None]

            error_regex = ("The placeholder {0:0:0} is referring to a SQL "
                           "query that does not retrieve data")
            with self.assertRaisesRegexp(ValueError, error_regex):
                trans._replace_placeholders("SELECT 42", ["{0:0:0}"])

    def test_add(self):
        with Transaction("test_add") as trans:
            self.assertEqual(trans._queries, [])

            sql1 = "INSERT INTO qiita.test_table (bool_column) VALUES (%s)"
            args1 = [True]
            trans.add(sql1, args1)
            sql2 = "INSERT INTO qiita.test_table (int_column) VALUES (1)"
            trans.add(sql2)

            exp = [(sql1, args1), (sql2, [])]
            self.assertEqual(trans._queries, exp)

            # Remove queries so __exit__ doesn't try to execute it
            trans._queries = []

    def test_add_many(self):
        with Transaction("test_add_many") as trans:
            self.assertEqual(trans._queries, [])

            sql = "INSERT INTO qiita.test_table (int_column) VALUES (%s)"
            args = [[1], [2], [3]]
            trans.add(sql, args, many=True)

            exp = [(sql, [1]), (sql, [2]), (sql, [3])]
            self.assertEqual(trans._queries, exp)

    def test_add_error(self):
        with Transaction("test_add_error") as trans:

            with self.assertRaises(TypeError):
                trans.add("SELECT 42", (1,))

            with self.assertRaises(TypeError):
                trans.add("SELECT 42", {'foo': 'bar'})

            with self.assertRaises(TypeError):
                trans.add("SELECT 42", [(1,), (1,)], many=True)

    def test_execute(self):
        with Transaction("test_execute") as trans:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s)"""
            trans.add(sql, ["test_insert", 2])
            sql = """UPDATE qiita.test_table
                     SET int_column = %s, bool_column = %s
                     WHERE str_column = %s"""
            trans.add(sql, [20, False, "test_insert"])
            obs = trans.execute()
            self.assertEqual(obs, [None, None])
            self._assert_sql_equal([])

        self._assert_sql_equal([("test_insert", False, 20)])

    def test_execute_many(self):
        with Transaction("test_execute_many") as trans:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s)"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            trans.add(sql, args, many=True)
            sql = """UPDATE qiita.test_table
                     SET int_column = %s, bool_column = %s
                     WHERE str_column = %s"""
            trans.add(sql, [20, False, 'insert2'])
            obs = trans.execute()
            self.assertEqual(obs, [None, None, None, None])

            self._assert_sql_equal([])

        self._assert_sql_equal([('insert1', True, 1),
                                ('insert3', True, 3),
                                ('insert2', False, 20)])

    def test_execute_return(self):
        with Transaction("test_execute_return") as trans:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s) RETURNING str_column, int_column"""
            trans.add(sql, ['test_insert', 2])
            sql = """UPDATE qiita.test_table SET bool_column = %s
                     WHERE str_column = %s RETURNING int_column"""
            trans.add(sql, [False, 'test_insert'])
            obs = trans.execute()
            self.assertEqual(obs, [[['test_insert', 2]], [[2]]])

    def test_execute_return_many(self):
        with Transaction("test_execute_return_many") as trans:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s) RETURNING str_column, int_column"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            trans.add(sql, args, many=True)
            sql = """UPDATE qiita.test_table SET bool_column = %s
                     WHERE str_column = %s"""
            trans.add(sql, [False, 'insert2'])
            sql = "SELECT * FROM qiita.test_table"
            trans.add(sql)
            obs = trans.execute()
            exp = [[['insert1', 1]],  # First query of the many query
                   [['insert2', 2]],  # Second query of the many query
                   [['insert3', 3]],  # Third query of the many query
                   None,  # Update query
                   [['insert1', True, 1],  # First result select
                    ['insert3', True, 3],  # Second result select
                    ['insert2', False, 2]]]  # Third result select
            self.assertEqual(obs, exp)

    def test_execute_placeholders(self):
        with Transaction("test_execute_placeholders") as trans:
            sql = """INSERT INTO qiita.test_table (int_column) VALUES (%s)
                     RETURNING str_column"""
            trans.add(sql, [2])
            sql = """UPDATE qiita.test_table SET str_column = %s
                     WHERE str_column = %s"""
            trans.add(sql, ["", "{0:0:0}"])
            obs = trans.execute()
            self.assertEqual(obs, [[['foo']], None])
            self._assert_sql_equal([])

        self._assert_sql_equal([('', True, 2)])

    def test_execute_error_bad_placeholder(self):
        with Transaction("test_execute_error_bad_placeholder") as trans:
            sql = "INSERT INTO qiita.test_table (int_column) VALUES (%s)"
            trans.add(sql, [2])
            sql = """UPDATE qiita.test_table SET bool_column = %s
                     WHERE str_column = %s"""
            trans.add(sql, [False, "{0:0:0}"])

            with self.assertRaises(ValueError):
                trans.execute()

            # make sure rollback correctly
            self._assert_sql_equal([])

    def test_execute_error_no_result_placeholder(self):
        with Transaction("test_execute_error_no_result_placeholder") as trans:
            sql = "INSERT INTO qiita.test_table (int_column) VALUES (%s)"
            trans.add(sql, [[1], [2], [3]], many=True)
            sql = """SELECT str_column FROM qiita.test_table
                     WHERE int_column = %s"""
            trans.add(sql, [4])
            sql = """UPDATE qiita.test_table SET bool_column = %s
                     WHERE str_column = %s"""
            trans.add(sql, [False, "{3:0:0}"])

            with self.assertRaises(ValueError):
                trans.execute()

            # make sure rollback correctly
            self._assert_sql_equal([])

    def test_execute_huge_transaction(self):
        with Transaction("test_execute_huge_transaction") as trans:
            # Add a lot of inserts to the transaction
            sql = "INSERT INTO qiita.test_table (int_column) VALUES (%s)"
            for i in range(1000):
                trans.add(sql, [i])
            # Add some updates to the transaction
            sql = """UPDATE qiita.test_table SET bool_column = %s
                     WHERE int_column = %s"""
            for i in range(500):
                trans.add(sql, [False, i])
            # Make the transaction fail with the last insert
            sql = """INSERT INTO qiita.table_to_make (the_trans_to_fail)
                     VALUES (1)"""
            trans.add(sql)

            with self.assertRaises(ValueError):
                trans.execute()

            # make sure rollback correctly
            self._assert_sql_equal([])

    def test_execute_commit_false(self):
        with Transaction("test_execute_commit_false") as trans:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s) RETURNING str_column, int_column"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            trans.add(sql, args, many=True)

            obs = trans.execute()
            exp = [[['insert1', 1]], [['insert2', 2]], [['insert3', 3]]]
            self.assertEqual(obs, exp)

            self._assert_sql_equal([])

            trans.commit()

            self._assert_sql_equal([('insert1', True, 1), ('insert2', True, 2),
                                    ('insert3', True, 3)])

    def test_execute_commit_false_rollback(self):
        with Transaction("test_execute_commit_false_rollback") as trans:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s) RETURNING str_column, int_column"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            trans.add(sql, args, many=True)

            obs = trans.execute()
            exp = [[['insert1', 1]], [['insert2', 2]], [['insert3', 3]]]
            self.assertEqual(obs, exp)

            self._assert_sql_equal([])

            trans.rollback()

            self._assert_sql_equal([])

    def test_execute_commit_false_wipe_queries(self):
        with Transaction("test_execute_commit_false_wipe_queries") as trans:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s) RETURNING str_column, int_column"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            trans.add(sql, args, many=True)

            obs = trans.execute()
            exp = [[['insert1', 1]], [['insert2', 2]], [['insert3', 3]]]
            self.assertEqual(obs, exp)

            self._assert_sql_equal([])

            sql = """UPDATE qiita.test_table SET bool_column = %s
                     WHERE str_column = %s"""
            args = [False, 'insert2']
            trans.add(sql, args)
            self.assertEqual(trans._queries, [(sql, args)])

            trans.execute()
            self._assert_sql_equal([])

        self._assert_sql_equal([('insert1', True, 1), ('insert3', True, 3),
                                ('insert2', False, 2)])

    def test_context_manager_rollback(self):
        try:
            with Transaction("test_context_manager_rollback") as trans:
                sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s) RETURNING str_column, int_column"""
                args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
                trans.add(sql, args, many=True)

                trans.execute()
                raise ValueError("Force exiting the context manager")
        except ValueError:
            pass
        self._assert_sql_equal([])
        self.assertEqual(
            trans._conn_handler._connection.get_transaction_status(),
            TRANSACTION_STATUS_IDLE)

    def test_context_manager_execute(self):
        with Transaction("test_context_manager_no_commit") as trans:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                 VALUES (%s, %s) RETURNING str_column, int_column"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            trans.add(sql, args, many=True)
            self._assert_sql_equal([])

        self._assert_sql_equal([('insert1', True, 1), ('insert2', True, 2),
                                ('insert3', True, 3)])
        self.assertEqual(
            trans._conn_handler._connection.get_transaction_status(),
            TRANSACTION_STATUS_IDLE)

    def test_context_manager_no_commit(self):
        with Transaction("test_context_manager_no_commit") as trans:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                 VALUES (%s, %s) RETURNING str_column, int_column"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            trans.add(sql, args, many=True)

            trans.execute()
            self._assert_sql_equal([])

        self._assert_sql_equal([('insert1', True, 1), ('insert2', True, 2),
                                ('insert3', True, 3)])
        self.assertEqual(
            trans._conn_handler._connection.get_transaction_status(),
            TRANSACTION_STATUS_IDLE)

    def test_context_manager_multiple(self):
        trans = Transaction("test_context_manager_multiple")
        self.assertEqual(trans._contexts_entered, 0)

        with trans:
            self.assertEqual(trans._contexts_entered, 1)

            trans.add("SELECT 42")
            with trans:
                self.assertEqual(trans._contexts_entered, 2)
                sql = """INSERT INTO qiita.test_table (str_column, int_column)
                         VALUES (%s, %s) RETURNING str_column, int_column"""
                args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
                trans.add(sql, args, many=True)

            # We exited the second context, nothing should have been executed
            self.assertEqual(trans._contexts_entered, 1)
            self.assertEqual(
                trans._conn_handler._connection.get_transaction_status(),
                TRANSACTION_STATUS_IDLE)
            self._assert_sql_equal([])

        # We have exited the first context, everything should have been
        # executed and committed
        self.assertEqual(trans._contexts_entered, 0)
        self._assert_sql_equal([('insert1', True, 1), ('insert2', True, 2),
                                ('insert3', True, 3)])
        self.assertEqual(
            trans._conn_handler._connection.get_transaction_status(),
            TRANSACTION_STATUS_IDLE)

    def test_context_manager_checker(self):
        t = Transaction("test_context_managet_checker")

        with self.assertRaises(RuntimeError):
            t.add("SELECT 42")

        with self.assertRaises(RuntimeError):
            t.execute()

        with self.assertRaises(RuntimeError):
            t.commit()

        with self.assertRaises(RuntimeError):
            t.rollback()

        with t:
            t.add("SELECT 42")

        with self.assertRaises(RuntimeError):
            t.execute()

    def test_index(self):
        with Transaction("test_index") as trans:
            self.assertEqual(trans.index, 0)

            trans.add("SELECT 42")
            self.assertEqual(trans.index, 1)

            sql = "INSERT INTO qiita.test_table (int_column) VALUES (%s)"
            args = [[1], [2], [3]]
            trans.add(sql, args, many=True)
            self.assertEqual(trans.index, 4)

            trans.execute()
            self.assertEqual(trans.index, 4)

            trans.add(sql, args, many=True)
            self.assertEqual(trans.index, 7)

if __name__ == "__main__":
    main()
