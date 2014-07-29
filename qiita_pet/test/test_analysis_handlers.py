from unittest import main

import mox

from tornado_test_base import TestHandlerBase


class TestAnalysisHandlersDB(TestHandlerBase):
    """Testing all analysis pages/functions that change the database"""
    database = True

    def test_create_analysis(self):
        self.mox.ReplayAll()
        response = self.post('/analysis/2', {'name': 'Web test Analysis',
                                             'description': 'For testing',
                                             'action': 'create'})

        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)
        self.assertTrue("/analysis/2" in response.effective_url)

        # Make sure analysis put into database
        sql = ("SELECT analysis_id FROM qiita.analysis WHERE name = "
               "'Web test Analysis' AND description = 'For testing'")
        self.assertEqual(self.conn_handler.execute_fetchone(sql)[0], 3)
        self.mox.VerifyAll()


class TestAnalysisHandlersNODB(TestHandlerBase):
    """Testing all analysis pages/functions that query the database"""
    def test_search_studies(self):
        self.mox.ReplayAll()
        post_args = {
            'analysis-id': 1,
            'action': 'search',
            'query':
                '(sample_type = ENVO:soil AND COMMON_NAME = "rhizosphere '
                'metagenome") AND NOT Description_duplicate includes Burmese'}

        response = self.post('/analysis/2', post_args)

        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)
        # make sure we have proper samples being pulled out
        self.mox.VerifyAll()

if __name__ == "__main__":
    main()
