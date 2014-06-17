from tornado.escape import url_escape, json_encode
from tornado.web import authenticated

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_core.util import send_email
from qiita_core.exceptions import IncorrectPasswordError, IncorrectEmailError
from qiita_db.user import User
from qiita_db.exceptions import QiitaDBUnknownIDError
# login code modified from https://gist.github.com/guillaumevincent/4771570


class CreateAnalysisHandler(BaseHandler):
    """Analysis creation"""
    def get(self):
        self.render('create_analysis.html', user=self.get_current_user())