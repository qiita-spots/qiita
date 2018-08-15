from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import TestCase, main, skipIf
from os.path import join, basename
from tempfile import mkdtemp
import pandas as pd
from datetime import datetime
from shutil import rmtree
from os import path
from glob import glob
from paramiko.ssh_exception import AuthenticationException

from h5py import File
from qiita_files.demux import to_hdf5

from qiita_ware.exceptions import ComputeError
from qiita_ware.commands import submit_EBI, list_remote, download_remote
from qiita_db.util import get_mountpoint
from qiita_db.study import Study, StudyPerson
from qiita_db.software import DefaultParameters, Parameters
from qiita_db.artifact import Artifact
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.user import User
from qiita_core.util import qiita_test_checker
from qiita_core.qiita_settings import qiita_config


@qiita_test_checker()
class SSHTests(TestCase):
    def setUp(self):
        self.self_dir_path = path.dirname(path.abspath(__file__))
        self.remote_dir_path = join(self.self_dir_path,
                                    'test_data/test_remote_dir/')
        self.test_ssh_key = join(self.self_dir_path, 'test_data/test_key')
        self.test_wrong_key = join(self.self_dir_path, 'test_data/random_key')
        self.temp_local_dir = mkdtemp()

    def tearDown(self):
        rmtree(self.temp_local_dir)

    def test_list_scp_wrong_key(self):
        """Tests remote file listing using a wrong private key and scp"""
        with self.assertRaises(AuthenticationException):
            list_remote('scp://localhost:'+self.remote_dir_path,
                        self.test_wrong_key)

    def test_list_scp_nonexist_key(self):
        """Tests remote file listing using a missing private key and scp"""
        with self.assertRaises(IOError):
            list_remote('scp://localhost:'+self.remote_dir_path,
                        join(self.self_dir_path, 'nokey'))

    def test_list_scp(self):
        """Tests remote file listing using private key and scp"""
        read_file_list = list_remote('scp://localhost:'+self.remote_dir_path,
                                     self.test_ssh_key)
        remote_filename_list = [basename(f) for f in
                                glob(join(self.remote_dir_path, '*'))]
        self.assertEqual(remote_filename_list, read_file_list)

    def test_list_sftp(self):
        """Tests remote file listing using private key and sftp"""
        read_file_list = list_remote('sftp://localhost:'+self.remote_dir_path,
                                     self.test_ssh_key)
        remote_filename_list = [basename(f) for f in
                                glob(join(self.remote_dir_path, '*'))]
        self.assertEqual(remote_filename_list, read_file_list)

    def test_download_scp(self):
        """Tests remote file listing using private key and scp"""
        download_remote('scp://localhost:'+self.remote_dir_path,
                        self.test_ssh_key, self.temp_local_dir)
        remote_filename_list = [basename(f) for f in
                                glob(join(self.remote_dir_path, '*'))]
        local_filename_list = [basename(f) for f in
                               glob(join(self.temp_local_dir, '*'))]
        self.assertEqual(remote_filename_list, local_filename_list)

    def test_download_sftp(self):
        """Tests remote file listing using private key and sftp"""
        download_remote('sftp://localhost:'+self.remote_dir_path,
                        self.test_ssh_key, self.temp_local_dir)
        remote_filename_list = [basename(f) for f in
                                glob(join(self.remote_dir_path, '*'))]
        local_filename_list = [basename(f) for f in
                               glob(join(self.temp_local_dir, '*'))]
        self.assertEqual(remote_filename_list, local_filename_list)


