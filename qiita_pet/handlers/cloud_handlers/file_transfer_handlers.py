import os
from pathlib import Path
import zipfile
from io import BytesIO

from tornado.gen import coroutine
from tornado.web import HTTPError, RequestHandler

from qiita_core.qiita_settings import qiita_config
from qiita_core.util import execute_as_transaction, is_test_environment
from qiita_db.handlers.oauth2 import authenticate_oauth
from qiita_pet.handlers.download import BaseHandlerDownload
import qiita_db as qdb


def is_directory(filepath):
    """Tests if given filepath is listed as directory in Qiita DB.

    Note: this is independent of the actual filesystem, only checks DB entries.

    Parameters
    ----------
    filepath : str
        The filepath to the directory that shall be tested for beeing listed
        as directory in Qiita's DB

    Returns
    -------
    Bool: True if the last part of the filepath is contained as filepath in
          qiita.filepath AND part after base_data_dir is a mountpoint in
          qiita.data_directory AND the filepath_type is 'directory or
          'html_summary_dir'.
    False otherwise.
    """
    working_filepath = filepath
    # chop off trailing / to ensure we point to a directory name properly
    if working_filepath.endswith(os.sep):
        working_filepath = os.path.dirname(working_filepath)

    dirname = os.path.basename(working_filepath)
    # file-objects foo are stored in <base_data_dir>/<mountpoint>/foo. To
    # determine mountpoint from a given filepath, we need to chop of
    # base_data_dir and then take the top directory level.
    # Checking if user provided filepath contains a valid mountpoint adds
    # to preventing users to download arbitrary file contents
    try:
        mount_dirname = Path(working_filepath).relative_to(
            Path(qiita_config.base_data_dir)).parts[0]
    except ValueError:
        # base_data_dir is no proper prefix of given filepath
        return False
    except IndexError:
        # only base_data_dir given
        return False
    if dirname == '' or mount_dirname == '':
        # later should never be true due to above IndexError, but better save
        # than sorry
        return False

    with qdb.sql_connection.TRN:
        # find entries that
        #   a) are of filepath_type "directory" or "html_summary_dir"
        #   b) whose filepath ends with directory name
        #   c) whose mountpoint matches the provided parent_directory
        sql = """SELECT filepath_id
                FROM qiita.filepath
                    JOIN qiita.filepath_type USING (filepath_type_id)
                    JOIN qiita.data_directory USING (data_directory_id)
                WHERE filepath_type IN ('directory', 'html_summary_dir') AND
                    filepath=%s AND
                    position(%s in mountpoint)>0;"""
        qdb.sql_connection.TRN.add(sql, [dirname, mount_dirname])
        hits = qdb.sql_connection.TRN.execute_fetchflatten()
        return len(hits) > 0


