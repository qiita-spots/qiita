from unittest import main
from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_db.analysis import Analysis
from qiita_db.util import get_count


class TestSelectCommandsHandler(TestHandlerBase):
    database = True

    def test_get(self):
        response = self.get('/analysis/3', {'aid': 1})
        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)

    def test_post(self):
        new_aid = get_count('qiita.analysis') + 1
        post_args = {
            'name': 'post-test',
            'description': "test of posting"}
        response = self.post('/analysis/3', post_args)
        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)
        # make sure analysis created
        analysis = Analysis(new_aid)
        self.assertEqual(analysis.name, 'post-test')


class TestAnalysisWaitHandler(TestHandlerBase):
    database = True

    def test_get_exists(self):
        response = self.get('/analysis/wait/1')
        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)

    def test_get_no_exists(self):
        response = self.get('/analysis/wait/237')
        # Make sure page response loaded with 404, not 500
        self.assertEqual(response.code, 404)

    def test_post(self):
        post_args = {
            'rarefaction-depth': 100,
            'commands': ['16S#command']
        }
        response = self.post('/analysis/wait/1', post_args)
        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)


class TestAnalysisResultsHandler(TestHandlerBase):
    database = True

    def test_get(self):
        # TODO: add proper test for this once figure out how. Issue 567
        # need to figure out biom table to test this with
        pass


class TestShowAnalysesHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/analysis/show/')
        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)


if __name__ == "__main__":
    main()