class CommandsTests(TestCase):
    def setUp(self):
        self.files_to_remove = []
        self.temp_dir = mkdtemp()
        self.files_to_remove.append(self.temp_dir)
        _, self.base_fp = get_mountpoint("preprocessed_data")[0]

    def write_demux_files(self, prep_template, generate_hdf5=True):
        """Writes a demux test file to avoid duplication of code"""
        fna_fp = join(self.temp_dir, 'seqs.fna')
        demux_fp = join(self.temp_dir, 'demux.seqs')
        if generate_hdf5:
            with open(fna_fp, 'w') as f:
                f.write(FASTA_EXAMPLE)
            with File(demux_fp, "w") as f:
                to_hdf5(fna_fp, f)
        else:
            with open(demux_fp, 'w') as f:
                f.write('')

        if prep_template.artifact is None:
            ppd = Artifact.create(
                [(demux_fp, 6)], "Demultiplexed", prep_template=prep_template)
        else:
            params = Parameters.from_default_params(
                DefaultParameters(1),
                {'input_data': prep_template.artifact.id})
            ppd = Artifact.create(
                [(demux_fp, 6)], "Demultiplexed",
                parents=[prep_template.artifact], processing_parameters=params)
        return ppd

    def generate_new_study_with_preprocessed_data(self):
        """Creates a new study up to the processed data for testing"""
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 3,
            "number_samples_promised": 3,
            "study_alias": "Test EBI",
            "study_description": "Study for testing EBI",
            "study_abstract": "Study for testing EBI",
            "emp_person_id": StudyPerson(2),
            "principal_investigator_id": StudyPerson(3),
            "lab_person_id": StudyPerson(1)
        }
        study = Study.create(User('test@foo.bar'), "Test EBI study", info)
        metadata_dict = {
            'Sample1': {'collection_timestamp': datetime(2015, 6, 1, 7, 0, 0),
                        'physical_specimen_location': 'location1',
                        'taxon_id': 9606,
                        'scientific_name': 'homo sapiens',
                        'Description': 'Test Sample 1'},
            'Sample2': {'collection_timestamp': datetime(2015, 6, 2, 7, 0, 0),
                        'physical_specimen_location': 'location1',
                        'taxon_id': 9606,
                        'scientific_name': 'homo sapiens',
                        'Description': 'Test Sample 2'},
            'Sample3': {'collection_timestamp': datetime(2015, 6, 3, 7, 0, 0),
                        'physical_specimen_location': 'location1',
                        'taxon_id': 9606,
                        'scientific_name': 'homo sapiens',
                        'Description': 'Test Sample 3'}
        }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index',
                                          dtype=str)
        SampleTemplate.create(metadata, study)
        metadata_dict = {
            'Sample1': {'primer': 'GTGCCAGCMGCCGCGGTAA',
                        'barcode': 'CGTAGAGCTCTC',
                        'center_name': 'KnightLab',
                        'platform': 'ILLUMINA',
                        'instrument_model': 'Illumina MiSeq',
                        'library_construction_protocol': 'Protocol ABC',
                        'experiment_design_description': "Random value 1"},
            'Sample2': {'primer': 'GTGCCAGCMGCCGCGGTAA',
                        'barcode': 'CGTAGAGCTCTA',
                        'center_name': 'KnightLab',
                        'platform': 'ILLUMINA',
                        'instrument_model': 'Illumina MiSeq',
                        'library_construction_protocol': 'Protocol ABC',
                        'experiment_design_description': "Random value 2"},
            'Sample3': {'primer': 'GTGCCAGCMGCCGCGGTAA',
                        'barcode': 'CGTAGAGCTCTT',
                        'center_name': 'KnightLab',
                        'platform': 'ILLUMINA',
                        'instrument_model': 'Illumina MiSeq',
                        'library_construction_protocol': 'Protocol ABC',
                        'experiment_design_description': "Random value 3"},
        }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index',
                                          dtype=str)
        pt = PrepTemplate.create(metadata, study, "16S", 'Metagenomics')
        fna_fp = join(self.temp_dir, 'seqs.fna')
        demux_fp = join(self.temp_dir, 'demux.seqs')
        with open(fna_fp, 'w') as f:
            f.write(FASTA_EXAMPLE_2.format(study.id))
        with File(demux_fp, 'w') as f:
            to_hdf5(fna_fp, f)

        ppd = Artifact.create(
            [(demux_fp, 6)], "Demultiplexed", prep_template=pt)

        return ppd

    def test_submit_EBI_step_2_failure(self):
        ppd = self.write_demux_files(PrepTemplate(1), True)
        pid = ppd.id

        with self.assertRaises(ComputeError):
            submit_EBI(pid, 'VALIDATE', True)

        rmtree(join(self.base_fp, '%d_ebi_submission' % pid), True)

    @skipIf(
        qiita_config.ebi_seq_xfer_pass == '', 'skip: ascp not configured')
    def test_submit_EBI_parse_EBI_reply_failure(self):
        ppd = self.write_demux_files(PrepTemplate(1))
        pid = ppd.id

        with self.assertRaises(ComputeError) as error:
            submit_EBI(pid, 'VALIDATE', True)
        error = str(error.exception)
        self.assertIn('EBI Submission failed! Log id:', error)
        self.assertIn('The EBI submission failed:', error)

        rmtree(join(self.base_fp, '%d_ebi_submission' % pid), True)

    @skipIf(
        qiita_config.ebi_seq_xfer_pass == '', 'skip: ascp not configured')
    def test_full_submission(self):
        artifact = self.generate_new_study_with_preprocessed_data()
        self.assertEqual(
            artifact.study.ebi_submission_status, 'not submitted')
        aid = artifact.id
        submit_EBI(aid, 'VALIDATE', True, test=True)
        self.assertEqual(artifact.study.ebi_submission_status, 'submitted')

        rmtree(join(self.base_fp, '%d_ebi_submission' % aid), True)


FASTA_EXAMPLE = """>1.SKB2.640194_1 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKB2.640194_2 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKB2.640194_3 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKM4.640180_4 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKM4.640180_5 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKB3.640195_6 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKB6.640176_7 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKD6.640190_8 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKM6.640187_9 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKD9.640182_10 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKM8.640201_11 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>1.SKM2.640199_12 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
"""

FASTA_EXAMPLE_2 = """>{0}.Sample1_1 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>{0}.Sample1_2 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>{0}.Sample1_3 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>{0}.Sample2_4 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>{0}.Sample2_5 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>{0}.Sample2_6 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>{0}.Sample3_7 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>{0}.Sample3_8 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
>{0}.Sample3_9 X orig_bc=X new_bc=X bc_diffs=0
CCACCCAGTAAC
"""


if __name__ == '__main__':
    main()
