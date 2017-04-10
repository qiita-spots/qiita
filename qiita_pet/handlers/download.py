from tornado.web import authenticated, HTTPError

from os.path import basename, getsize, join
from os import walk
from datetime import datetime

from .base_handlers import BaseHandler
from qiita_pet.handlers.api_proxy import study_get_req
from qiita_db.study import Study
from qiita_db.util import filepath_id_to_rel_path, get_db_files_base_dir
from qiita_db.meta_util import validate_filepath_access_by_user
from qiita_core.util import execute_as_transaction, get_release_info


class DownloadHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self, filepath_id):
        fid = int(filepath_id)

        if not validate_filepath_access_by_user(self.current_user, fid):
            raise HTTPError(
                403, "%s doesn't have access to "
                "filepath_id: %s" % (self.current_user.email, str(fid)))

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
            raise HTTPError(405, "%s: %s, %s" % (study_info['message'],
                                                 self.current_user.email,
                                                 str(study_id)))

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
                    # ignore if tgz as they could create problems and the
                    # raw data is in the folder
                    if data_type == 'tgz':
                        continue
                    if data_type == 'directory':
                        # If we have a directory, we actually need to list
                        # all the files from the directory so NGINX can
                        # actually download all of them
                        for dp, _, fps in walk(path):
                            for fname in fps:
                                fullpath = join(dp, fname)
                                spath = fullpath
                                if fullpath.startswith(basedir):
                                    spath = fullpath[basedir_len:]
                                to_download.append((fullpath, spath, spath))
                    elif path.startswith(basedir):
                        spath = path[basedir_len:]
                        to_download.append((path, spath, spath))
                    else:
                        # We are not aware of any case that can trigger this
                        # situation, but we wanted to be overly cautious
                        # There is no test for this line cause we don't know
                        # how to trigger it
                        to_download.append((path, path, path))

                if to_add:
                    for pt in a.prep_templates:
                        qmf = pt.qiime_map_fp
                        if qmf is not None:
                            sqmf = qmf
                            if qmf.startswith(basedir):
                                sqmf = qmf[basedir_len:]
                            to_download.append(
                                (qmf, sqmf, 'mapping_files/%s_mapping_file.txt'
                                            % a.id))

        # If we don't have nginx, write a file that indicates this
        all_files = '\n'.join(["- %s /protected/%s %s" % (getsize(fp), sfp, n)
                               for fp, sfp, n in to_download])
        self.write("%s\n" % all_files)

        zip_fn = 'study_%d_%s.zip' % (
            study_id, datetime.now().strftime('%m%d%y-%H%M%S'))

        self.set_header('Content-Description', 'File Transfer')
        self.set_header('Expires', '0')
        self.set_header('Cache-Control', 'no-cache')
        self.set_header('X-Archive-Files', 'zip')
        self.set_header('Content-Disposition',
                        'attachment; filename=%s' % zip_fn)
        self.finish()


class DownloadRelease(BaseHandler):
    def get(self, extras):
        _, relpath, _ = get_release_info()

        # If we don't have nginx, write a file that indicates this
        self.write("This installation of Qiita was not equipped with nginx, "
                   "so it is incapable of serving files. The file you "
                   "attempted to download is located at %s" % relpath)

        self.set_header('Content-Description', 'File Transfer')
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Transfer-Encoding', 'binary')
        self.set_header('Expires',  '0')
        self.set_header('Cache-Control',  'no-cache')
        self.set_header('X-Accel-Redirect',
                        '/protected-working_dir/' + relpath)
        self.set_header('Content-Disposition',
                        'attachment; filename=%s' % basename(relpath))

        self.finish()
