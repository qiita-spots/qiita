# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from functools import partial
from json import dumps
from collections import defaultdict
from future.utils import viewitems

from tornado.web import authenticated

from qiita_core.qiita_settings import qiita_config
from qiita_core.util import execute_as_transaction
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import download_link_or_path
from qiita_pet.handlers.analysis_handlers import check_analysis_access
from qiita_pet.util import is_localhost
from qiita_db.util import retrieve_filepaths
from qiita_db.analysis import Analysis
from qiita_db.logger import LogEntry
from qiita_db.reference import Reference
from qiita_db.artifact import Artifact


class ListAnalysesHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self):
        message = self.get_argument('message', '')
        level = self.get_argument('level', '')
        user = self.current_user

        analyses = user.shared_analyses | user.private_analyses

        is_local_request = is_localhost(self.request.headers['host'])
        dlop = partial(download_link_or_path, is_local_request)
        mappings = {}
        bioms = {}
        tgzs = {}
        for analysis in analyses:
            _id = analysis.id
            mappings[_id], bioms[_id], tgzs[_id] = '', '', ''
            for fid, fp, fpt in retrieve_filepaths('analysis_filepath',
                                                   'analysis_id', _id):
                if fpt == 'plain_text':
                    mappings[_id] = dlop(fp, fid, 'mapping file')
                if fpt == 'biom':
                    bioms[_id] = dlop(fp, fid, 'biom file')
                if fpt == 'tgz':
                    tgzs[_id] = dlop(fp, fid, 'tgz file')

        self.render("list_analyses.html", analyses=analyses, message=message,
                    level=level, is_local_request=is_local_request,
                    mappings=mappings, bioms=bioms, tgzs=tgzs)

    @authenticated
    @execute_as_transaction
    def post(self):
        analysis_id = int(self.get_argument('analysis_id'))
        analysis = Analysis(analysis_id)
        analysis_name = analysis.name.decode('utf-8')

        check_analysis_access(self.current_user, analysis)

        try:
            Analysis.delete(analysis_id)
            msg = ("Analysis <b><i>%s</i></b> has been deleted." % (
                analysis_name))
            level = "success"
        except Exception as e:
            e = str(e)
            msg = ("Couldn't remove <b><i>%s</i></b> analysis: %s" % (
                analysis_name, e))
            level = "danger"
            LogEntry.create('Runtime', "Couldn't remove analysis ID %d: %s" %
                            (analysis_id, e))

        self.redirect(u"%s/analysis/list/?level=%s&message=%s"
                      % (qiita_config.portal_dir, level, msg))


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
