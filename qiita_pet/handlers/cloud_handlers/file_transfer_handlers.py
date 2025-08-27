import os

from tornado.web import HTTPError, RequestHandler
from tornado.gen import coroutine

from qiita_core.util import execute_as_transaction
from qiita_db.handlers.oauth2 import authenticate_oauth
from qiita_core.qiita_settings import qiita_config


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

        # delivery of the file via nginx requires replacing the basedatadir
        # with the prefix defined in the nginx configuration for the
        # base_data_dir, '/protected/' by default
        protected_filepath = filepath.replace(basedatadir, '/protected')

        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Transfer-Encoding', 'binary')
        self.set_header('X-Accel-Redirect', protected_filepath)
        self.set_header('Content-Description', 'File Transfer')
        self.set_header('Expires',  '0')
        self.set_header('Cache-Control',  'no-cache')
        self.set_header('Content-Disposition',
                        'attachment; filename=%s' % os.path.basename(
                            protected_filepath))
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

        for filespath, filelist in self.request.files.items():
            if filespath.startswith(basedatadir):
                filespath = filespath[len(basedatadir):]

            for file in filelist:
                filepath = os.path.join(filespath, file['filename'])
                # remove leading /
                if filepath.startswith(os.sep):
                    filepath = filepath[len(os.sep):]
                filepath = os.path.abspath(os.path.join(basedatadir, filepath))

                if os.path.exists(filepath):
                    raise HTTPError(403, reason=(
                        "The requested file is already "
                        "present in Qiita's BASE_DATA_DIR!"))

                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(file['body'])
                    stored_files.append(filepath)

        self.write("Stored %i files into BASE_DATA_DIR of Qiita:\n%s\n" % (
            len(stored_files),
            '\n'.join(map(lambda x: ' - %s' % x, stored_files))))

        self.finish()
