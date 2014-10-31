from json import loads

from tornado.web import authenticated, HTTPError

from .base_handlers import BaseHandler
from .study_handlers import check_access

from qiita_ware import r_server
from qiita_ware.context import submit
from qiita_ware.dispatchable import add_files_to_raw_data

from qiita_db.util import get_study_fp
from qiita_db.study import Study
from qiita_db.user import User
from qiita_db.exceptions import QiitaDBUnknownIDError

from os.path import join


class ComputeCompleteHandler(BaseHandler):
    @authenticated
    def get(self, job_id):
        details = loads(r_server.get(job_id))

        if details['status_msg'] == 'Failed':
            # TODO: something smart
            pass

        self.redirect('/')


class AddFilesToRawData(BaseHandler):
    @authenticated
    def post(self):

        # vars to add files to raw data
        study_id = self.get_argument('study_id', None)
        raw_data_id = self.get_argument('raw_data_id', None)
        barcodes = self.get_argument('barcodes', None)
        forward_reads = self.get_argument('forward', None)
        reverse_reads = self.get_argument('reverse', None)

        study_id = int(study_id)

        try:
            study = Study(study_id)
        except QiitaDBUnknownIDError:
            # Study not in database so fail nicely
            raise HTTPError(404, "Study %d does not exist" % study_id)
        else:
            check_access(User(self.current_user), study)

        fp = get_study_fp(study_id)
        barcodes = [(join(fp, t), "raw_barcodes") for t in barcodes.split(',')]
        forward_reads = [(join(fp, t), "raw_forward_seqs")
                         for t in forward_reads.split(',')]
        if reverse_reads:
            reverse_reads = [(join(fp, t), "raw_reverse_seqs")
                             for t in reverse_reads.split(',')]

        # this should never happen if following the GUI pipeline
        # but rather be save than sorry
        if (len(barcodes) != len(forward_reads)
           or (barcodes and len(barcodes) != len(forward_reads))):
            raise HTTPError(404, "What are you doing?")

        # join all files to send on single var
        filepaths = barcodes
        filepaths.extend(forward_reads)
        if reverse_reads:
            filepaths.extend(reverse_reads)

        job_id = submit(self.current_user, add_files_to_raw_data, raw_data_id,
                        filepaths)

        self.render('compute_wait.html', user=self.current_user,
                    job_id=job_id, title='Adding files to your raw data',
                    completion_redirect='/study/description/%d' % study_id)
