from unittest import TestCase, main

import numpy.testing as npt

from qiita_core.util import qiita_test_checker
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.portal import Portal
from qiita_db.study import Study, StudyPerson
from qiita_db.user import User
from qiita_db.analysis import Analysis
from qiita_db.exceptions import (QiitaDBError, QiitaDBDuplicateError,
                                 QiitaDBWarning)
from qiita_core.qiita_settings import qiita_config


@qiita_test_checker()
class TestPortal(TestCase):
    portal = qiita_config.portal

    def setUp(self):
        self.study = Study(1)
        self.analysis = Analysis(1)
        self.qiita_portal = Portal('QIITA')
        self.emp_portal = Portal('EMP')

    def tearDown(self):
        qiita_config.portal = self.portal

    def test_list_portals(self):
        obs = Portal.list_portals()
        exp = ['EMP']
        self.assertEqual(obs, exp)

    def test_add_portal(self):
        Portal.create("NEWPORTAL", "SOMEDESC")
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.portal_type")
        exp = [[1, 'QIITA', 'QIITA portal. Access to all data stored '
                'in database.'],
               [2, 'EMP', 'EMP portal'],
               [4, 'NEWPORTAL', 'SOMEDESC']]
        self.assertItemsEqual(obs, exp)

        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.analysis_portal")
        exp = [[1, 1], [2, 1], [3, 1], [4, 1], [5, 1], [6, 1], [7, 2], [8, 2],
               [9, 2], [10, 2], [11, 4], [12, 4], [13, 4], [14, 4]]
        self.assertItemsEqual(obs, exp)

        with self.assertRaises(QiitaDBDuplicateError):
            Portal.create("EMP", "DOESNTMATTERFORDESC")

    def test_remove_portal(self):
        Portal.create("NEWPORTAL", "SOMEDESC")
        # Select some samples on a default analysis
        a = Analysis(User("test@foo.bar").default_analysis)
        a.add_samples({1: ['1.SKB8.640193', '1.SKD5.640186']})

        Portal.delete("NEWPORTAL")
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.portal_type")
        exp = [[1, 'QIITA', 'QIITA portal. Access to all data stored '
                'in database.'],
               [2, 'EMP', 'EMP portal']]
        self.assertItemsEqual(obs, exp)

        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.analysis_portal")
        exp = [[1, 1], [2, 1], [3, 1], [4, 1], [5, 1], [6, 1], [7, 2], [8, 2],
               [9, 2], [10, 2]]
        self.assertItemsEqual(obs, exp)

        with self.assertRaises(IncompetentQiitaDeveloperError):
            Portal.delete("NOEXISTPORTAL")
        with self.assertRaises(QiitaDBError):
            Portal.delete("QIITA")

        Portal.create("NEWPORTAL2", "SOMEDESC")
        # Add analysis to this new portal and make sure error raised
        qiita_config.portal = "NEWPORTAL2"
        Analysis.create(User("test@foo.bar"), "newportal analysis", "desc")
        qiita_config.portal = "QIITA"
        with self.assertRaises(QiitaDBError):
            Portal.delete("NEWPORTAL2")

        # Add study to this new portal and make sure error raised
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "study_alias": "FCM",
            "study_description": "Microbiome of people who eat nothing but "
                                 "fried chicken",
            "study_abstract": "Exploring how a high fat diet changes the "
                              "gut microbiome",
            "emp_person_id": StudyPerson(2),
            "principal_investigator_id": StudyPerson(3),
            "lab_person_id": StudyPerson(1)
        }
        Portal.create("NEWPORTAL3", "SOMEDESC")
        qiita_config.portal = "NEWPORTAL3"
        Study.create(User('test@foo.bar'), "Fried chicken microbiome",
                     [1], info)
        qiita_config.portal = "QIITA"
        with self.assertRaises(QiitaDBError):
            Portal.delete("NEWPORTAL3")

    def test_check_studies(self):
        with self.assertRaises(QiitaDBError):
            self.qiita_portal._check_studies([2000000000000, 122222222222222])

    def test_check_analyses(self):
        with self.assertRaises(QiitaDBError):
            self.qiita_portal._check_analyses([2000000000000, 122222222222222])

        with self.assertRaises(QiitaDBError):
            self.qiita_portal._check_analyses([8, 9])

    def test_get_studies_by_portal(self):
        obs = self.emp_portal.get_studies()
        self.assertEqual(obs, set())

        obs = self.qiita_portal.get_studies()
        self.assertEqual(obs, {1})

    def test_add_study_portals(self):
        self.emp_portal.add_studies([self.study.id])
        obs = self.study._portals
        self.assertEqual(obs, ['EMP', 'QIITA'])

        obs = npt.assert_warns(
            QiitaDBWarning, self.emp_portal.add_studies, [self.study.id])

    def test_remove_study_portals(self):
        with self.assertRaises(ValueError):
            self.qiita_portal.remove_studies([self.study.id])

        self.emp_portal.add_studies([self.study.id])
        self.emp_portal.remove_studies([self.study.id])
        obs = self.study._portals
        self.assertEqual(obs, ['QIITA'])

        obs = npt.assert_warns(
            QiitaDBWarning, self.emp_portal.remove_studies, [self.study.id])

    def test_get_analyses_by_portal(self):
        obs = self.emp_portal.get_analyses()
        self.assertEqual(obs, {7, 8, 9, 10})

        obs = self.qiita_portal.get_analyses()
        self.assertEqual(obs, {1, 2, 3, 4, 5, 6})

    def test_add_analysis_portals(self):
        self.emp_portal.add_analyses([self.analysis.id])
        obs = self.analysis._portals
        self.assertEqual(obs, ['EMP', 'QIITA'])

        obs = npt.assert_warns(
            QiitaDBWarning, self.emp_portal.add_analyses, [self.analysis.id])

    def test_remove_analysis_portals(self):
        with self.assertRaises(ValueError):
            self.qiita_portal.remove_analyses([self.analysis.id])

        self.emp_portal.add_analyses([self.analysis.id])
        self.emp_portal.remove_analyses([self.analysis.id])
        obs = self.analysis._portals
        self.assertEqual(obs, ['QIITA'])

        obs = npt.assert_warns(
            QiitaDBWarning, self.emp_portal.remove_analyses,
            [self.analysis.id])


if __name__ == '__main__':
    main()
