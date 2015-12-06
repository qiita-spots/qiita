from json import loads

from tornado.web import authenticated, HTTPError
from moi import r_client

from .base_handlers import BaseHandler
from .util import check_access

from qiita_ware.context import submit
from qiita_ware.dispatchable import create_raw_data
from qiita_core.util import execute_as_transaction
from qiita_db.study import Study
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.util import get_mountpoint
from qiita_db.metadata_template.prep_template import PrepTemplate

from os.path import join, exists


class ComputeCompleteHandler(BaseHandler):
    @authenticated
    def get(self, job_id):
        details = loads(r_client.get(job_id))

        if details['status_msg'] == 'Failed':
            # TODO: something smart
            pass

        self.redirect('/')


class CreateRawData(BaseHandler):
    @authenticated
    @execute_as_transaction
    def post(self):
        pt_id = self.get_argument('prep_template_id')
        raw_data_filetype = self.get_argument('filetype')
        barcodes_str = self.get_argument('barcodes')
        forward_reads_str = self.get_argument('forward')
        sff_str = self.get_argument('sff')
        fasta_str = self.get_argument('fasta')
        qual_str = self.get_argument('qual')
        reverse_reads_str = self.get_argument('reverse')

        pt = PrepTemplate(pt_id)
        study_id = pt.study_id

        def _split(x):
            return x.split(',') if x else []
        filepaths, fps = [], []
        fps.append((_split(barcodes_str), 'raw_barcodes'))
        fps.append((_split(fasta_str), 'raw_fasta'))
        fps.append((_split(qual_str), 'raw_qual'))
        fps.append((_split(forward_reads_str), 'raw_forward_seqs'))
        fps.append((_split(reverse_reads_str), 'raw_reverse_seqs'))
        fps.append((_split(sff_str), 'raw_sff'))

        # We need to retrieve the full path for all the files, as the
        # arguments only contain the file name. Since we don't know in which
        # mountpoint the data lives, we retrieve all of them and we loop
        # through all the files checking if they exist or not.
        for _, f in get_mountpoint("uploads", retrieve_all=True):
            f = join(f, str(study_id))
            for fp_set, filetype in fps:
                for t in fp_set:
                    ft = join(f, t)
                    if exists(ft):
                        filepaths.append((ft, filetype))

        job_id = submit(self.current_user.id, create_raw_data,
                        raw_data_filetype, pt, filepaths)

        self.render('compute_wait.html',
                    job_id=job_id, title='Adding raw data',
                    completion_redirect=(
                        '/study/description/%s?top_tab=prep_template_tab'
                        '&sub_tab=%s' % (study_id, pt_id)))
