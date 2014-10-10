from tornado.web import authenticated, RequestHandler

from os.path import isdir, join, exists
from os import makedirs, listdir

from shutil import copyfileobj, rmtree

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.util import get_study_fp


class UploadFileHandler(BaseHandler):
    # """ main upload class
    # based on
    # https://github.com/23/resumable.js/blob/master/samples/Backend%20on%20PHP.md
    # """

    @authenticated
    def post(self):
        resumable_identifier = self.get_argument('resumableIdentifier')
        resumable_filename = self.get_argument('resumableFilename')
        resumable_chunk_number = int(self.get_argument('resumableChunkNumber'))
        resumable_total_chunks = int(self.get_argument('resumableTotalChunks'))
        study_id = self.get_argument('study_id')
        data = self.request.files['file'][0]['body']

        fp = join(get_study_fp(study_id), resumable_identifier)
        # creating temporal folder for upload
        if not isdir(fp):
            makedirs(fp)
        dfp = join(fp, '%s.part.%d' % (resumable_filename,
                                       resumable_chunk_number))

        # writting the output file
        with open(dfp, 'wb') as f:
            f.write(bytes(data))

        # validating if all files have been uploaded
        num_files = len([n for n in listdir(fp)])
        if resumable_total_chunks == num_files:
            # creating final destination
            ffp = join(get_study_fp(study_id), resumable_filename)
            with open(ffp, 'wb') as f:
                for c in range(1, resumable_total_chunks+1):
                    chunk = join(fp, '%s.part.%d' % (resumable_filename, c))
                    copyfileobj(open(chunk, 'rb'), f)

                # deleting the tmp folder with contents and finish file
                rmtree(fp)
                self.set_status(200)

    @authenticated
    def get(self):
        """ this is the first point of entry into the upload service

        this should either set the status as 400 (error) so the file/chunk is
        sent via post or 200 (valid) to not send the file
        """
        study_id = self.get_argument('study_id')

        # temporaly filename or chunck
        tfp = join(get_study_fp(study_id),
                   self.get_argument('resumableFilename') + '.part.' +
                   self.get_argument('resumableChunkNumber'))

        if exists(tfp):
            self.set_status(200)
        else:
            self.set_status(400)
