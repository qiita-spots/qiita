from tornado.web import authenticated

from os.path import basename
from datetime import datetime

from .base_handlers import BaseHandler
from qiita_pet.exceptions import QiitaPetAuthorizationError
from qiita_pet.handlers.api_proxy import study_get_req
from qiita_db.study import Study
from qiita_db.util import filepath_id_to_rel_path, get_db_files_base_dir
from qiita_db.meta_util import validate_filepath_access_by_user
from qiita_core.util import execute_as_transaction


class DownloadHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self, filepath_id):
        fid = int(filepath_id)

        if not validate_filepath_access_by_user(self.current_user, fid):
            raise QiitaPetAuthorizationError(
                self.current_user, 'filepath id %s' % str(fid))

        relpath = filepath_id_to_rel_path(fid)
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


class DownloadStudyBIOMSHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self, study_id):
        study_id = int(study_id)
        # Check access to study
        study_info = study_get_req(study_id, self.current_user.id)

        if study_info['status'] != 'success':
            raise QiitaPetAuthorizationError(
                self.current_user, 'study id %s' % str(study_id))

        study = Study(study_id)
        user = self.current_user
        basedir = get_db_files_base_dir()
        basedir_len = len(basedir) + 1
        # loop over artifacts and retrieve those that we have access to
        to_download = []
        vfabu = validate_filepath_access_by_user
        for a in study.artifacts():
            if a.artifact_type == 'BIOM':
                to_add = True
                for i, (fid, path, data_type) in enumerate(a.filepaths):
                    # validate access only of the first artifact filepath,
                    # the rest have the same permissions
                    if (i == 0 and not vfabu(user, fid)):
                        to_add = False
                        break
                    if path.startswith(basedir):
                        path = path[basedir_len:]
                    to_download.append((path, data_type))

                if to_add:
                    for pt in a.prep_templates:
                        qmf = pt.qiime_map_fp
                        if qmf is not None:
                            if qmf.startswith(basedir):
                                qmf = qmf[basedir_len:]
                            to_download.append((qmf, 'QIIME map file'))

        # If we don't have nginx, write a file that indicates this
        all_files = '\n'.join(['%s: %s' % (n, fp) for fp, n in to_download])
        self.write("This installation of Qiita was not equipped with nginx, "
                   "so it is incapable of serving files. The files you "
                   "attempted to download are located at:\n%s" % all_files)

        zip_fn = 'study_%d_%s.zip' % (
            study_id, datetime.now().strftime('%m%d%y-%H%M%S'))

        self.set_header('Content-Description', 'File Transfer')
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Transfer-Encoding', 'binary')
        self.set_header('Expires', '0')
        self.set_header('Cache-Control', 'no-cache')
        self.set_header('X-Accel-Files', 'zip')
        for fp, n in to_download:
            self.set_header('X-Accel-Redirect', '/protected/' + fp)
        self.set_header('Content-Disposition',
                        'attachment; filename=%s' % zip_fn)
        self.finish()
