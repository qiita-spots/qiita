from json import loads

from tornado.web import authenticated, HTTPError
from moi import r_client

from .base_handlers import BaseHandler
from .util import check_access

from qiita_ware.context import submit
from qiita_ware.dispatchable import (add_files_to_raw_data, unlink_all_files,
                                     create_raw_data)
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


class AddFilesToRawData(BaseHandler):
    @authenticated
    @execute_as_transaction
    def post(self):

        # vars to add files to raw data
        study_id = self.get_argument('study_id')
        raw_data_id = self.get_argument('raw_data_id')
        prep_template_id = self.get_argument('prep_template_id')
        barcodes_str = self.get_argument('barcodes')
        forward_reads_str = self.get_argument('forward')
        sff_str = self.get_argument('sff')
        fasta_str = self.get_argument('fasta')
        qual_str = self.get_argument('qual')
        reverse_reads_str = self.get_argument('reverse')

        study_id = int(study_id)
        try:
            study = Study(study_id)
        except QiitaDBUnknownIDError:
            # Study not in database so fail nicely
            raise HTTPError(404, "Study %d does not exist" % study_id)
        else:
            check_access(self.current_user, study, raise_error=True)

        def _split(x):
            return x.split(',') if x else []
        filepaths, fps = [], []
        fps.append((_split(barcodes_str), 'raw_barcodes'))
        fps.append((_split(fasta_str), 'raw_fasta'))
        fps.append((_split(qual_str), 'raw_qual'))
        fps.append((_split(forward_reads_str), 'raw_forward_seqs'))
        fps.append((_split(reverse_reads_str), 'raw_reverse_seqs'))
        fps.append((_split(sff_str), 'raw_sff'))

        for _, f in get_mountpoint("uploads", retrieve_all=True):
            f = join(f, str(study_id))
            for fp_set, filetype in fps:
                for t in fp_set:
                    ft = join(f, t)
                    if exists(ft):
                        filepaths.append((ft, filetype))

        job_id = submit(self.current_user.id, add_files_to_raw_data,
                        raw_data_id, filepaths)

        self.render('compute_wait.html',
                    job_id=job_id, title='Adding files to your raw data',
                    completion_redirect=(
                        '/study/description/%s?top_tab=prep_template_tab'
                        '&sub_tab=%s' % (study_id, prep_template_id)))


class UnlinkAllFiles(BaseHandler):
    @authenticated
    @execute_as_transaction
    def post(self):
        # vars to remove all files from a raw data
        study_id = self.get_argument('study_id', None)
        raw_data_id = self.get_argument('raw_data_id', None)
        prep_template_id = self.get_argument('prep_template_id', None)

        study_id = int(study_id) if study_id else None

        try:
            study = Study(study_id)
        except QiitaDBUnknownIDError:
            # Study not in database so fail nicely
            raise HTTPError(404, "Study %d does not exist" % study_id)
        else:
            check_access(self.current_user, study, raise_error=True)

        job_id = submit(self.current_user.id, unlink_all_files, raw_data_id)

        self.render('compute_wait.html', job_id=job_id,
                    title='Removing files from your raw data',
                    completion_redirect=(
                        '/study/description/%s?top_tab=prep_template_tab&'
                        'sub_tab=%s' % (study_id, prep_template_id)))
