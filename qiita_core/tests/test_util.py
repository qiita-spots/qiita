from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import (
    send_email, qiita_test_checker, execute_as_transaction, get_qiita_version,
    is_test_environment)
import qiita_db as qdb


class UtilTests(TestCase):
    def test_send_email(self):
        # TODO: issue 1639
        # figure out how to test sending emails
        pass

    def test_send_email_fail(self):
        """testing send email functionality"""
        # the default configuration is not correct and should fail
        with self.assertRaises(IOError):
            send_email("antgonza@gmail.com", "This is a test",
                       "This is the body of the test")

    def test_is_test_environment(self):
        self.assertTrue(is_test_environment())

    def test_qiita_test_checker(self):
        """testing qiita test checker"""
        @qiita_test_checker()
        class test_class:
            pass

    def test_qiita_test_checker_fail(self):
        """testing qiita test checker fail"""
        with self.assertRaises(RuntimeError):
            @qiita_test_checker(test=True)
            class test_class_fail:
                pass

    def test_execute_as_transaction(self):
        """testing that execute as transaction returns 2 different wrappers"""
        @execute_as_transaction
        def function():
            # retrieve transaction id
            with qdb.sql_connection.TRN:
                sql = "SELECT txid_current();"
                qdb.sql_connection.TRN.add(sql)
                return qdb.sql_connection.TRN.execute_fetchlast()

        f1 = function()
        f2 = function()
        self.assertNotEqual(f1, f2)

    def test_get_qiita_version(self):
        exp_version, exp_sha = get_qiita_version()
        # testing just the version
        self.assertEqual(exp_version, qdb.__version__)


if __name__ == '__main__':
    main()
