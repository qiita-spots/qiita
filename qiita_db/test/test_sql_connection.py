from unittest import TestCase, main

from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.exceptions import QiitaDBExecutionError
from qiita_core.util import qiita_test_checker


@qiita_test_checker()
class TestConnHandler(TestCase):
    def test_create_queue(self):
        self.conn_handler.create_queue("toy_queue")
        self.assertEqual(self.conn_handler.list_queues(), ["toy_queue"])

    def test_close(self):
        self.assertEqual(self.conn_handler._user_conn.closed, 0)
        self.conn_handler.close()
        self.assertNotEqual(self.conn_handler._user_conn.closed, 0)

    def test_run_queue(self):
        self.conn_handler.create_queue("toy_queue")
        self.conn_handler.add_to_queue(
            "toy_queue", "INSERT INTO qiita.qiita_user (email, name, password,"
            "phone) VALUES (%s, %s, %s, %s)",
            ['insert@foo.bar', 'Toy', 'pass', '111-111-11112'])
        self.conn_handler.add_to_queue(
            "toy_queue", "UPDATE qiita.qiita_user SET user_level_id = 1, "
            "phone = '222-222-2221' WHERE email = %s",
            ['insert@foo.bar'])
        obs = self.conn_handler.execute_queue("toy_queue")
        self.assertEqual(obs, [])
        obs = self.conn_handler.execute_fetchall(
            "SELECT * from qiita.qiita_user WHERE email = %s",
            ['insert@foo.bar'])
        exp = [['insert@foo.bar', 1, 'pass', 'Toy', None, None, '222-222-2221',
                None, None, None]]
        self.assertEqual(obs, exp)

    def test_run_queue_many(self):
        sql = ("INSERT INTO qiita.qiita_user (email, name, password,"
               "phone) VALUES (%s, %s, %s, %s)")
        sql_args = [
            ('p1@test.com', 'p1', 'pass1', '111-111'),
            ('p2@test.com', 'p2', 'pass2', '111-222')
            ]
        self.conn_handler.create_queue("toy_queue")
        self.conn_handler.add_to_queue(
            "toy_queue", sql, sql_args, many=True)
        self.conn_handler.execute_queue('toy_queue')

        # make sure both users added
        obs = self.conn_handler.execute_fetchall(
            "SELECT * from qiita.qiita_user WHERE email = %s",
            ['p1@test.com'])
        exp = [['p1@test.com', 5, 'pass1', 'p1', None, None, '111-111',
                None, None, None]]
        self.assertEqual(obs, exp)
        obs = self.conn_handler.execute_fetchall(
            "SELECT * from qiita.qiita_user WHERE email = %s",
            ['p2@test.com'])
        exp = [['p2@test.com', 5, 'pass2', 'p2', None, None, '111-222',
                None, None, None]]
        self.assertEqual(obs, exp)

    def test_run_queue_last_return(self):
        self.conn_handler.create_queue("toy_queue")
        self.conn_handler.add_to_queue(
            "toy_queue", "INSERT INTO qiita.qiita_user (email, name, password,"
            "phone) VALUES (%s, %s, %s, %s)",
            ['insert@foo.bar', 'Toy', 'pass', '111-111-11112'])
        self.conn_handler.add_to_queue(
            "toy_queue", "UPDATE qiita.qiita_user SET user_level_id = 1, "
            "phone = '222-222-2221' WHERE email = %s RETURNING phone",
            ['insert@foo.bar'])
        obs = self.conn_handler.execute_queue("toy_queue")
        self.assertEqual(obs, ['222-222-2221'])

    def test_run_queue_placeholders(self):
        self.conn_handler.create_queue("toy_queue")
        self.conn_handler.add_to_queue(
            "toy_queue", "INSERT INTO qiita.qiita_user (email, name, password,"
            "phone) VALUES (%s, %s, %s, %s) RETURNING email, password",
            ['insert@foo.bar', 'Toy', 'pass', '111-111-11112'])
        self.conn_handler.add_to_queue(
            "toy_queue", "UPDATE qiita.qiita_user SET user_level_id = 1, "
            "phone = '222-222-2221' WHERE email = %s AND password = %s",
            ['{0}', '{1}'])
        obs = self.conn_handler.execute_queue("toy_queue")
        self.assertEqual(obs, [])
        obs = self.conn_handler.execute_fetchall(
            "SELECT * from qiita.qiita_user WHERE email = %s",
            ['insert@foo.bar'])
        exp = [['insert@foo.bar', 1, 'pass', 'Toy', None, None, '222-222-2221',
                None, None, None]]
        self.assertEqual(obs, exp)

    def test_queue_fail(self):
        """Fail if no results data exists for substitution"""
        self.conn_handler = SQLConnectionHandler()
        self.conn_handler.create_queue("toy_queue")
        self.conn_handler.add_to_queue(
            "toy_queue",
            "INSERT INTO qiita.qiita_user (email, name, password) VALUES "
            "(%s, %s, %s)", ['somebody@foo.bar', 'Toy', 'pass'])
        self.conn_handler.add_to_queue(
            "toy_queue", "UPDATE qiita.qiita_user SET user_level_id = 1 "
            "WHERE email = %s and password = %s", [{0}, {1}])

        with self.assertRaises(QiitaDBExecutionError):
            self.conn_handler.execute_queue("toy_queue")

        # make sure roll back correctly
        obs = self.conn_handler.execute_fetchall(
            "SELECT * from qiita.qiita_user WHERE email = %s",
            ['somebody@foo.bar'])
        self.assertEqual(obs, [])

    def test_huge_queue(self):
        self.conn_handler = SQLConnectionHandler()
        self.conn_handler.create_queue("toy_queue")
        # add tons of inserts to queue
        for x in range(120):
            self.conn_handler.add_to_queue(
                "toy_queue",
                "INSERT INTO qiita.qiita_user (email, name, password) VALUES "
                "(%s, %s, %s)", ['%dsomebody@foo.bar' % x, 'Toy', 'pass'])
        # add failing insert as final item in queue
        self.conn_handler.add_to_queue(
            "toy_queue",
            "INSERT INTO qiita.qiita_BADTABLE (email, name, password) VALUES "
            "(%s, %s, %s)", ['%dsomebody@foo.bar' % x, 'Toy', 'pass'])
        self.conn_handler.add_to_queue(
            "toy_queue", "UPDATE qiita.qiita_user SET user_level_id = 1 "
            "WHERE email = %s and password = %s", [{0}, {1}])
        with self.assertRaises(QiitaDBExecutionError):
            self.conn_handler.execute_queue("toy_queue")

        # make sure roll back correctly
        obs = self.conn_handler.execute_fetchall(
            "SELECT * from qiita.qiita_user WHERE email LIKE "
            "'%somebody@foo.bar%'")
        self.assertEqual(obs, [])

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
