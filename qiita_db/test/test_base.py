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
from qiita_core.qiita_settings import qiita_config
import qiita_db as qdb


@qiita_test_checker()
class QiitaBaseTest(TestCase):
    """Tests that the base class functions act correctly"""

    def setUp(self):
        # We need an actual subclass in order to test the equality functions
        self.tester = qdb.artifact.Artifact(1)
        self.portal = qiita_config.portal

    def tearDown(self):
        qiita_config.portal = self.portal

    def test_init_base_error(self):
        """Raises an error when instantiating a base class directly"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            qdb.base.QiitaObject(1)

    def test_init_error_inexistent(self):
        """Raises an error when instantiating an object that does not exists"""
        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.artifact.Artifact(10)

    def test_check_subclass(self):
        """Nothing happens if check_subclass called from a subclass"""
        self.tester._check_subclass()

    def test_check_subclass_error(self):
        """check_subclass raises an error if called from a base class"""
        # Checked through the __init__ call
        with self.assertRaises(IncompetentQiitaDeveloperError):
            qdb.base.QiitaObject(1)
        with self.assertRaises(IncompetentQiitaDeveloperError):
            qdb.base.QiitaStatusObject(1)

    def test_check_id(self):
        """Correctly checks if an id exists on the database"""
        self.assertTrue(self.tester._check_id(1))
        self.assertFalse(self.tester._check_id(100))

    def test_check_portal(self):
        """Correctly checks if object is accessable in portal given"""
        qiita_config.portal = 'QIITA'
        tester = qdb.analysis.Analysis(1)
        self.assertTrue(tester._check_portal(1))
        qiita_config.portal = 'EMP'
        self.assertFalse(tester._check_portal(1))

        self.assertTrue(self.tester._check_portal(1))

    def test_equal_self(self):
        """Equality works with the same object"""
        self.assertEqual(self.tester, self.tester)

    def test_equal(self):
        """Equality works with two objects pointing to the same instance"""
        new = qdb.artifact.Artifact(1)
        self.assertEqual(self.tester, new)

    def test_not_equal(self):
        """Not equals works with object of the same type"""
        sp1 = qdb.study.StudyPerson(1)
        sp2 = qdb.study.StudyPerson(2)
        self.assertNotEqual(sp1, sp2)

    def test_not_equal_type(self):
        """Not equals works with object of different type"""
        new = qdb.study.Study(1)
        self.assertNotEqual(self.tester, new)


@qiita_test_checker()
class QiitaStatusObjectTest(TestCase):
    """Tests that the QittaStatusObject class functions act correctly"""

    def setUp(self):
        # We need an actual subclass in order to test the equality functions
        self.tester = qdb.analysis.Analysis(1)

    def test_status(self):
        """Correctly returns the status of the object"""
        self.assertEqual(self.tester.status, "in_construction")

    def test_check_status_single(self):
        """check_status works passing a single status"""
        self.assertTrue(self.tester.check_status(["in_construction"]))
        self.assertFalse(self.tester.check_status(["queued"]))

    def test_check_status_exclude_single(self):
        """check_status works passing a single status and the exclude flag"""
        self.assertTrue(self.tester.check_status(["public"], exclude=True))
        self.assertFalse(self.tester.check_status(["in_construction"],
                         exclude=True))

    def test_check_status_list(self):
        """check_status work passing a list of status"""
        self.assertTrue(self.tester.check_status(
            ["in_construction", "queued"]))
        self.assertFalse(self.tester.check_status(
            ["public", "queued"]))

    def test_check_status_exclude_list(self):
        """check_status work passing a list of status and the exclude flag"""
        self.assertTrue(self.tester.check_status(
            ["public", "queued"], exclude=True))
        self.assertFalse(self.tester.check_status(
            ["in_construction", "queued"], exclude=True))

    def test_check_status_unknown_status(self):
        """check_status raises an error if an invalid status is provided"""
        with self.assertRaises(ValueError):
            self.tester.check_status(["foo"])

        with self.assertRaises(ValueError):
            self.tester.check_status(["foo"], exclude=True)

    def test_check_status_unknown_status_list(self):
        """check_status raises an error if an invalid status list is provided
        """
        with self.assertRaises(ValueError):
            self.tester.check_status(["foo", "bar"])

        with self.assertRaises(ValueError):
            self.tester.check_status(["foo", "bar"], exclude=True)

if __name__ == '__main__':
    main()
