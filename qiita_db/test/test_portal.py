from unittest import TestCase, main

import numpy.testing as npt

from qiita_core.util import qiita_test_checker
from qiita_core.qiita_settings import qiita_config
import qiita_db as qdb


@qiita_test_checker()
class TestPortal(TestCase):
    def setUp(self):
        self.portal = qiita_config.portal
        self.study = qdb.study.Study(1)
        self.analysis = qdb.analysis.Analysis(1)
        self.qiita_portal = qdb.portal.Portal('QIITA')
        self.emp_portal = qdb.portal.Portal('EMP')

    def tearDown(self):
        qiita_config.portal = self.portal

    def test_list_portals(self):
        obs = qdb.portal.Portal.list_portals()
        exp = ['EMP']
        self.assertEqual(obs, exp)

    def test_add_portal(self):
        obs = qdb.portal.Portal.create("NEWPORTAL", "SOMEDESC")
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

        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateError):
            qdb.portal.Portal.create("EMP", "DOESNTMATTERFORDESC")

        qdb.portal.Portal.delete('NEWPORTAL')

    def test_remove_portal(self):
        qdb.portal.Portal.create("NEWPORTAL", "SOMEDESC")
        # Select some samples on a default analysis
        qiita_config.portal = "NEWPORTAL"
        a = qdb.user.User("test@foo.bar").default_analysis
        a.add_samples({1: ['1.SKB8.640193', '1.SKD5.640186']})

        qdb.portal.Portal.delete("NEWPORTAL")
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

        with self.assertRaises(qdb.exceptions.QiitaDBLookupError):
            qdb.portal.Portal.delete("NOEXISTPORTAL")
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.portal.Portal.delete("QIITA")

        qdb.portal.Portal.create("NEWPORTAL2", "SOMEDESC")
        # Add analysis to this new portal and make sure error raised
        qiita_config.portal = "NEWPORTAL2"
        qdb.analysis.Analysis.create(
            qdb.user.User("test@foo.bar"), "newportal analysis", "desc")
        qiita_config.portal = "QIITA"
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.portal.Portal.delete("NEWPORTAL2")

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
            "emp_person_id": qdb.study.StudyPerson(2),
            "principal_investigator_id": qdb.study.StudyPerson(3),
            "lab_person_id": qdb.study.StudyPerson(1)
        }
        qdb.portal.Portal.create("NEWPORTAL3", "SOMEDESC")
        qiita_config.portal = "NEWPORTAL3"
        qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "Fried chicken microbiome",
            [1], info)
        qiita_config.portal = "QIITA"
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.portal.Portal.delete("NEWPORTAL3")

    def test_check_studies(self):
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            self.qiita_portal._check_studies([2000000000000, 122222222222222])

    def test_check_analyses(self):
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            self.qiita_portal._check_analyses([2000000000000, 122222222222222])

        with self.assertRaises(qdb.exceptions.QiitaDBError):
            self.qiita_portal._check_analyses([8, 9])

    def test_get_studies_by_portal(self):
        obs = self.emp_portal.get_studies()
        self.assertEqual(obs, set())

        obs = self.qiita_portal.get_studies()
        self.assertEqual(obs, {qdb.study.Study(1)})

    def test_add_study_portals(self):
        obs = qdb.portal.Portal.create("NEWPORTAL4", "SOMEDESC")
        obs.add_studies([self.study.id])
        self.assertItemsEqual(self.study._portals, ['NEWPORTAL4', 'QIITA'])

        npt.assert_warns(qdb.exceptions.QiitaDBWarning, obs.add_studies,
                         [self.study.id])

        obs.remove_studies([self.study.id])
        qdb.portal.Portal.delete("NEWPORTAL4")

    def test_remove_study_portals(self):
        with self.assertRaises(ValueError):
            self.qiita_portal.remove_studies([self.study.id])

        self.emp_portal.add_studies([1])
        # Set up the analysis in EMP portal
        self.emp_portal.add_analyses([self.analysis.id])
        obs = self.analysis._portals
        self.assertItemsEqual(obs, ['QIITA', 'EMP'])

        # Test study removal failure
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            self.emp_portal.remove_studies([self.study.id])
        obs = self.study._portals
        self.assertItemsEqual(obs, ['QIITA', 'EMP'])

        # Test study removal
        self.emp_portal.remove_analyses([self.analysis.id])
        self.emp_portal.remove_studies([self.study.id])
        obs = self.study._portals
        self.assertEqual(obs, ['QIITA'])

        obs = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning, self.emp_portal.remove_studies,
            [self.study.id])

    def test_get_analyses_by_portal(self):
        qiita_config.portal = 'EMP'
        exp = {qdb.analysis.Analysis(7), qdb.analysis.Analysis(8),
               qdb.analysis.Analysis(9), qdb.analysis.Analysis(10)}
        obs = self.emp_portal.get_analyses()
        self.assertEqual(obs, exp)

        qiita_config.portal = 'QIITA'
        exp = {qdb.analysis.Analysis(1), qdb.analysis.Analysis(2),
               qdb.analysis.Analysis(3), qdb.analysis.Analysis(4),
               qdb.analysis.Analysis(5), qdb.analysis.Analysis(6)}
        obs = self.qiita_portal.get_analyses()
        self.assertEqual(obs, exp)

    def test_add_analysis_portals(self):
        obs = self.analysis._portals
        self.assertEqual(obs, ['QIITA'])
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            self.emp_portal.add_analyses([self.analysis.id])
        obs = self.analysis._portals
        self.assertEqual(obs, ['QIITA'])

        self.emp_portal.add_studies([1])
        self.emp_portal.add_analyses([self.analysis.id])
        obs = self.analysis._portals
        self.assertEqual(obs, ['EMP', 'QIITA'])

        npt.assert_warns(
            qdb.exceptions.QiitaDBWarning, self.emp_portal.add_analyses,
            [self.analysis.id])

        self.emp_portal.remove_analyses([self.analysis.id])
        self.emp_portal.remove_studies([1])

    def test_remove_analysis_portals(self):
        with self.assertRaises(ValueError):
            self.qiita_portal.remove_analyses([self.analysis.id])

        # set up the analysis in EMP portal
        self.emp_portal.add_studies([1])
        self.emp_portal.add_analyses([self.analysis.id])
        obs = self.analysis._portals
        self.assertItemsEqual(obs, ['QIITA', 'EMP'])
        # Test removal
        self.emp_portal.remove_analyses([self.analysis.id])
        obs = self.analysis._portals
        self.assertEqual(obs, ['QIITA'])

        obs = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning, self.emp_portal.remove_analyses,
            [self.analysis.id])

        self.emp_portal.remove_studies([1])


if __name__ == '__main__':
    main()
