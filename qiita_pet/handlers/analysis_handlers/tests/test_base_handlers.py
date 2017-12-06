# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from json import loads, dumps

from tornado.web import HTTPError
from mock import Mock

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_core.util import qiita_test_checker
from qiita_core.qiita_settings import r_client
from qiita_core.testing import wait_for_processing_job
from qiita_db.user import User
from qiita_db.analysis import Analysis
from qiita_db.software import Command, Parameters, DefaultParameters
from qiita_db.processing_job import ProcessingWorkflow
from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_pet.handlers.analysis_handlers.base_handlers import (
    analyisis_graph_handler_get_request,
    analysis_description_handler_get_request)


@qiita_test_checker()
class TestBaseHandlersUtils(TestCase):
    def tearDown(self):
        r_client.flushdb()

    def test_analysis_description_handler_get_request(self):
        obs = analysis_description_handler_get_request(1, User('test@foo.bar'))
        exp = {'analysis_name': 'SomeAnalysis',
               'analysis_id': 1,
               'analysis_description': 'A test analysis',
               'analysis_mapping_id': 16,
               'analysis_is_public': False,
               'alert_type': 'info',
               'alert_msg': ''}
        self.assertEqual(obs, exp)

        r_client.set('analysis_1', dumps({'job_id': 'job_id'}))
        r_client.set('job_id', dumps({'status_msg': 'running'}))
        obs = analysis_description_handler_get_request(1, User('test@foo.bar'))
        exp = {'analysis_name': 'SomeAnalysis',
               'analysis_id': 1,
               'analysis_description': 'A test analysis',
               'analysis_mapping_id': 16,
               'analysis_is_public': False,
               'alert_type': 'info',
               'alert_msg': 'An artifact is being deleted from this analysis'}
        self.assertEqual(obs, exp)

        r_client.set('job_id', dumps(
            {'status_msg': 'Success',
             'return': {'status': 'danger',
                        'message': 'Error deleting artifact'}}))
        obs = analysis_description_handler_get_request(1, User('test@foo.bar'))
        exp = {'analysis_name': 'SomeAnalysis',
               'analysis_id': 1,
               'analysis_description': 'A test analysis',
               'analysis_mapping_id': 16,
               'analysis_is_public': False,
               'alert_type': 'danger',
               'alert_msg': 'Error deleting artifact'}
        self.assertEqual(obs, exp)

    def test_analyisis_graph_handler_get_request(self):
        obs = analyisis_graph_handler_get_request(1, User('test@foo.bar'))
        # The job id is randomly generated in the test environment. Gather
        # it here. There is only 1 job in the first artifact of the analysis
        job_id = Analysis(1).artifacts[0].jobs()[0].id
        exp = {'edges': [(8, job_id), (job_id, 9)],
               'nodes': [
                    ('job', 'job', job_id, 'Single Rarefaction', 'success'),
                    ('artifact', 'BIOM', 9, 'noname\n(BIOM)', 'artifact'),
                    ('artifact', 'BIOM',   8, 'noname\n(BIOM)', 'artifact')],
               'workflow': None}
        self.assertItemsEqual(obs, exp)
        self.assertItemsEqual(obs['edges'], exp['edges'])
        self.assertItemsEqual(obs['nodes'], exp['nodes'])
        self.assertIsNone(obs['workflow'])

        # An admin has full access to the analysis
        obs = analyisis_graph_handler_get_request(1, User('admin@foo.bar'))
        self.assertItemsEqual(obs, exp)
        self.assertItemsEqual(obs['edges'], exp['edges'])
        self.assertItemsEqual(obs['nodes'], exp['nodes'])

        # If the analysis is shared with the user he also has access
        obs = analyisis_graph_handler_get_request(1, User('shared@foo.bar'))
        self.assertItemsEqual(obs, exp)
        self.assertItemsEqual(obs['edges'], exp['edges'])
        self.assertItemsEqual(obs['nodes'], exp['nodes'])

        # The user doesn't have access to the analysis
        with self.assertRaises(HTTPError):
            analyisis_graph_handler_get_request(1, User('demo@microbio.me'))


