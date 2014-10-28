from unittest import TestCase, main

from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.exceptions import QiitaDBExecutionError
from qiita_core.util import qiita_test_checker


@qiita_test_checker()
class TestConnHandler(TestCase):
    def test_create_queue(self):
        self.conn_handler.create_queue("toy_queue")
        self.assertEqual(self.conn_handler.list_queues(), ["toy_queue"])

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
        self.conn_handler.execute_queue("toy_queue")
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
if __name__ == "__main__":
    main()
