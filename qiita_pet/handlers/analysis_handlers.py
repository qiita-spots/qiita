from tornado.web import authenticated

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.user import User
from qiita_db.analysis import Analysis
from qiita_db.study import Study
# login code modified from https://gist.github.com/guillaumevincent/4771570


class CreateAnalysisHandler(BaseHandler):
    """Analysis creation"""
    @authenticated
    def get(self):
        self.render('create_analysis.html', user=self.get_current_user())


class SelectStudiesHandler(BaseHandler):
    """Study selection"""
    @authenticated
    def post(self):
        name = self.get_argument('name')
        description = self.get_argument('description')
        user = self.get_current_user()
        # create list of studies
        study_ids = {s.id for s in Study.get_public()}
        userobj = User(user)
        [study_ids.add(x) for x in userobj.private_studies]
        [study_ids.add(x) for x in userobj.shared_studies]

        studies = [Study(i) for i in study_ids]
        analysis = Analysis.create(User(user), name, description)

        self.render('select_studies.html', user=user, aid=analysis.id,
                    studies=studies)