class TestBaseHandlers(TestHandlerBase):
    def test_post_create_analysis_handler(self):
        user = User('test@foo.bar')
        dflt_analysis = user.default_analysis
        dflt_analysis.add_samples(
            {4: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196',
                 '1.SKM9.640192', '1.SKM4.640180']})
        args = {'name': 'New Test Analysis',
                'description': 'Test Analysis Description'}
        response = self.post('/analysis/create/', args)
        self.assertRegexpMatches(
            response.effective_url,
            r"http://localhost:\d+/analysis/description/\d+/")
        self.assertEqual(response.code, 200)

        # The new analysis id is located at the -2 position (see regex above)
        new_id = response.effective_url.split('/')[-2]
        a = Analysis(new_id)
        # Make sure that all jobs have completed before we exit this tests
        for j in a.jobs:
            wait_for_processing_job(j.id)

    def test_get_analysis_description_handler(self):
        response = self.get('/analysis/description/1/')
        self.assertEqual(response.code, 200)

    def test_post_analysis_description_handler(self):
        response = self.post('/analysis/description/1/', {})
        self.assertEqual(response.code, 200)

    def test_get_analysis_jobs_handler(self):
        user = User('test@foo.bar')
        dflt_analysis = user.default_analysis
        dflt_analysis.add_samples(
            {4: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196',
                 '1.SKM9.640192', '1.SKM4.640180']})
        new = Analysis.create(user, "newAnalysis", "A New Analysis",
                              from_default=True)
        response = self.get('/analysis/description/%s/jobs/' % new.id)
        self.assertEqual(response.code, 200)

        # There is only one job
        job_id = new.jobs[0].id
        obs = loads(response.body)
        exp = {job_id: {'status': 'queued', 'step': None, 'error': ""}}
        self.assertEqual(obs, exp)