class FetchFileFromCentralHandler(RequestHandler):
    @authenticate_oauth
    @coroutine
    @execute_as_transaction
    def get(self, requested_filepath):
        # ensure we have an absolute path, i.e. starting at /
        filepath = os.path.join(os.path.sep, requested_filepath)
        # use a canonic version of the filepath
        filepath = os.path.abspath(filepath)

        # canonic version of base_data_dir
        basedatadir = os.path.abspath(qiita_config.base_data_dir)

        # TODO: can we somehow check, if the requesting client (which should be
        #       one of the plugins) was started from a user that actually has
        #       access to the requested file?

        if not filepath.startswith(basedatadir):
            # attempt to access files outside of the BASE_DATA_DIR
            # intentionally NOT reporting the actual location to avoid exposing
            # instance internal information
            raise HTTPError(403, reason=(
                "You cannot access files outside of "
                "the BASE_DATA_DIR of Qiita!"))

        if not os.path.exists(filepath):
            raise HTTPError(403, reason=(
                "The requested file is not present in Qiita's BASE_DATA_DIR!"))

        filename_directory = "qiita-main-data.zip"
        if os.path.isdir(filepath):
            # Test if this directory is managed by Qiita's DB as directory
            # Thus we can prevent that a lazy client simply downloads the whole
            # basa_data_directory
            if not is_directory(filepath):
                raise HTTPError(403, reason=(
                    "You cannot access this directory!"))
            else:
                # flag the response for qiita_client
                self.set_header('Is-Qiita-Directory', 'yes')

        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Transfer-Encoding', 'binary')
        self.set_header('Content-Description', 'File Transfer')
        self.set_header('Expires',  '0')
        self.set_header('Cache-Control',  'no-cache')

        # We here need to differentiate a request that comes directly to the
        # qiita instance (happens in testing) or was redirected through nginx
        # (should be the default). If nginx, we can use nginx' fast file
        # delivery mechanisms, otherwise, we need to send via slower tornado.
        # We indirectly infer this by looking for the "X-Forwarded-For" header,
        # which should only exists when redirectred through nginx.
        if self.request.headers.get('X-Forwarded-For') is None:
            # delivery via tornado
            if not is_directory(filepath):
                # a single file
                self.set_header(
                    'Content-Disposition',
                    'attachment; filename=%s' % os.path.basename(filepath))
                with open(filepath, "rb") as f:
                    self.write(f.read())
            else:
                # a whole directory
                memfile = BytesIO()
                with zipfile.ZipFile(memfile, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for root, dirs, files in os.walk(filepath):
                        for file in files:
                            full_path = os.path.join(root, file)
                            # make path in zip file relative
                            rel_path = os.path.relpath(full_path, filepath)
                            zf.write(full_path, rel_path)
                memfile.seek(0)
                self.set_header('Content-Type', 'application/zip')
                self.set_header('Content-Disposition',
                                'attachment; filename=%s' % filename_directory)
                self.write(memfile.read())
        else:
            # delivery via nginx
            if not is_directory(filepath):
                # a single file:
                # delivery of the file via nginx requires replacing the
                # basedatadir with the prefix defined in the nginx
                # configuration for the base_data_dir, '/protected/' by default
                protected_filepath = filepath.replace(basedatadir,
                                                      '/protected')
                self.set_header('X-Accel-Redirect', protected_filepath)
                self.set_header(
                    'Content-Disposition',
                    'attachment; filename=%s' % os.path.basename(
                        protected_filepath))
            else:
                # a whole directory
                to_download = BaseHandlerDownload._list_dir_files_nginx(
                    self, filepath)

                # fp_subdir is the part of the filepath the user requested,
                # without QIITA_BASE_DIR
                fp_subdir = os.path.relpath(filepath, basedatadir)

                # above function adds filepath to located files, which is
                # different from the non-nginx version, e.g.
                # fp = /protected/job/2_test_folder/testdir/fileA.txt
                # fp_name = job/2_test_folder/testdir/fileA.txt
                # where "job/2_test_folder" is what user requested and
                #       "testdir/fileA.txt" is a file within this directory.
                # When extracting by qiita_client, the "job/2_test_folder"
                # part would be added twice (one by user request, second by
                # unzipping). Therefore, we need to correct these names here:
                to_download = [
                    (fp, os.path.relpath(fp_name, fp_subdir), fp_checksum,
                     fp_size)
                    for fp, fp_name, fp_checksum, fp_size
                    in to_download]
                BaseHandlerDownload._write_nginx_file_list(self, to_download)
                BaseHandlerDownload._set_nginx_headers(
                    self, filename_directory)

        self.finish()


class PushFileToCentralHandler(RequestHandler):
    @authenticate_oauth
    @coroutine
    @execute_as_transaction
    def post(self):
        if not self.request.files:
            raise HTTPError(400, reason='No files to upload defined!')

        # canonic version of base_data_dir
        basedatadir = os.path.abspath(qiita_config.base_data_dir)
        stored_files = []
        stored_directories = []

        for filespath, filelist in self.request.files.items():
            if filespath.startswith(basedatadir):
                filespath = filespath[len(basedatadir):]

            for file in filelist:
                # differentiate between regular files and whole directories,
                # which must be zipped AND the client must provide the
                # is_directory='true' body argument.
                sent_directory = self.get_body_argument(
                    'is_directory', "false") == "true"

                filepath = os.path.join(filespath, file['filename'])
                # remove leading /
                if filepath.startswith(os.sep):
                    filepath = filepath[len(os.sep):]
                filepath = os.path.abspath(os.path.join(basedatadir, filepath))

                if sent_directory:
                    # if a whole directory was send, we want to store it at
                    # the given dirname of the filepath
                    filepath = os.path.dirname(filepath)

                # prevent overwriting existing files, except in test mode
                if os.path.exists(filepath) and (not is_test_environment()):
                    raise HTTPError(403, reason=(
                        "The requested %s is already "
                        "present in Qiita's BASE_DATA_DIR!" %
                        ('directory' if sent_directory else 'file')))

                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                if sent_directory:
                    with zipfile.ZipFile(BytesIO(file['body'])) as zf:
                        zf.extractall(filepath)
                        stored_directories.append(filepath)
                else:
                    with open(filepath, "wb") as f:
                        f.write(file['body'])
                        stored_files.append(filepath)

        for (_type, objs) in [('files', stored_files),
                              ('directories', stored_directories)]:
            if len(objs) > 0:
                self.write(
                    "Stored %i %s into BASE_DATA_DIR of Qiita:\n%s\n" % (
                        len(objs),
                        _type,
                        '\n'.join(map(lambda x: ' - %s' % x, objs))))

        self.finish()