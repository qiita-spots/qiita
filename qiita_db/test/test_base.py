# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.util import qiita_test_checker
from qiita_db.base import QiitaObject, QiitaStatusObject
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.data import RawData
from qiita_db.study import Study
from qiita_db.analysis import Analysis


@qiita_test_checker()
class QiitaBaseTest(TestCase):
    """Tests that the base class functions act correctly"""

    def setUp(self):
        # We need an actual subclass in order to test the equality functions
        self.tester = RawData(1)

    def test_init_base_error(self):
        """Raises an error when instantiating a base class directly"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            QiitaObject(1)

    def test_init_error_inexistent(self):
        """Raises an error when instantiating an object that does not exists"""
        with self.assertRaises(QiitaDBUnknownIDError):
            RawData(10)

    def test_check_subclass(self):
        """Nothing happens if check_subclass called from a subclass"""
        self.tester._check_subclass()

    def test_check_subclass_error(self):
        """check_subclass raises an error if called from a base class"""
        # Checked through the __init__ call
        with self.assertRaises(IncompetentQiitaDeveloperError):
            QiitaObject(1)
        with self.assertRaises(IncompetentQiitaDeveloperError):
            QiitaStatusObject(1)

    def test_check_id(self):
        """Correctly checks if an id exists on the database"""
        self.assertTrue(self.tester._check_id(1))
        self.assertFalse(self.tester._check_id(100))

    def test_equal_self(self):
        """Equality works with the same object"""
        self.assertEqual(self.tester, self.tester)

    def test_equal(self):
        """Equality works with two objects pointing to the same instance"""
        new = RawData(1)
        self.assertEqual(self.tester, new)

    def test_not_equal(self):
        """Not equals works with object of the same type"""
        new = RawData(2)
        self.assertNotEqual(self.tester, new)

    def test_not_equal_type(self):
        """Not equals works with object of different type"""
        new = Study(1)
        self.assertNotEqual(self.tester, new)


@qiita_test_checker()
class QiitaStatusObjectTest(TestCase):
    """Tests that the QittaStatusObject class functions act correctly"""

    def setUp(self):
        # We need an actual subclass in order to test the equality functions
        self.tester = Analysis(1)

    def test_status(self):
        """Correctly returns the status of the object"""
        self.assertEqual(self.tester.status, "in_construction")

    def test_check_status_single(self):
        """check_status works passing a single status"""
        self.assertTrue(self.tester.check_status(["in_construction"]))
        self.assertTrue(self.tester.check_status(["in_construction"],
                        conn_handler=self.conn_handler))
        self.assertFalse(self.tester.check_status(["queued"]))
        self.assertFalse(self.tester.check_status(["queued"],
                         conn_handler=self.conn_handler))

    def test_check_status_exclude_single(self):
        """check_status works passing a single status and the exclude flag"""
        self.assertTrue(self.tester.check_status(["public"], exclude=True))
        self.assertTrue(self.tester.check_status(["public"], exclude=True,
                        conn_handler=self.conn_handler))
        self.assertFalse(self.tester.check_status(["in_construction"],
                         exclude=True))
        self.assertFalse(self.tester.check_status(["in_construction"],
                         exclude=True, conn_handler=self.conn_handler))

    def test_check_status_list(self):
        """check_status work passing a list of status"""
        self.assertTrue(self.tester.check_status(
            ["in_construction", "queued"]))
        self.assertTrue(self.tester.check_status(
            ["in_construction", "queued"],
            conn_handler=self.conn_handler))
        self.assertFalse(self.tester.check_status(
            ["public", "queued"]))
        self.assertFalse(self.tester.check_status(
            ["public", "queued"], conn_handler=self.conn_handler))

    def test_check_status_exclude_list(self):
        """check_status work passing a list of status and the exclude flag"""
        self.assertTrue(self.tester.check_status(
            ["public", "queued"], exclude=True))
        self.assertTrue(self.tester.check_status(
            ["public", "queued"], exclude=True,
            conn_handler=self.conn_handler))
        self.assertFalse(self.tester.check_status(
            ["in_construction", "queued"], exclude=True))
        self.assertFalse(self.tester.check_status(
            ["in_construction", "queued"], exclude=True,
            conn_handler=self.conn_handler))

    def test_check_status_unknown_status(self):
        """check_status raises an error if an invalid status is provided"""
        with self.assertRaises(ValueError):
            self.tester.check_status(["foo"])

        with self.assertRaises(ValueError):
            self.tester.check_status(["foo"], exclude=True)

        with self.assertRaises(ValueError):
            self.tester.check_status(["foo"], conn_handler=self.conn_handler)

        with self.assertRaises(ValueError):
            self.tester.check_status(["foo"], exclude=True,
                                     conn_handler=self.conn_handler)

    def test_check_status_unknown_status_list(self):
        """check_status raises an error if an invalid status list is provided
        """
        with self.assertRaises(ValueError):
            self.tester.check_status(["foo", "bar"])

        with self.assertRaises(ValueError):
            self.tester.check_status(["foo", "bar"], exclude=True)

        with self.assertRaises(ValueError):
            self.tester.check_status(["foo", "bar"],
                                     conn_handler=self.conn_handler)

        with self.assertRaises(ValueError):
            self.tester.check_status(["foo", "bar"], exclude=True,
                                     conn_handler=self.conn_handler)

if __name__ == '__main__':
    main()
