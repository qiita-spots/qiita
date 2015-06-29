from tornado.web import authenticated, HTTPError

from qiita_db.study import Study
from qiita_db.portal import (list_portals)
from .base_handlers import BaseHandler


class StudyPortalHandler(BaseHandler):
    def check_admin(self):
        if self.current_user.status != "admin":
            raise HTTPError(403, "%s does not have access to portal editing!" %
                            self.current_user.id)

    @authenticated
    def get(self):
        # check_admin()
        # COLS MUST HAVE AN ID COLUMN!
        cols = ['study_id', 'study_title', 'study_alias']
        studies = Study.get_info(info_cols=cols)
        portals = list_portals()
        self.render('portals_edit.html', headers=cols, info=studies,
                    id_col="study_id", portals=portals,
                    submit_url="/admin/portals/studies/")
