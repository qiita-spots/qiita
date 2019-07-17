# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import authenticated, HTTPError
from tornado.gen import coroutine

from future.utils import viewitems
from os.path import basename, getsize, join, isdir
from os import walk
from datetime import datetime

from .base_handlers import BaseHandler
from qiita_pet.handlers.api_proxy.util import check_access
from qiita_db.study import Study
from qiita_db.util import (filepath_id_to_rel_path, get_db_files_base_dir,
                           get_filepath_information, get_mountpoint,
                           filepath_id_to_object_id, get_data_types)
from qiita_db.meta_util import validate_filepath_access_by_user
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_core.util import execute_as_transaction, get_release_info


class BaseHandlerDownload(BaseHandler):
    def _check_permissions(self, sid):
        # Check general access to study
        study_info = check_access(sid, self.current_user.id)
        if study_info:
            raise HTTPError(405, reason="%s: %s, %s" % (
                study_info['message'], self.current_user.email, sid))
        return Study(sid)

    def _generate_files(self, header_name, accessions, filename):
        text = "sample_name\t%s\n%s" % (header_name, '\n'.join(
            ["%s\t%s" % (k, v) for k, v in viewitems(accessions)]))

        self.set_header('Content-Description', 'text/csv')
        self.set_header('Expires', '0')
        self.set_header('Cache-Control', 'no-cache')
        self.set_header('Content-Disposition', 'attachment; '
                        'filename=%s' % filename)
        self.write(text)
        self.finish()

    def _list_dir_files_nginx(self, dirpath):
        """Generates a nginx list of files in the given dirpath for nginx

        Parameters
        ----------
        dirpath : str
            Path to the directory

        Returns
        -------
        list of (str, str, str)
            The path information needed by nginx for each file in the
            directory
        """
        basedir = get_db_files_base_dir()
        basedir_len = len(basedir) + 1
        to_download = []
        for dp, _, fps in walk(dirpath):
            for fn in fps:
                fullpath = join(dp, fn)
                spath = fullpath
                if fullpath.startswith(basedir):
                    spath = fullpath[basedir_len:]
                to_download.append((spath, spath, '-', str(getsize(fullpath))))
        return to_download

    def _list_artifact_files_nginx(self, artifact):
        """Generates a nginx list of files for the given artifact

        Parameters
        ----------
        artifact : qiita_db.artifact.Artifact
            The artifact to retrieve the files

        Returns
        -------
        list of (str, str, str)
            The path information needed by nginx for each file in the artifact
        """
        basedir = get_db_files_base_dir()
        basedir_len = len(basedir) + 1
        to_download = []
        for i, x in enumerate(artifact.filepaths):
            # ignore if tgz as they could create problems and the
            # raw data is in the folder
            if x['fp_type'] == 'tgz':
                continue
            if isdir(x['fp']):
                # If we have a directory, we actually need to list all the
                # files from the directory so NGINX can actually download all
                # of them
                to_download.extend(self._list_dir_files_nginx(x['fp']))
            elif x['fp'].startswith(basedir):
                spath = x['fp'][basedir_len:]
                to_download.append(
                    (spath, spath, str(x['checksum']), str(x['fp_size'])))
            else:
                to_download.append(
                    (x['fp'], x['fp'], str(x['checksum']), str(x['fp_size'])))

        for pt in artifact.prep_templates:
            qmf = pt.qiime_map_fp
            if qmf is not None:
                sqmf = qmf
                if qmf.startswith(basedir):
                    sqmf = qmf[basedir_len:]
                fname = 'mapping_files/%s_mapping_file.txt' % artifact.id
                to_download.append((sqmf, fname, '-', str(getsize(qmf))))
        return to_download

    def _write_nginx_file_list(self, to_download):
        """Writes out the nginx file list

        Parameters
        ----------
        to_download : list of (str, str, str, str)
            The file list information
        """
        all_files = '\n'.join(
            ["%s %s /protected/%s %s" % (fp_checksum, fp_size, fp, fp_name)
             for fp, fp_name, fp_checksum, fp_size in to_download])

        self.set_header('X-Archive-Files', 'zip')
        self.write("%s\n" % all_files)

    def _set_nginx_headers(self, fname):
        """Sets commong nginx headers

        Parameters
        ----------
        fname : str
            Nginx's output filename
        """
        self.set_header('Content-Description', 'File Transfer')
        self.set_header('Expires',  '0')
        self.set_header('Cache-Control',  'no-cache')
        self.set_header('Content-Disposition',
                        'attachment; filename=%s' % fname)

    def _write_nginx_placeholder_file(self, fp):
        """Writes nginx placeholder file in case that nginx is not set up

        Parameters
        ----------
        fp : str
            The path to be downloaded through nginx
        """
        # If we don't have nginx, write a file that indicates this
        self.write("This installation of Qiita was not equipped with "
                   "nginx, so it is incapable of serving files. The file "
                   "you attempted to download is located at %s" % fp)


