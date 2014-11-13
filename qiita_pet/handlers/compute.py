from json import loads

from tornado.web import authenticated, HTTPError

from .base_handlers import BaseHandler
from .study_handlers import check_access

from qiita_ware import r_server
from qiita_ware.context import submit
from qiita_ware.dispatchable import add_files_to_raw_data, unlink_all_files

from qiita_db.study import Study
from qiita_db.user import User
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.util import get_mountpoint

from os.path import join, exists


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
        study_id = self.get_argument('study_id')
        raw_data_id = self.get_argument('raw_data_id')
        barcodes_str = self.get_argument('barcodes')
        forward_reads_str = self.get_argument('forward')
        reverse_reads_str = self.get_argument('reverse', None)

        study_id = int(study_id)
        try:
            study = Study(study_id)
        except QiitaDBUnknownIDError:
            # Study not in database so fail nicely
            raise HTTPError(404, "Study %d does not exist" % study_id)
        else:
            check_access(User(self.current_user), study, raise_error=True)

        barcodes, forward_reads, reverse_reads = [], [], []
        for _, f in get_mountpoint("uploads", retrive_all=True):
            f = join(f, str(study_id))
            for t in barcodes_str.split(','):
                ft = join(f, t)
                if exists(ft):
                    barcodes.append([ft, "raw_barcodes"])
            for t in forward_reads_str.split(','):
                ft = join(f, t)
                if exists(ft):
                    forward_reads.append([ft, "raw_forward_seqs"])
            if reverse_reads_str:
                for t in reverse_reads_str.split(','):
                    ft = join(f, t)
                    if exists(ft):
                        reverse_reads.append([ft, "raw_reverse_seqs"])

        # this should never happen if following the GUI pipeline
        # but rather be save than sorry
        if (len(barcodes) != len(forward_reads)
           or (barcodes and len(barcodes) != len(forward_reads))):
            raise HTTPError(404, "user %s tried to submit a wrong pair of "
                                 "barcodes/forward/reverse reads" %
                                 self.current_user)

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


class UnlinkAllFiles(BaseHandler):
    @authenticated
    def post(self):
        # vars to remove all files from a raw data
        study_id = self.get_argument('study_id', None)
        raw_data_id = self.get_argument('raw_data_id', None)

        study_id = int(study_id) if study_id else None

        try:
            study = Study(study_id)
        except QiitaDBUnknownIDError:
            # Study not in database so fail nicely
            raise HTTPError(404, "Study %d does not exist" % study_id)
        else:
            check_access(User(self.current_user), study, raise_error=True)

        job_id = submit(self.current_user, unlink_all_files, raw_data_id)

        self.render('compute_wait.html', user=self.current_user,
                    job_id=job_id, title='Removing files from your raw data',
                    completion_redirect='/study/description/%d' % study_id)
