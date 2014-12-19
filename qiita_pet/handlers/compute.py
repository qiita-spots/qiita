from json import loads

from tornado.web import authenticated, HTTPError
from moi import r_client

from .base_handlers import BaseHandler
from .util import check_access

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
        details = loads(r_client.get(job_id))

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
        sff_str = self.get_argument('sff')
        reverse_reads_str = self.get_argument('reverse')

        study_id = int(study_id)
        try:
            study = Study(study_id)
        except QiitaDBUnknownIDError:
            # Study not in database so fail nicely
            raise HTTPError(404, "Study %d does not exist" % study_id)
        else:
            check_access(User(self.current_user), study, raise_error=True)

        _split = lambda x: x.split(',') if x else []
        barcodes, fwd_reads, rev_reads, sff, fps = [], [], [], [], []
        fps.append((_split(barcodes_str), 'raw_barcodes', barcodes))
        fps.append((_split(forward_reads_str), 'raw_forward_seqs', fwd_reads))
        fps.append((_split(reverse_reads_str), 'raw_reverse_seqs', rev_reads))
        fps.append((_split(sff_str), 'raw_sff', sff))

        for _, f in get_mountpoint("uploads", retrive_all=True):
            f = join(f, str(study_id))
            for fp_set, filetype, fps_to_keep in fps:
                for t in fp_set:
                    ft = join(f, t)
                    if exists(ft):
                        fps_to_keep.append((ft, filetype))

        # this should never happen if following the GUI pipeline
        # but rather be save than sorry
        if (len(barcodes) != len(fwd_reads)
           or (barcodes and len(barcodes) != len(fwd_reads))):
            raise HTTPError(404, "user %s tried to submit a wrong pair of "
                                 "barcodes/forward/reverse reads" %
                                 self.current_user)

        # join all files to send on single var
        filepaths = barcodes
        filepaths.extend(fwd_reads)
        filepaths.extend(sff)
        filepaths.extend(rev_reads)

        job_id = submit(self.current_user, add_files_to_raw_data, raw_data_id,
                        filepaths)

        self.render('compute_wait.html', user=self.current_user,
                    job_id=job_id, title='Adding files to your raw data',
                    completion_redirect=(
                        '/study/description/%s?top_tab=raw_data_tab&sub_tab=%s'
                        % (study_id, raw_data_id)))


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
                    completion_redirect=(
                        '/study/description/%s?top_tab=raw_data_tab&sub_tab=%s'
                        % (study_id, raw_data_id)))