class DownloadHandler(BaseHandlerDownload):
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, filepath_id):
        fid = int(filepath_id)

        if not validate_filepath_access_by_user(self.current_user, fid):
            raise HTTPError(
                403, "%s doesn't have access to "
                "filepath_id: %s" % (self.current_user.email, str(fid)))

        relpath = filepath_id_to_rel_path(fid)
        fp_info = get_filepath_information(fid)
        fname = basename(relpath)

        if fp_info['filepath_type'] in ('directory', 'html_summary_dir'):
            # This is a directory, we need to list all the files so NGINX
            # can download all of them
            to_download = self._list_dir_files_nginx(fp_info['fullpath'])
            self._write_nginx_file_list(to_download)
            fname = '%s.zip' % fname
        else:
            self._write_nginx_placeholder_file(relpath)
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-Transfer-Encoding', 'binary')
            self.set_header('X-Accel-Redirect', '/protected/' + relpath)
            aid = filepath_id_to_object_id(fid)
            if aid is not None:
                fname = '%d_%s' % (aid, fname)

        self._set_nginx_headers(fname)
        self.finish()


class DownloadStudyBIOMSHandler(BaseHandlerDownload):
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, study_id):
        study_id = int(study_id)
        study = self._check_permissions(study_id)
        # loop over artifacts and retrieve those that we have access to
        to_download = []
        # The user has access to the study, but we don't know if the user
        # can do whatever he wants to the study or just access the public
        # data. (1) an admin has access to all the data; (2) if the study
        # is not public, and the user has access, then it has full access
        # to the data; (3) if the study is public and the user is not the owner
        # or the study is shared with him, then the user doesn't have full
        # access to the study data
        full_access = (
            (self.current_user.level == 'admin') |
            (study.status != 'public') |
            ((self.current_user == study.owner) |
             (self.current_user in study.shared_with)))

        for a in study.artifacts(artifact_type='BIOM'):
            if full_access or a.visibility == 'public':
                to_download.extend(self._list_artifact_files_nginx(a))

        self._write_nginx_file_list(to_download)

        zip_fn = 'study_%d_%s.zip' % (
            study_id, datetime.now().strftime('%m%d%y-%H%M%S'))

        self._set_nginx_headers(zip_fn)
        self.finish()


class DownloadRelease(BaseHandlerDownload):
    @coroutine
    def get(self, extras):
        biom_metadata_release, archive_release = get_release_info()
        if extras == 'archive':
            relpath = archive_release[1]
        else:
            relpath = biom_metadata_release[1]

        # If we don't have nginx, write a file that indicates this
        # Note that this configuration will automatically create and download
        # ("on the fly") the zip file via the contents in all_files
        self._write_nginx_placeholder_file(relpath)

        self._set_nginx_headers(basename(relpath))

        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Transfer-Encoding', 'binary')
        self.set_header('X-Accel-Redirect',
                        '/protected-working_dir/' + relpath)
        self.finish()


