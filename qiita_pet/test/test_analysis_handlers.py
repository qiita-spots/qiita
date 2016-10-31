from unittest import main
from json import loads

from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_db.analysis import Analysis
from qiita_db.user import User
from qiita_db.util import get_count


class TestSelectCommandsHandler(TestHandlerBase):

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

    def test_post_other_params(self):
        post_args = {
            'rarefaction-depth': '',
            'merge-duplicated-sample-ids': 'on',
            'commands': ['16S#command']
        }
        response = self.post('/analysis/wait/1', post_args)
        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)


class TestAnalysisResultsHandler(TestHandlerBase):

    def test_get(self):
        # TODO: add proper test for this once figure out how. Issue 567
        # need to figure out biom table to test this with
        pass


class TestShowAnalysesHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/analysis/show/')
        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)


class TestSelectedSamplesHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/analysis/selected/')
        # Make sure page response loaded sucessfully
        self.assertEqual(response.code, 200)


class TestShareAnalysisAjax(TestHandlerBase):

    def test_get_deselected(self):
        a = Analysis(1)
        u = User('shared@foo.bar')
        args = {'deselected': u.id, 'id': a.id}
        self.assertEqual(a.shared_with, [u])
        response = self.get('/analysis/sharing/', args)
        self.assertEqual(response.code, 200)
        exp = {'users': [], 'links': ''}
        self.assertEqual(loads(response.body), exp)
        self.assertEqual(a.shared_with, [])

        # Make sure unshared message added to the system
        self.assertEqual('Analysis \'SomeAnalysis\' has been unshared from '
                         'you.', u.messages()[0][1])
        # Share the analysis back with the user
        a.share(u)

    def test_get_selected(self):
        s = Analysis(1)
        u = User('admin@foo.bar')
        args = {'selected': u.id, 'id': s.id}
        response = self.get('/analysis/sharing/', args)
        self.assertEqual(response.code, 200)
        exp = {
            'users': ['shared@foo.bar', u.id],
            'links':
                ('<a target="_blank" href="mailto:shared@foo.bar">Shared</a>, '
                 '<a target="_blank" href="mailto:admin@foo.bar">Admin</a>')}
        self.assertEqual(loads(response.body), exp)
        self.assertEqual(s.shared_with, [User('shared@foo.bar'), u])

        # Make sure shared message added to the system
        self.assertEqual('Analysis <a href="/analysis/results/1">'
                         '\'SomeAnalysis\'</a> has been shared with you.',
                         u.messages()[0][1])

    def test_get_no_access(self):
        s = Analysis(2)
        u = User('admin@foo.bar')
        args = {'selected': u.id, 'id': 2}
        response = self.get('/analysis/sharing/', args)
        self.assertEqual(response.code, 403)
        self.assertEqual(s.shared_with, [])


if __name__ == "__main__":
    main()
