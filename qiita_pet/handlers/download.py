from tornado.web import authenticated

from .base_handlers import BaseHandler

class DownloadHandler(BaseHandler):
    @authenticated
    def get(self, filepath_id):
        self.set_header('X-Accel-Redirect',
                        '/protected/preprocessed_data/' +
                        filepath_id)
        self.finish()
