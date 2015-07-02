from tornado.web import authenticated, HTTPError

from qiita_db.study import Study
from qiita_db.portal import Portal
from .base_handlers import BaseHandler


class StudyPortalHandler(BaseHandler):
    def check_admin(self):
        if self.current_user.level != "admin":
            raise HTTPError(403, "%s does not have access to portal editing!" %
                            self.current_user.id)

    def render_page(self):
        # You must specify an ID column as the first item in cols list.
        # This will be used on the page as the value for the checkboxes and
        # therefore the value returned through the form for a checked box.
        cols = ['study_id', 'study_title', 'study_alias']
        studies = Study.get_info(info_cols=cols)
        portals = Portal.list_portals()
        self.render('portals_edit.html', headers=cols, info=studies,
                    id_col="study_id", portals=portals,
                    submit_url="/admin/portals/studies/")

    @authenticated
    def get(self):
        self.check_admin()
        self.render_page()

    def post(self):
        self.check_admin()
        portal = self.get_argument('portal')
        studies = self.get_arguments('selected')
        action = self.get_argument('action')

        portal = Portal(portal)
        if action == "Add":
            portal.add_studies(studies)
        elif action == "Remove":
            portal.remove_studies(studies)
        else:
            raise HTTPError(400, "Unknown action: %s" % action)
        self.render_page()
