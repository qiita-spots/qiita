from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_db.base import QiitaStatusObject


@qiita_test_checker()
class QiitaStatusDecoratorTest(TestCase):
    """Tests that the test database have been successfully populated"""

    def setUp(self):
        self.tester = QiitaStatusObject(1)
        self.tester._table = "study"

    def test_check_status_single(self):
        @self.tester.check_status("public")
        def tf(string):
            return string

        obs = tf("Ran")
        self.assertEqual(obs, "Ran")

    def test_check_status_exclude_single(self):
        @self.tester.check_status("private", exclude=True)
        def tf(string):
            return string

    def test_check_status_list(self):
        @self.tester.check_status(("public", "waiting_approval"))
        def tf(string):
            return string

        obs = tf("Ran")
        self.assertEqual(obs, "Ran")

    def test_check_status_exclude_list(self):
        @self.tester.check_status(("private", "waiting_approval"),
                                  exclude=True)
        def tf(string):
            return string


        obs = tf("Ran again")
        self.assertEqual(obs, "Ran again")

    def test_check_status_stops_run_single(self):
        with self.assertRaises(ValueError):
            @self.tester.check_status("waiting_approval")
            def tf(string):
                return string
            tf("FAIL")

    def test_check_status_exclude_stops_run_single(self):
        with self.assertRaises(ValueError):
            @self.tester.check_status("public", exclude=True)
            def tf(string):
                return string
            tf("FAIL")

    def test_check_status_stops_run_list(self):
        with self.assertRaises(ValueError):
            @self.tester.check_status(("waiting_approval", "private"))
            def tf(string):
                return string
            tf("FAIL")

    def test_check_status_exclude_stops_run_list(self):
        with self.assertRaises(ValueError):
            @self.tester.check_status(("public", "private"), exclude=True)
            def tf(string):
                return string
            tf("FAIL")

    def test_check_status_unknown_status(self):
        with self.assertRaises(ValueError):
            @self.tester.check_status("football")
            def tf(string):
                return string
            tf("FAIL")

if __name__ == '__main__':
    main()
