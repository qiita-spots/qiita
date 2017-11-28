# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from functools import partial
from json import dumps, loads
from collections import defaultdict
from future.utils import viewitems

from tornado.web import authenticated

from qiita_core.qiita_settings import qiita_config
from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import r_client
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import download_link_or_path
from qiita_pet.handlers.analysis_handlers import check_analysis_access
from qiita_pet.util import is_localhost
from qiita_db.util import generate_analysis_list
from qiita_db.analysis import Analysis
from qiita_db.processing_job import ProcessingJob
from qiita_db.software import Parameters
from qiita_db.reference import Reference
from qiita_db.artifact import Artifact
from qiita_db.software import Software


class ListAnalysesHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self):
        user = self.current_user
        is_local_request = is_localhost(self.request.headers['host'])

        uanalyses = user.shared_analyses | user.private_analyses
        user_analysis_ids = set([a.id for a in uanalyses])

        panalyses = Analysis.get_by_status('public')
        public_analysis_ids = set([a.id for a in panalyses])
        public_analysis_ids = public_analysis_ids - user_analysis_ids

        user_analyses = generate_analysis_list(user_analysis_ids)
        public_analyses = generate_analysis_list(public_analysis_ids, True)

        dlop = partial(download_link_or_path, is_local_request)

        messages = {'info': '', 'danger': ''}
        for analysis_id in user_analysis_ids:
            job_info = r_client.get('analysis_delete_%d' % analysis_id)
            if job_info:
                job_info = defaultdict(lambda: '', loads(job_info))
                job_id = job_info['job_id']
                job = ProcessingJob(job_id)
                job_status = job.status
                processing = job_status not in ('success', 'error')
                if processing:
                    messages['info'] += (
                        'Analysis %s is being deleted<br/>' % analysis_id)
                elif job_status == 'error':
                    messages['danger'] += (
                        job.log.msg.replace('\n', '<br/>') + '<br/>')
                else:
                    if job_info['alert_type'] not in messages:
                        messages[job_info['alert_type']] = []
                    messages[job_info['alert_type']] += (
                        job.log.msg.replace('\n', '<br/>') + '<br/>')

        self.render("list_analyses.html", user_analyses=user_analyses,
                    public_analyses=public_analyses, messages=messages,
                    dlop=dlop)

    @authenticated
    @execute_as_transaction
    def post(self):
        analysis_id = int(self.get_argument('analysis_id'))

        user = self.current_user
        check_analysis_access(user, Analysis(analysis_id))

        qiita_plugin = Software.from_name_and_version('Qiita', 'alpha')
        cmd = qiita_plugin.get_command('delete_analysis')
        params = Parameters.load(cmd, values_dict={'analysis_id': analysis_id})
        job = ProcessingJob.create(user, params, True)
        # Store the job id attaching it to the sample template id
        r_client.set('analysis_delete_%d' % analysis_id,
                     dumps({'job_id': job.id}))
        job.submit()

        self.redirect("%s/analysis/list/" % (qiita_config.portal_dir))


class AnalysisSummaryAJAX(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self):
        info = self.current_user.default_analysis.summary_data()
        self.write(dumps(info))


class SelectedSamplesHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self):
        # Format sel_data to get study IDs for the processed data
        sel_data = defaultdict(dict)
        proc_data_info = {}
        sel_samps = self.current_user.default_analysis.samples
        for aid, samples in viewitems(sel_samps):
            a = Artifact(aid)
            sel_data[a.study][aid] = samples
            # Also get processed data info
            processing_parameters = a.processing_parameters
            if processing_parameters is None:
                params = None
                algorithm = None
            else:
                cmd = processing_parameters.command
                params = processing_parameters.values
                if 'reference' in params:
                    ref = Reference(params['reference'])
                    del params['reference']

                    params['reference_name'] = ref.name
                    params['reference_version'] = ref.version
                algorithm = '%s (%s)' % (cmd.software.name, cmd.name)

            proc_data_info[aid] = {
                'processed_date': str(a.timestamp),
                'algorithm': algorithm,
                'data_type': a.data_type,
                'params': params
            }

        self.render("analysis_selected.html", sel_data=sel_data,
                    proc_info=proc_data_info)
