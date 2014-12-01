# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from operator import itemgetter

from tornado.web import UIModule
from tornado.gen import Task
from future.utils import viewitems

from qiita_db.util import get_filetypes
from qiita_db.study import Study
from qiita_db.data import RawData
from qiita_db.user import User


def get_raw_data_from_other_studies(user, study):
    """Retrieves a tuple of raw_data_id and the last study title for that
    raw_data
    """
    d = {}
    for sid in user.user_studies:
        if sid == study.id:
            continue
        for rdid in Study(sid).raw_data():
            d[rdid] = Study(RawData(rdid).studies[-1]).title
    return d


class RawDataTab(UIModule):
    def render(self, study_id):
        user = User(self.current_user)
        study = Study(int(study_id))

        filetypes = sorted(viewitems(get_filetypes()), key=itemgetter(1))
        filetypes = ['<option value="%s">%s</option>' % (v, k)
                     for k, v in filetypes]
        other_studies_rd = get_raw_data_from_other_studies(user, study)
        other_studies_rd = ['<option value="%s">%s</option>' % (k,
                            "id: %d, study: %s" % (k, v))
                            for k, v in viewitems(other_studies_rd)]

        return self.render_string(
            "raw_data_tab.html",
            filetypes=filetypes,
            other_studies_rd=other_studies_rd)
