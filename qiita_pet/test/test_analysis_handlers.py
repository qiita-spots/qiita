from unittest import main
from tornado_test_base import TestHandlerBase
from qiita_db.analysis import Analysis
from qiita_db.user import User

from analysis_handlers import (
    check_analysis_access, SearchStudiesHandler, SelectCommandsHandler,
    AnalysisWaitHandler, AnalysisResultsHandler, ShowAnalysesHandler)


class TestSearchStudiesHandler(TestHandlerBase):
    database = True

    def test_parse_search_results(self):
        raise NotImplementedError()

    def test__selected_parser(self):
        raise NotImplementedError()

    def test__parse_form_select(self):
        raise NotImplementedError()

    def test__parse_form_deselect(self):
        raise NotImplementedError()

    def test_get_existing_selected(self):
        response = self.get('/analysis/2?aid=1')
        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)
        # make sure we have proper samples being pulled out
        self.assertTrue("SKB8.640193" in str(response.body))

    def test_post_search_no_results(self):
        post_args = {
            'analysis-id': 1,
            'action': 'search',
            'query': 'sample_type = unicorns_and_rainbows'}

        response = self.post('/analysis/2', post_args)

        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)
        # make sure we have proper error message
        self.assertTrue("No results found." in str(response.body))

    def test_post_malformed_search(self):
        post_args = {
            'analysis-id': 1,
            'action': 'search',
            'query': '(sample_type ='}

        response = self.post('/analysis/2', post_args)

        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)
        # make sure we have proper error message
        self.assertTrue("Malformed search query, please read search help."
                        in str(response.body))

    def test_post_search_studies(self):
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

    def test_post_deselect_samples(self):
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
        self.assertTrue("SKB8.640193" not in str(response.body))

    def test_post_create_analysis(self):
        response = self.post('/analysis/2', {'name': 'Web test Analysis',
                                             'description': 'For testing',
                                             'action': 'create'})

        # Make sure page response loaded sucessfully and went to proper place
        self.assertEqual(response.code, 200)
        self.assertTrue("/analysis/2" in response.effective_url)
        # pull analysis_id out from page and instantiate to maeke sure exists

    def test_post_select_samples(self):
        newaid = Analysis.create(User("test@foo.bar"), "test1", "testdesc").id
        post_args = {
            'analysis-id': newaid,
            'action': 'select',
            'availstudies': "1#1",
            '1#1': 1,
            '1': 'SKD5.640186'}

        response = self.post('/analysis/2', post_args)

        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)
        # make sure sample added
        self.assertTrue("SKD5.640186" in str(response.body))


class TestSelectCommandsHandler(TestHandlerBase):
    database = True
    def test_get(self):
        raise NotImplementedError()

    def test_post(self):
        raise NotImplementedError()


class TestAnalysisWaitHandler(TestHandlerBase):
    database = True
    def test_get(self):
        raise NotImplementedError()

    def test_post(self):
        raise NotImplementedError()


class TestAnalysisResultsHandler(TestHandlerBase):
    database = True
    def test_get(self):
        raise NotImplementedError()


class TestShowAnalysesHandler(TestHandlerBase):
    def test_get(self):
        raise NotImplementedError()


if __name__ == "__main__":
    main()
