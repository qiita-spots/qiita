from json import loads

from tornado.web import authenticated
from moi import r_client

from .base_handlers import BaseHandler

from qiita_ware.context import submit
from qiita_ware.dispatchable import create_raw_data, copy_raw_data
from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import qiita_config
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

        self.redirect('%s/' % qiita_config.portal_dir)


class CreateRawData(BaseHandler):
    def create_from_scratch(self, prep_template, study_id):
        raw_data_filetype = self.get_argument('filetype')
        barcodes_str = self.get_argument('barcodes')
        forward_reads_str = self.get_argument('forward')
        sff_str = self.get_argument('sff')
        fasta_str = self.get_argument('fasta')
        qual_str = self.get_argument('qual')
        reverse_reads_str = self.get_argument('reverse')

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

        return submit(self.current_user.id, create_raw_data, raw_data_filetype,
                      prep_template, filepaths)

    def create_from_artifact(self, prep_template, artifact_id):
        return submit(self.current_user.id, copy_raw_data,
                      prep_template, artifact_id)

    @authenticated
    @execute_as_transaction
    def post(self):
        pt_id = self.get_argument('prep_template_id')
        pt = PrepTemplate(pt_id)
        study_id = pt.study_id

        artifact_id = self.get_argument('artifact_id', default=None)

        if artifact_id is not None:
            job_id = self.create_from_artifact(pt, artifact_id)
        else:
            job_id = self.create_from_scratch(pt, study_id)

        self.render('compute_wait.html',
                    job_id=job_id, title='Adding raw data',
                    completion_redirect=(
                        '%s/study/description/%s?top_tab=prep_template_tab'
                        '&sub_tab=%s'
                        % (qiita_config.portal_dir, study_id, pt_id)))
