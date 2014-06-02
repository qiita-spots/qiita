# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_db.base import QiitaStatusObject, QiitaObject
from qiita_db.exceptions import QiitaDBStatusError


class QiitaBaseTest(TestCase):
    """Tests that the base class functions act correctly"""

    def setUp(self):
        self.tester = QiitaObject(1)

    def test_equal_self(self):
        self.assertEqual(self.tester, self.tester)

    def test_equal(self):
        new = QiitaObject(1)
        self.assertEqual(self.tester, new)

    def test_not_equal(self):
        new = QiitaObject(3)
        self.assertNotEqual(self.tester, new)

    def test_not_equal_type(self):
        new = QiitaStatusObject(1)
        self.assertNotEqual(self.tester, new)


@qiita_test_checker()
class QiitaStatusDecoratorTest(TestCase):
    """Tests that the status decorator works correctly"""

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
        @self.tester.check_status("waiting_approval")
        def tf(string):
            return string
        with self.assertRaises(QiitaDBStatusError):
            tf("FAIL")

    def test_check_status_exclude_stops_run_single(self):
        @self.tester.check_status("public", exclude=True)
        def tf(string):
            return string
        with self.assertRaises(QiitaDBStatusError):
            tf("FAIL")

    def test_check_status_stops_run_list(self):
        @self.tester.check_status(("waiting_approval", "private"))
        def tf(string):
            return string
        with self.assertRaises(QiitaDBStatusError):
            tf("FAIL")

    def test_check_status_exclude_stops_run_list(self):
        @self.tester.check_status(("public", "private"), exclude=True)
        def tf(string):
            return string
        with self.assertRaises(QiitaDBStatusError):
            tf("FAIL")

    def test_check_status_unknown_status(self):
        @self.tester.check_status("football")
        def tf(string):
            return string
        with self.assertRaises(ValueError):
            tf("FAIL")

if __name__ == '__main__':
    main()
