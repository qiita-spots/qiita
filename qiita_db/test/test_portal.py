from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_db.portal import (
    add_studies_to_portal, remove_studies_from_portal, get_studies_by_portal,
    add_analyses_to_portal, remove_analyses_from_portal,
    get_analyses_by_portal)
from qiita_db.study import Study
from qiita_db.analysis import Analysis
from qiita_core.qiita_settings import qiita_config

# Only test if functions available
if qiita_config.portal == "QIITA":
    @qiita_test_checker()
    class TestPortal(TestCase):
        def setUp(self):
            self.study = Study(1)
            self.analysis = Analysis(1)

        def tearDown(self):
            qiita_config.portal = 'QIITA'

        def test_get_studies_by_portal(self):
            obs = get_studies_by_portal('EMP')
            self.assertEqual(obs, set())

            obs = get_studies_by_portal('QIITA')
            self.assertEqual(obs, {1})

        def test_add_study_portals(self):
            add_studies_to_portal('EMP', [self.study.id])
            obs = self.study._portals
            self.assertEqual(obs, ['EMP', 'QIITA'])

        def test_remove_study_portals(self):
            with self.assertRaises(ValueError):
                remove_studies_from_portal('QIITA', [self.study.id])

            add_studies_to_portal('EMP', [self.study.id])
            remove_studies_from_portal('EMP', [self.study.id])
            obs = self.study._portals
            self.assertEqual(obs, ['QIITA'])

        def test_get_analyses_by_portal(self):
            obs = get_analyses_by_portal('EMP')
            self.assertEqual(obs, set())

            obs = get_analyses_by_portal('QIITA')
            self.assertEqual(obs, set(x for x in range(1, 11)))

        def test_add_study_portals(self):
            add_analyses_to_portal('EMP', [self.analysis.id])
            obs = self.analysis._portals
            self.assertEqual(obs, ['EMP', 'QIITA'])

        def test_remove_analysis_portals(self):
            with self.assertRaises(ValueError):
                remove_analyses_from_portal('QIITA', [self.analysis.id])

            add_analyses_to_portal('EMP', [self.analysis.id])
            remove_analyses_from_portal('EMP', [self.analysis.id])
            obs = self.analysis._portals
            self.assertEqual(obs, ['QIITA'])


if __name__ == '__main__':
    main()
