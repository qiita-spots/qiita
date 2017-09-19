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
from qiita_pet.handlers.api_proxy import study_get_req
from qiita_db.study import Study
from qiita_db.util import (filepath_id_to_rel_path, get_db_files_base_dir,
                           get_filepath_information)
from qiita_db.meta_util import validate_filepath_access_by_user
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_core.util import execute_as_transaction, get_release_info


class BaseHandlerDownload(BaseHandler):
    def _check_permissions(self, sid):
        # Check general access to study
        study_info = study_get_req(sid, self.current_user.id)
        if study_info['status'] != 'success':
            raise HTTPError(405, "%s: %s, %s" % (study_info['message'],
                                                 self.current_user.email, sid))
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
                to_download.append((fullpath, spath, spath))
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
        for i, (fid, path, data_type) in enumerate(artifact.filepaths):
            # ignore if tgz as they could create problems and the
            # raw data is in the folder
            if data_type == 'tgz':
                continue
            if isdir(path):
                # If we have a directory, we actually need to list all the
                # files from the directory so NGINX can actually download all
                # of them
                to_download.extend(self._list_dir_files_nginx(path))
            elif path.startswith(basedir):
                spath = path[basedir_len:]
                to_download.append((path, spath, spath))
            else:
                to_download.append((path, path, path))

        for pt in artifact.prep_templates:
            qmf = pt.qiime_map_fp
            if qmf is not None:
                sqmf = qmf
                if qmf.startswith(basedir):
                    sqmf = qmf[basedir_len:]
                to_download.append(
                    (qmf, sqmf, 'mapping_files/%s_mapping_file.txt'
                                % artifact.id))
        return to_download

    def _write_nginx_file_list(self, to_download):
        """Writes out the nginx file list

        Parameters
        ----------
        to_download : list of (str, str, str)
            The file list information
        """
        all_files = '\n'.join(
            ["- %s /protected/%s %s" % (getsize(fp), sfp, n)
             for fp, sfp, n in to_download])

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
        for a in study.artifacts():
            if a.artifact_type == 'BIOM':
                to_download.extend(self._list_artifact_files_nginx(a))

        self._write_nginx_file_list(to_download)

        zip_fn = 'study_%d_%s.zip' % (
            study_id, datetime.now().strftime('%m%d%y-%H%M%S'))

        self._set_nginx_headers(zip_fn)
        self.finish()


class DownloadRelease(BaseHandlerDownload):
    @coroutine
    def get(self, extras):
        _, relpath, _ = get_release_info()

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
        # Check "owner" access to the study
        if not study.has_access(user, True):
            raise HTTPError(405, "%s: %s, %s" % ('No raw data access',
                                                 self.current_user.email,
                                                 str(study_id)))

        # loop over artifacts and retrieve raw data (no parents)
        to_download = []
        for a in study.artifacts():
            if not a.parents:
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
