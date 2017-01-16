# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from functools import partial

from tornado.web import authenticated

from qiita_core.qiita_settings import qiita_config
from qiita_core.util import execute_as_transaction
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import download_link_or_path
from qiita_pet.handlers.analysis_handlers import check_analysis_access
from qiita_pet.util import is_localhost
from qiita_db.util import get_filepath_id
from qiita_db.analysis import Analysis
from qiita_db.logger import LogEntry


class ListAnalysesHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self):
        message = self.get_argument('message', '')
        level = self.get_argument('level', '')
        user = self.current_user

        analyses = user.shared_analyses | user.private_analyses

        is_local_request = is_localhost(self.request.headers['host'])
        gfi = partial(get_filepath_id, 'analysis')
        dlop = partial(download_link_or_path, is_local_request)
        mappings = {}
        bioms = {}
        tgzs = {}
        for analysis in analyses:
            _id = analysis.id
            # getting mapping file
            mapping = analysis.mapping_file
            if mapping is not None:
                mappings[_id] = dlop(mapping, gfi(mapping), 'mapping file')
            else:
                mappings[_id] = ''

            bioms[_id] = ''
            # getting tgz file
            tgz = analysis.tgz
            if tgz is not None:
                tgzs[_id] = dlop(tgz, gfi(tgz), 'tgz file')
            else:
                tgzs[_id] = ''

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
