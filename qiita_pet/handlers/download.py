from tornado.web import authenticated

from os.path import basename

from .base_handlers import BaseHandler
from qiita_pet.exceptions import QiitaPetAuthorizationError
from qiita_db.util import filepath_id_to_rel_path
from qiita_db.meta_util import get_accessible_filepath_ids
from qiita_core.util import execute_as_transaction


class DownloadHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self, filepath_id):
        filepath_id = int(filepath_id)
        # Check access to file
        accessible_filepaths = get_accessible_filepath_ids(self.current_user)

        if filepath_id not in accessible_filepaths:
            raise QiitaPetAuthorizationError(
                self.current_user, 'filepath id %s' % str(filepath_id))

        relpath = filepath_id_to_rel_path(filepath_id)
        fname = basename(relpath)

        # If we don't have nginx, write a file that indicates this
        self.write("This installation of Qiita was not equipped with nginx, "
                   "so it is incapable of serving files. The file you "
                   "attempted to download is located at %s" % relpath)

        self.set_header('Content-Description', 'File Transfer')
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Transfer-Encoding', 'binary')
        self.set_header('Expires',  '0')
        self.set_header('Cache-Control',  'no-cache')
        self.set_header('X-Accel-Redirect', '/protected/' + relpath)
        self.set_header('Content-Disposition',
                        'attachment; filename=%s' % fname)

        self.finish()