class DownloadRawData(BaseHandlerDownload):
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, study_id):
        study_id = int(study_id)
        study = self._check_permissions(study_id)
        user = self.current_user
        # Checking access options
        is_owner = study.has_access(user, True)
        public_raw_download = study.public_raw_download
        if not is_owner and not public_raw_download:
            raise HTTPError(405, reason="%s: %s, %s" % (
                'No raw data access', self.current_user.email, str(study_id)))

        # loop over artifacts and retrieve raw data (no parents)
        to_download = []
        for a in study.artifacts():
            if not a.parents:
                if not is_owner and a.visibility != 'public':
                    continue
                to_download.extend(self._list_artifact_files_nginx(a))

        self._write_nginx_file_list(to_download)

        zip_fn = 'study_raw_data_%d_%s.zip' % (
            study_id, datetime.now().strftime('%m%d%y-%H%M%S'))

        self._set_nginx_headers(zip_fn)
        self.finish()


class DownloadEBISampleAccessions(BaseHandlerDownload):
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, study_id):
        sid = int(study_id)
        self._check_permissions(sid)

        self._generate_files(
            'sample_accession', SampleTemplate(sid).ebi_sample_accessions,
            'ebi_sample_accessions_study_%s.tsv' % sid)


class DownloadEBIPrepAccessions(BaseHandlerDownload):
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, prep_template_id):
        pid = int(prep_template_id)
        pt = PrepTemplate(pid)
        sid = pt.study_id

        self._check_permissions(sid)

        self._generate_files(
            'experiment_accession', pt.ebi_experiment_accessions,
            'ebi_experiment_accessions_study_%s_prep_%s.tsv' % (sid, pid))


class DownloadUpload(BaseHandlerDownload):
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self, path):
        user = self.current_user
        if user.level != 'admin':
            raise HTTPError(403, reason="%s doesn't have access to download "
                            "uploaded files" % user.email)

        # [0] because it returns a list
        # [1] we only need the filepath
        filepath = get_mountpoint("uploads")[0][1][
            len(get_db_files_base_dir()):]
        relpath = join(filepath, path)

        self._write_nginx_placeholder_file(relpath)
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Transfer-Encoding', 'binary')
        self.set_header('X-Accel-Redirect', '/protected/' + relpath)
        self._set_nginx_headers(basename(relpath))
        self.finish()


class DownloadPublicHandler(BaseHandlerDownload):
    @coroutine
    @execute_as_transaction
    def get(self):
        data = self.get_argument("data", None)
        study_id = self.get_argument("study_id",  None)
        data_type = self.get_argument("data_type",  None)
        dtypes = get_data_types().keys()

        if data is None or study_id is None or data not in ('raw', 'biom'):
            raise HTTPError(422, reason='You need to specify both data (the '
                            'data type you want to download - raw/biom) and '
                            'study_id')
        elif data_type is not None and data_type not in dtypes:
            raise HTTPError(422, reason='Not a valid data_type. Valid types '
                            'are: %s' % ', '.join(dtypes))
        else:
            study_id = int(study_id)
            try:
                study = Study(study_id)
            except QiitaDBUnknownIDError:
                raise HTTPError(422, reason='Study does not exist')
            else:
                public_raw_download = study.public_raw_download
                if study.status != 'public':
                    raise HTTPError(422, reason='Study is not public. If this '
                                    'is a mistake contact: '
                                    'qiita.help@gmail.com')
                elif data == 'raw' and not public_raw_download:
                    raise HTTPError(422, reason='No raw data access. If this '
                                    'is a mistake contact: '
                                    'qiita.help@gmail.com')
                else:
                    to_download = []
                    for a in study.artifacts(dtype=data_type,
                                             artifact_type='BIOM'
                                             if data == 'biom' else None):
                        if a.visibility != 'public':
                            continue
                        to_download.extend(self._list_artifact_files_nginx(a))

                    if not to_download:
                        raise HTTPError(422, reason='Nothing to download. If '
                                        'this is a mistake contact: '
                                        'qiita.help@gmail.com')
                    else:
                        self._write_nginx_file_list(to_download)

                        zip_fn = 'study_%d_%s_%s.zip' % (
                            study_id, data, datetime.now().strftime(
                                '%m%d%y-%H%M%S'))

                        self._set_nginx_headers(zip_fn)
        self.finish()