class TestAnalysisGraphHandler(TestHandlerBase):
    def test_get_analysis_graph_handler(self):
        response = self.get('/analysis/description/1/graph/')
        self.assertEqual(response.code, 200)
        # The job id is randomly generated in the test environment. Gather
        # it here. There is only 1 job in the first artifact of the analysis
        job_id = Analysis(1).artifacts[0].jobs()[0].id
        obs = loads(response.body)
        exp = {'edges': [[8, job_id], [job_id, 9]],
               'nodes': [
                    ['job', 'job', job_id, 'Single Rarefaction', 'success'],
                    ['artifact', 'BIOM', 9, 'noname\n(BIOM)', 'artifact'],
                    ['artifact', 'BIOM', 8, 'noname\n(BIOM)', 'artifact']],
               'workflow': None}
        self.assertItemsEqual(obs, exp)
        self.assertItemsEqual(obs['edges'], exp['edges'])
        self.assertItemsEqual(obs['nodes'], exp['nodes'])
        self.assertIsNone(obs['workflow'])

        # Create a new analysis with 2 starting BIOMs to be able to test
        # the different if statements of the request
        BaseHandler.get_current_user = Mock(
            return_value=User('shared@foo.bar'))
        user = User('shared@foo.bar')
        dflt_analysis = user.default_analysis
        dflt_analysis.add_samples(
            {4: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196'],
             6: ['1.SKB8.640193', '1.SKD8.640184', '1.SKB7.640196']})
        args = {'name': 'New Test Graph Analysis', 'description': 'Desc'}
        response = self.post('/analysis/create/', args)
        new_id = response.effective_url.split('/')[-2]
        a = Analysis(new_id)
        # Wait until all the jobs are done so the BIOM tables exist
        for j in a.jobs:
            wait_for_processing_job(j.id)

        artifacts = a.artifacts
        self.assertEqual(len(artifacts), 2)

        # Create a new workflow starting on the first artifact
        # Magic number 9 -> Summarize Taxa command
        params = Parameters.load(
            Command(9), values_dict={'metadata_category': 'None',
                                     'sort': 'False',
                                     'biom_table': artifacts[0].id})
        wf = ProcessingWorkflow.from_scratch(user, params)

        # There is only one job in the workflow
        job_id = wf.graph.nodes()[0].id

        response = self.get('/analysis/description/%s/graph/' % new_id)
        self.assertEqual(response.code, 200)
        obs = loads(response.body)
        exp = {'edges': [[artifacts[0].id, job_id],
                         [job_id, '%s:taxa_summary' % job_id]],
               'nodes': [
                    ['job', 'job', job_id, 'Summarize Taxa',
                     'in_construction'],
                    ['artifact', 'BIOM', artifacts[0].id, 'noname\n(BIOM)',
                     'artifact'],
                    ['artifact', 'BIOM', artifacts[1].id, 'noname\n(BIOM)',
                     'artifact'],
                    ['type', 'taxa_summary', '%s:taxa_summary' % job_id,
                     'taxa_summary\n(taxa_summary)', 'type']],
               'workflow': wf.id}
        # Check that the keys are the same
        self.assertItemsEqual(obs, exp)
        # Check the edges
        self.assertItemsEqual(obs['edges'], exp['edges'])
        # Check the edges
        self.assertItemsEqual(obs['nodes'], exp['nodes'])
        # Check the edges
        self.assertEqual(obs['workflow'], exp['workflow'])

        # Add a job to the second BIOM to make sure that the edes and nodes
        # are respected. Magic number 12 -> Single Rarefaction
        job2 = wf.add(
            DefaultParameters(16), req_params={'depth': '100',
                                               'biom_table': artifacts[1].id})
        job_id_2 = job2.id

        response = self.get('/analysis/description/%s/graph/' % new_id)
        self.assertEqual(response.code, 200)
        obs = loads(response.body)
        exp = {'edges': [[artifacts[0].id, job_id],
                         [job_id, '%s:taxa_summary' % job_id],
                         [artifacts[1].id, job_id_2],
                         [job_id_2, '%s:rarefied_table' % job_id_2]],
               'nodes': [
                    ['job', 'job', job_id, 'Summarize Taxa',
                     'in_construction'],
                    ['job', 'job', job_id_2, 'Single Rarefaction',
                     'in_construction'],
                    ['artifact', 'BIOM', artifacts[0].id, 'noname\n(BIOM)',
                     'artifact'],
                    ['artifact', 'BIOM', artifacts[1].id, 'noname\n(BIOM)',
                     'artifact'],
                    ['type', 'taxa_summary', '%s:taxa_summary' % job_id,
                     'taxa_summary\n(taxa_summary)', 'type'],
                    ['type', 'BIOM', '%s:rarefied_table' % job_id_2,
                     'rarefied_table\n(BIOM)', 'type']],
               'workflow': wf.id}
        # Check that the keys are the same
        self.assertItemsEqual(obs, exp)
        # Check the edges
        self.assertItemsEqual(obs['edges'], exp['edges'])
        # Check the edges
        self.assertItemsEqual(obs['nodes'], exp['nodes'])
        # Check the edges
        self.assertEqual(obs['workflow'], exp['workflow'])

        # Add a second Workflow to the second artifact to force the raise of
        # the error. This situation should never happen when using
        # the interface
        params = Parameters.load(
            Command(9), values_dict={'metadata_category': 'None',
                                     'sort': 'False',
                                     'biom_table': artifacts[1].id})
        wf = ProcessingWorkflow.from_scratch(user, params)
        response = self.get('/analysis/description/%s/graph/' % new_id)
        self.assertEqual(response.code, 500)


if __name__ == '__main__':
    main()
