from tornado.web import authenticated

from .base_handlers import BaseHandler


class DownloadHandler(BaseHandler):
    @authenticated
    def get(self, filepath_id):
        # Check access to file
        self.set_header('Content-Description', 'File Transfer')
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Transfer-Encoding', 'binary')
        self.set_header('Expires',  '0')
        self.set_header('X-Accel-Redirect',
                        '/protected/preprocessed_data/' + filepath_id)
        self.finish()
