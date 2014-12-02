# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from tornado.web import authenticated, HTTPError

from qiita_ware.util import dataframe_from_template, stats_from_df
from qiita_db.study import Study
from qiita_db.user import User
from qiita_db.metadata_template import SampleTemplate, PrepTemplate
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_pet.handlers.base_handlers import BaseHandler


class MetadataSummaryHandler(BaseHandler):
    @authenticated
    def get(self, arguments):
        study_id = int(self.get_argument('study_id'))

        # this block is tricky because you can either pass the sample or the
        # prep template and if none is passed then we will let an exception
        # be raised because template will not be declared for the logic below
        if self.get_argument('prep_template', None):
            template = PrepTemplate(int(self.get_argument('prep_template')))
        if self.get_argument('sample_template', None):
            template = None
            tid = int(self.get_argument('sample_template'))
            try:
                template = SampleTemplate(tid)
            except QiitaDBUnknownIDError:
                raise HTTPError(404, "SampleTemplate %d does not exist" % tid)

        study = Study(template.study_id)

        # check whether or not the user has access to the requested information
        if not study.has_access(User(self.current_user)):
            raise HTTPError(403, "You do not have access to access this "
                                 "information.")

        df = dataframe_from_template(template)
        stats = stats_from_df(df)

        self.render('metadata_summary.html', user=self.current_user,
                    study_title=study.title, stats=stats,
                    study_id=study_id)
