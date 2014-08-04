from unittest import main

from tornado_test_base import TestHandlerBase
from qiita_db.analysis import Analysis
from qiita_db.user import User


class TestAnalysisHandlersDB(TestHandlerBase):
    """Testing all analysis pages/functions that change the database"""
    database = True

    def test_create_analysis(self):
        response = self.post('/analysis/2', {'name': 'Web test Analysis',
                                             'description': 'For testing',
                                             'action': 'create'})

        # Make sure page response loaded sucessfully and went to proper place
        self.assertEqual(response.code, 200)
        self.assertTrue("/analysis/2" in response.effective_url)
        # pull analysis_id out from page and instantiate to maeke sure exists


    def test_select_samples(self):
        newaid = Analysis.create(User("test@foo.bar"), "test1", "testdesc").id
        post_args = {
            'analysis-id': newaid,
            'action': 'select',
            'availstudies': "1#18S",
            '1#18S': 1,
            '1': 'SKD5.640186'}

        response = self.post('/analysis/2', post_args)

        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)
        # make sure sample added
        self.assertTrue("SKD5.640186" in response.body)

    def test_deselect_samples(self):
        post_args = {
            'analysis-id': 1,
            'action': 'deselect',
            'selstudies': '1',
            'dt1': '1',
            'sel1': 'SKB8.640193'}

        response = self.post('/analysis/2', post_args)

        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)
        # make sure sample removed
        self.assertTrue("SKB8.640193" not in response.body)


class TestAnalysisHandlersNODB(TestHandlerBase):
    """Testing all analysis pages/functions that query the database"""
    def test_existing_selected(self):
        response = self.get('/analysis/2?aid=1')
        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)
        # make sure we have proper samples being pulled out
        self.assertTrue("SKB8.640193" in response.body)

    def test_search_studies(self):
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

    def test_search_no_results(self):
        post_args = {
            'analysis-id': 1,
            'action': 'search',
            'query': 'sample_type = unicorns_and_rainbows'}

        response = self.post('/analysis/2', post_args)

        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)
        # make sure we have proper error message
        self.assertTrue("No results found." in response.body)

    def test_malformed_search(self):
        post_args = {
            'analysis-id': 1,
            'action': 'search',
            'query': '(sample_type ='}

        response = self.post('/analysis/2', post_args)

        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)
        # make sure we have proper error message
        self.assertTrue("Malformed search query, please try again."
                        in response.body)


if __name__ == "__main__":
    main()
