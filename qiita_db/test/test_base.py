from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_db.base import QiitaStatusObject


@qiita_test_checker()
class QiitaStatusDecoratorTest(TestCase):
    """Tests that the test database have been successfully populated"""

    def setUp(self):
        self.tester = QiitaStatusObject(1)
        self.tester._table = "study"

    def test_check_status(self):
        @self.tester.check_status("public")
        def tf(string):
            return string

        obs = tf("Ran")
        self.assertEqual(obs, "Ran")

    def test_check_status_not_state(self):
        @self.tester.check_status("private", not_state=True)
        def tf(string):
            return string

        obs = tf("Ran again")
        self.assertEqual(obs, "Ran again")

    def test_check_status_stops_run(self):
        with self.assertRaises(ValueError):
            @self.tester.check_status("waiting_approval")
            def testfunc1():
                return "Ran"
            testfunc1()

    def test_check_status_not_state_stops_run(self):
        @self.tester.check_status("public", not_state=True)
        def testfunc2():
            return "Ran"
        testfunc2()

    def test_check_status_unknown_status(self):
        with self.assertRaises(ValueError):
            @self.tester.check_status("football")
            def testfunc3():
                return "Ran"
            testfunc3()

if __name__ == '__main__':
    main()
