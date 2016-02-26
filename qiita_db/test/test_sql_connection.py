from unittest import TestCase, main
from os import remove, close
from os.path import exists
from tempfile import mkstemp

from psycopg2._psycopg import connection
from psycopg2 import connect
from psycopg2.extensions import TRANSACTION_STATUS_IDLE

from qiita_core.util import qiita_test_checker
from qiita_core.qiita_settings import qiita_config
import qiita_db as qdb


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
        self._files_to_remove = []

    def tearDown(self):
        for fp in self._files_to_remove:
            if exists(fp):
                remove(fp)

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


class TestTransaction(TestBase):
    def test_init(self):
        obs = qdb.sql_connection.Transaction()
        self.assertEqual(obs._queries, [])
        self.assertEqual(obs._results, [])
        self.assertEqual(obs._connection, None)
        self.assertEqual(obs._contexts_entered, 0)
        with obs:
            pass
        self.assertTrue(isinstance(obs._connection, connection))

    def test_add(self):
        with qdb.sql_connection.TRN:
            self.assertEqual(qdb.sql_connection.TRN._queries, [])

            sql1 = "INSERT INTO qiita.test_table (bool_column) VALUES (%s)"
            args1 = [True]
            qdb.sql_connection.TRN.add(sql1, args1)
            sql2 = "INSERT INTO qiita.test_table (int_column) VALUES (1)"
            qdb.sql_connection.TRN.add(sql2)
            args3 = (False,)
            qdb.sql_connection.TRN.add(sql1, args3)
            sql3 = "INSERT INTO qiita.test_table (int_column) VALEUS (%(foo)s)"
            args4 = {'foo': 1}
            qdb.sql_connection.TRN.add(sql3, args4)

            exp = [(sql1, args1), (sql2, None), (sql1, args3), (sql3, args4)]
            self.assertEqual(qdb.sql_connection.TRN._queries, exp)

            # Remove queries so __exit__ doesn't try to execute it
            qdb.sql_connection.TRN._queries = []

    def test_add_many(self):
        with qdb.sql_connection.TRN:
            self.assertEqual(qdb.sql_connection.TRN._queries, [])

            sql = "INSERT INTO qiita.test_table (int_column) VALUES (%s)"
            args = [[1], [2], [3]]
            qdb.sql_connection.TRN.add(sql, args, many=True)

            exp = [(sql, [1]), (sql, [2]), (sql, [3])]
            self.assertEqual(qdb.sql_connection.TRN._queries, exp)

    def test_add_error(self):
        with qdb.sql_connection.TRN:
            with self.assertRaises(TypeError):
                qdb.sql_connection.TRN.add("SELECT 42", 1)

            with self.assertRaises(TypeError):
                qdb.sql_connection.TRN.add("SELECT 42", {'foo': 'bar'},
                                           many=True)

            with self.assertRaises(TypeError):
                qdb.sql_connection.TRN.add("SELECT 42", [1, 1], many=True)

    def test_execute(self):
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s)"""
            qdb.sql_connection.TRN.add(sql, ["test_insert", 2])
            sql = """UPDATE qiita.test_table
                     SET int_column = %s, bool_column = %s
                     WHERE str_column = %s"""
            qdb.sql_connection.TRN.add(sql, [20, False, "test_insert"])
            obs = qdb.sql_connection.TRN.execute()
            self.assertEqual(obs, [None, None])
            self._assert_sql_equal([])

        self._assert_sql_equal([("test_insert", False, 20)])

    def test_execute_many(self):
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s)"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            qdb.sql_connection.TRN.add(sql, args, many=True)
            sql = """UPDATE qiita.test_table
                     SET int_column = %s, bool_column = %s
                     WHERE str_column = %s"""
            qdb.sql_connection.TRN.add(sql, [20, False, 'insert2'])
            obs = qdb.sql_connection.TRN.execute()
            self.assertEqual(obs, [None, None, None, None])

            self._assert_sql_equal([])

        self._assert_sql_equal([('insert1', True, 1),
                                ('insert3', True, 3),
                                ('insert2', False, 20)])

    def test_execute_return(self):
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s) RETURNING str_column, int_column"""
            qdb.sql_connection.TRN.add(sql, ['test_insert', 2])
            sql = """UPDATE qiita.test_table SET bool_column = %s
                     WHERE str_column = %s RETURNING int_column"""
            qdb.sql_connection.TRN.add(sql, [False, 'test_insert'])
            obs = qdb.sql_connection.TRN.execute()
            self.assertEqual(obs, [[['test_insert', 2]], [[2]]])

    def test_execute_return_many(self):
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s) RETURNING str_column, int_column"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            qdb.sql_connection.TRN.add(sql, args, many=True)
            sql = """UPDATE qiita.test_table SET bool_column = %s
                     WHERE str_column = %s"""
            qdb.sql_connection.TRN.add(sql, [False, 'insert2'])
            sql = "SELECT * FROM qiita.test_table"
            qdb.sql_connection.TRN.add(sql)
            obs = qdb.sql_connection.TRN.execute()
            exp = [[['insert1', 1]],  # First query of the many query
                   [['insert2', 2]],  # Second query of the many query
                   [['insert3', 3]],  # Third query of the many query
                   None,  # Update query
                   [['insert1', True, 1],  # First result select
                    ['insert3', True, 3],  # Second result select
                    ['insert2', False, 2]]]  # Third result select
            self.assertEqual(obs, exp)

    def test_execute_huge_transaction(self):
        with qdb.sql_connection.TRN:
            # Add a lot of inserts to the transaction
            sql = "INSERT INTO qiita.test_table (int_column) VALUES (%s)"
            for i in range(1000):
                qdb.sql_connection.TRN.add(sql, [i])
            # Add some updates to the transaction
            sql = """UPDATE qiita.test_table SET bool_column = %s
                     WHERE int_column = %s"""
            for i in range(500):
                qdb.sql_connection.TRN.add(sql, [False, i])
            # Make the transaction fail with the last insert
            sql = """INSERT INTO qiita.table_to_make (the_trans_to_fail)
                     VALUES (1)"""
            qdb.sql_connection.TRN.add(sql)

            with self.assertRaises(ValueError):
                qdb.sql_connection.TRN.execute()

            # make sure rollback correctly
            self._assert_sql_equal([])

    def test_execute_commit_false(self):
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s) RETURNING str_column, int_column"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            qdb.sql_connection.TRN.add(sql, args, many=True)

            obs = qdb.sql_connection.TRN.execute()
            exp = [[['insert1', 1]], [['insert2', 2]], [['insert3', 3]]]
            self.assertEqual(obs, exp)

            self._assert_sql_equal([])

            qdb.sql_connection.TRN.commit()

            self._assert_sql_equal([('insert1', True, 1), ('insert2', True, 2),
                                    ('insert3', True, 3)])

    def test_execute_commit_false_rollback(self):
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s) RETURNING str_column, int_column"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            qdb.sql_connection.TRN.add(sql, args, many=True)

            obs = qdb.sql_connection.TRN.execute()
            exp = [[['insert1', 1]], [['insert2', 2]], [['insert3', 3]]]
            self.assertEqual(obs, exp)

            self._assert_sql_equal([])

            qdb.sql_connection.TRN.rollback()

            self._assert_sql_equal([])

    def test_execute_commit_false_wipe_queries(self):
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s) RETURNING str_column, int_column"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            qdb.sql_connection.TRN.add(sql, args, many=True)

            obs = qdb.sql_connection.TRN.execute()
            exp = [[['insert1', 1]], [['insert2', 2]], [['insert3', 3]]]
            self.assertEqual(obs, exp)

            self._assert_sql_equal([])

            sql = """UPDATE qiita.test_table SET bool_column = %s
                     WHERE str_column = %s"""
            args = [False, 'insert2']
            qdb.sql_connection.TRN.add(sql, args)
            self.assertEqual(qdb.sql_connection.TRN._queries, [(sql, args)])

            qdb.sql_connection.TRN.execute()
            self._assert_sql_equal([])

        self._assert_sql_equal([('insert1', True, 1), ('insert3', True, 3),
                                ('insert2', False, 2)])

    def test_execute_fetchlast(self):
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s) RETURNING str_column, int_column"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            qdb.sql_connection.TRN.add(sql, args, many=True)

            sql = """SELECT EXISTS(
                        SELECT * FROM qiita.test_table WHERE int_column=%s)"""
            qdb.sql_connection.TRN.add(sql, [2])
            self.assertTrue(qdb.sql_connection.TRN.execute_fetchlast())

    def test_execute_fetchindex(self):
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s) RETURNING str_column, int_column"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            qdb.sql_connection.TRN.add(sql, args, many=True)
            self.assertEqual(qdb.sql_connection.TRN.execute_fetchindex(),
                             [['insert3', 3]])

            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s) RETURNING str_column, int_column"""
            args = [['insert4', 4], ['insert5', 5], ['insert6', 6]]
            qdb.sql_connection.TRN.add(sql, args, many=True)
            self.assertEqual(qdb.sql_connection.TRN.execute_fetchindex(3),
                             [['insert4', 4]])

    def test_execute_fetchflatten(self):
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s)"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            qdb.sql_connection.TRN.add(sql, args, many=True)

            sql = "SELECT str_column, int_column FROM qiita.test_table"
            qdb.sql_connection.TRN.add(sql)

            sql = "SELECT int_column FROM qiita.test_table"
            qdb.sql_connection.TRN.add(sql)
            obs = qdb.sql_connection.TRN.execute_fetchflatten()
            self.assertEqual(obs, [1, 2, 3])

            sql = "SELECT 42"
            qdb.sql_connection.TRN.add(sql)
            obs = qdb.sql_connection.TRN.execute_fetchflatten(idx=3)
            self.assertEqual(obs, ['insert1', 1, 'insert2', 2, 'insert3', 3])

    def test_context_manager_rollback(self):
        try:
            with qdb.sql_connection.TRN:
                sql = """INSERT INTO qiita.test_table (str_column, int_column)
                     VALUES (%s, %s) RETURNING str_column, int_column"""
                args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
                qdb.sql_connection.TRN.add(sql, args, many=True)

                qdb.sql_connection.TRN.execute()
                raise ValueError("Force exiting the context manager")
        except ValueError:
            pass
        self._assert_sql_equal([])
        self.assertEqual(
            qdb.sql_connection.TRN._connection.get_transaction_status(),
            TRANSACTION_STATUS_IDLE)

    def test_context_manager_execute(self):
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                 VALUES (%s, %s) RETURNING str_column, int_column"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            qdb.sql_connection.TRN.add(sql, args, many=True)
            self._assert_sql_equal([])

        self._assert_sql_equal([('insert1', True, 1), ('insert2', True, 2),
                                ('insert3', True, 3)])
        self.assertEqual(
            qdb.sql_connection.TRN._connection.get_transaction_status(),
            TRANSACTION_STATUS_IDLE)

    def test_context_manager_no_commit(self):
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                 VALUES (%s, %s) RETURNING str_column, int_column"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            qdb.sql_connection.TRN.add(sql, args, many=True)

            qdb.sql_connection.TRN.execute()
            self._assert_sql_equal([])

        self._assert_sql_equal([('insert1', True, 1), ('insert2', True, 2),
                                ('insert3', True, 3)])
        self.assertEqual(
            qdb.sql_connection.TRN._connection.get_transaction_status(),
            TRANSACTION_STATUS_IDLE)

    def test_context_manager_multiple(self):
        self.assertEqual(qdb.sql_connection.TRN._contexts_entered, 0)

        with qdb.sql_connection.TRN:
            self.assertEqual(qdb.sql_connection.TRN._contexts_entered, 1)

            qdb.sql_connection.TRN.add("SELECT 42")
            with qdb.sql_connection.TRN:
                self.assertEqual(qdb.sql_connection.TRN._contexts_entered, 2)
                sql = """INSERT INTO qiita.test_table (str_column, int_column)
                         VALUES (%s, %s) RETURNING str_column, int_column"""
                args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
                qdb.sql_connection.TRN.add(sql, args, many=True)

            # We exited the second context, nothing should have been executed
            self.assertEqual(qdb.sql_connection.TRN._contexts_entered, 1)
            self.assertEqual(
                qdb.sql_connection.TRN._connection.get_transaction_status(),
                TRANSACTION_STATUS_IDLE)
            self._assert_sql_equal([])

        # We have exited the first context, everything should have been
        # executed and committed
        self.assertEqual(qdb.sql_connection.TRN._contexts_entered, 0)
        self._assert_sql_equal([('insert1', True, 1), ('insert2', True, 2),
                                ('insert3', True, 3)])
        self.assertEqual(
            qdb.sql_connection.TRN._connection.get_transaction_status(),
            TRANSACTION_STATUS_IDLE)

    def test_context_manager_multiple_2(self):
        self.assertEqual(qdb.sql_connection.TRN._contexts_entered, 0)

        def tester():
            self.assertEqual(qdb.sql_connection.TRN._contexts_entered, 1)
            with qdb.sql_connection.TRN:
                self.assertEqual(qdb.sql_connection.TRN._contexts_entered, 2)
                sql = """SELECT EXISTS(
                        SELECT * FROM qiita.test_table WHERE int_column=%s)"""
                qdb.sql_connection.TRN.add(sql, [2])
                self.assertTrue(qdb.sql_connection.TRN.execute_fetchlast())
            self.assertEqual(qdb.sql_connection.TRN._contexts_entered, 1)

        with qdb.sql_connection.TRN:
            self.assertEqual(qdb.sql_connection.TRN._contexts_entered, 1)
            sql = """INSERT INTO qiita.test_table (str_column, int_column)
                         VALUES (%s, %s) RETURNING str_column, int_column"""
            args = [['insert1', 1], ['insert2', 2], ['insert3', 3]]
            qdb.sql_connection.TRN.add(sql, args, many=True)
            tester()
            self.assertEqual(qdb.sql_connection.TRN._contexts_entered, 1)
            self._assert_sql_equal([])

        self.assertEqual(qdb.sql_connection.TRN._contexts_entered, 0)
        self._assert_sql_equal([('insert1', True, 1), ('insert2', True, 2),
                                ('insert3', True, 3)])
        self.assertEqual(
            qdb.sql_connection.TRN._connection.get_transaction_status(),
            TRANSACTION_STATUS_IDLE)

    def test_post_commit_funcs(self):
        fd, fp = mkstemp()
        close(fd)
        self._files_to_remove.append(fp)

        def func(fp):
            with open(fp, 'w') as f:
                f.write('\n')

        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add("SELECT 42")
            qdb.sql_connection.TRN.add_post_commit_func(func, fp)

        self.assertTrue(exists(fp))

    def test_post_commit_funcs_error(self):
        def func():
            raise ValueError()

        with self.assertRaises(RuntimeError):
            with qdb.sql_connection.TRN:
                qdb.sql_connection.TRN.add("SELECT 42")
                qdb.sql_connection.TRN.add_post_commit_func(func)

    def test_post_rollback_funcs(self):
        fd, fp = mkstemp()
        close(fd)
        self._files_to_remove.append(fp)

        def func(fp):
            with open(fp, 'w') as f:
                f.write('\n')

        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add("SELECT 42")
            qdb.sql_connection.TRN.add_post_rollback_func(func, fp)
            qdb.sql_connection.TRN.rollback()

        self.assertTrue(exists(fp))

    def test_post_rollback_funcs_error(self):
        def func():
            raise ValueError()

        with self.assertRaises(RuntimeError):
            with qdb.sql_connection.TRN:
                qdb.sql_connection.TRN.add("SELECT 42")
                qdb.sql_connection.TRN.add_post_rollback_func(func)
                qdb.sql_connection.TRN.rollback()

    def test_context_manager_checker(self):
        with self.assertRaises(RuntimeError):
            qdb.sql_connection.TRN.add("SELECT 42")

        with self.assertRaises(RuntimeError):
            qdb.sql_connection.TRN.execute()

        with self.assertRaises(RuntimeError):
            qdb.sql_connection.TRN.commit()

        with self.assertRaises(RuntimeError):
            qdb.sql_connection.TRN.rollback()

        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add("SELECT 42")

        with self.assertRaises(RuntimeError):
            qdb.sql_connection.TRN.execute()

    def test_index(self):
        with qdb.sql_connection.TRN:
            self.assertEqual(qdb.sql_connection.TRN.index, 0)

            qdb.sql_connection.TRN.add("SELECT 42")
            self.assertEqual(qdb.sql_connection.TRN.index, 1)

            sql = "INSERT INTO qiita.test_table (int_column) VALUES (%s)"
            args = [[1], [2], [3]]
            qdb.sql_connection.TRN.add(sql, args, many=True)
            self.assertEqual(qdb.sql_connection.TRN.index, 4)

            qdb.sql_connection.TRN.execute()
            self.assertEqual(qdb.sql_connection.TRN.index, 4)

            qdb.sql_connection.TRN.add(sql, args, many=True)
            self.assertEqual(qdb.sql_connection.TRN.index, 7)

        self.assertEqual(qdb.sql_connection.TRN.index, 0)

if __name__ == "__main__":
    main()
