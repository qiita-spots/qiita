from unittest import TestCase, main

from psycopg2._psycopg import connection
from psycopg2.extras import DictCursor
from psycopg2 import connect
from psycopg2.extensions import (ISOLATION_LEVEL_AUTOCOMMIT,
                                 ISOLATION_LEVEL_READ_COMMITTED)

from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.exceptions import QiitaDBExecutionError
from qiita_core.util import qiita_test_checker
from qiita_core.qiita_settings import qiita_config


DB_TEST_TABLE = """CREATE TABLE qiita.test_table (
    str_column      varchar DEFAULT 'foo' NOT NULL,
    bool_column     bool DEFAULT True NOT NULL,
    int_column      bigint NOT NULL);"""


@qiita_test_checker()
class TestConnHandler(TestCase):
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
        with self.assertRaises(RuntimeError):
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

    def test_create_queue(self):
        self.assertEqual(self.conn_handler.queues, {})
        self.conn_handler.create_queue("toy_queue")
        self.assertEqual(self.conn_handler.queues, {'toy_queue': []})

    def test_create_queue_error(self):
        self.conn_handler.create_queue("test_queue")
        with self.assertRaises(KeyError):
            self.conn_handler.create_queue("test_queue")

    def test_list_queues(self):
        self.assertEqual(self.conn_handler.list_queues(), [])
        self.conn_handler.create_queue("test_queue")
        self.assertEqual(self.conn_handler.list_queues(), ["test_queue"])

    def test_add_to_queue(self):
        self.conn_handler.create_queue("test_queue")

        sql1 = "INSERT INTO qiita.test_table (bool_column) VALUES (%s)"
        sql_args1 = (True,)
        self.conn_handler.add_to_queue("test_queue", sql1, sql_args1)
        self.assertEqual(self.conn_handler.queues,
                         {"test_queue": [(sql1, sql_args1)]})

        sql2 = "INSERT INTO qiita.test_table (int_column) VALUES (1)"
        self.conn_handler.add_to_queue("test_queue", sql2)
        self.assertEqual(self.conn_handler.queues,
                         {"test_queue": [(sql1, sql_args1), (sql2, None)]})

    def test_add_to_queue_many(self):
        self.conn_handler.create_queue("test_queue")

        sql = "INSERT INTO qiita.test_table (int_column) VALUES (%s)"
        sql_args = [(1,), (2,), (3,)]
        self.conn_handler.add_to_queue("test_queue", sql, sql_args, many=True)
        self.assertEqual(self.conn_handler.queues,
                         {"test_queue": [(sql, (1,)), (sql, (2,)),
                                         (sql, (3,))]})

    def test_execute_queue(self):
        self.conn_handler.create_queue("test_queue")
        sql = """INSERT INTO qiita.test_table (str_column, int_column)
                 VALUES (%s, %s)"""
        self.conn_handler.add_to_queue("test_queue", sql, ['test_insert', '2'])
        sql = """UPDATE qiita.test_table
                 SET int_column = 20, bool_column = FALSE
                 WHERE str_column = %s"""
        self.conn_handler.add_to_queue("test_queue", sql, ['test_insert'])
        obs = self.conn_handler.execute_queue("test_queue")
        self.assertEqual(obs, [])
        self._assert_sql_equal([("test_insert", False, 20)])

    def test_execute_queue_many(self):
        sql = """INSERT INTO qiita.test_table (str_column, int_column)
                 VALUES (%s, %s)"""
        sql_args = [('insert1', 1), ('insert2', 2), ('insert3', 3)]

        self.conn_handler.create_queue("test_queue")
        self.conn_handler.add_to_queue("test_queue", sql, sql_args, many=True)
        sql = """UPDATE qiita.test_table
                 SET int_column = 20, bool_column = FALSE
                 WHERE str_column = %s"""
        self.conn_handler.add_to_queue("test_queue", sql, ['insert2'])
        obs = self.conn_handler.execute_queue('test_queue')
        self.assertEqual(obs, [])

        self._assert_sql_equal([('insert1', True, 1), ('insert3', True, 3),
                                ('insert2', False, 20)])

    def test_execute_queue_last_return(self):
        self.conn_handler.create_queue("test_queue")
        sql = """INSERT INTO qiita.test_table (str_column, int_column)
                 VALUES (%s, %s)"""
        self.conn_handler.add_to_queue("test_queue", sql, ['test_insert', '2'])
        sql = """UPDATE qiita.test_table SET bool_column = FALSE
                 WHERE str_column = %s RETURNING int_column"""
        self.conn_handler.add_to_queue("test_queue", sql, ['test_insert'])
        obs = self.conn_handler.execute_queue("test_queue")
        self.assertEqual(obs, [2])

    def test_execute_queue_placeholders(self):
        self.conn_handler.create_queue("test_queue")
        sql = """INSERT INTO qiita.test_table (int_column) VALUES (%s)
                 RETURNING str_column"""
        self.conn_handler.add_to_queue("test_queue", sql, (2,))
        sql = """UPDATE qiita.test_table SET bool_column = FALSE
                 WHERE str_column = %s"""
        self.conn_handler.add_to_queue("test_queue", sql, ('{0}',))
        obs = self.conn_handler.execute_queue("test_queue")
        self.assertEqual(obs, [])
        self._assert_sql_equal([('foo', False, 2)])

    def test_execute_queue_placeholders_regex(self):
        self.conn_handler.create_queue("test_queue")
        sql = """INSERT INTO qiita.test_table (int_column)
                 VALUES (%s) RETURNING str_column"""
        self.conn_handler.add_to_queue("test_queue", sql, (1,))
        sql = """UPDATE qiita.test_table SET str_column = %s
                 WHERE str_column = %s"""
        self.conn_handler.add_to_queue("test_queue", sql, ("", "{0}"))
        obs = self.conn_handler.execute_queue("test_queue")
        self.assertEqual(obs, [])
        self._assert_sql_equal([('', True, 1)])

    def test_execute_queue_fail(self):
        self.conn_handler.create_queue("test_queue")
        sql = """INSERT INTO qiita.test_table (int_column) VALUES (%s)"""
        self.conn_handler.add_to_queue("test_queue", sql, (2,))
        sql = """UPDATE qiita.test_table SET bool_column = False
                 WHERE str_column = %s"""
        self.conn_handler.add_to_queue("test_queue", sql, ('{0}',))

        with self.assertRaises(QiitaDBExecutionError):
            self.conn_handler.execute_queue("test_queue")

        # make sure rollback correctly
        self._assert_sql_equal([])

    def test_huge_queue(self):
        self.conn_handler.create_queue("test_queue")
        # Add a lof of inserts to the queue
        sql = "INSERT INTO qiita.test_table (int_column) VALUES (%s)"
        for x in range(1000):
            self.conn_handler.add_to_queue("test_queue", sql, (x,))

        # Make the queue fail with the last insert
        sql = "INSERT INTO qiita.table_to_make (the_queue_to_fail) VALUES (1)"
        self.conn_handler.add_to_queue("test_queue", sql)

        with self.assertRaises(QiitaDBExecutionError):
            self.conn_handler.execute_queue("test_queue")

        # make sure rollback correctly
        self._assert_sql_equal([])

    def test_get_temp_queue(self):
        my_queue = self.conn_handler.get_temp_queue()
        self.assertTrue(my_queue in self.conn_handler.list_queues())

        self.conn_handler.add_to_queue(my_queue,
                                       "SELECT * from qiita.qiita_user")
        self.conn_handler.add_to_queue(my_queue,
                                       "SELECT * from qiita.user_level")
        self.conn_handler.execute_queue(my_queue)

        self.assertTrue(my_queue not in self.conn_handler.list_queues())

if __name__ == "__main__":
    main()
