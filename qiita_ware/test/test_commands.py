from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import TestCase, main
from os.path import join
from tempfile import mkdtemp
import pandas as pd
from datetime import datetime

from h5py import File
from qiita_files.demux import to_hdf5

from qiita_ware.exceptions import ComputeError, EBISubmissionError
from qiita_ware.commands import submit_EBI
from qiita_db.study import Study, StudyPerson
from qiita_db.software import DefaultParameters, Parameters
from qiita_db.artifact import Artifact
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.user import User
from qiita_core.util import qiita_test_checker


@qiita_test_checker()
class CommandsTests(TestCase):
    def setUp(self):
        self.files_to_remove = []
        self.temp_dir = mkdtemp()
        self.files_to_remove.append(self.temp_dir)

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
        ppd = self.write_demux_files(PrepTemplate(1), False)

        with self.assertRaises(EBISubmissionError):
            submit_EBI(ppd.id, 'VALIDATE', True)

    def test_submit_EBI_parse_EBI_reply_failure(self):
        ppd = self.write_demux_files(PrepTemplate(1))
        with self.assertRaises(ComputeError):
            submit_EBI(ppd.id, 'VALIDATE', True)

    def test_full_submission(self):
        artifact = self.generate_new_study_with_preprocessed_data()

        # just making sure
        self.assertEqual(artifact.study.ebi_submission_status, 'not submitted')

        submit_EBI(artifact.id, 'VALIDATE', True, test=True)

        self.assertEqual(artifact.study.ebi_submission_status, 'submitted')


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
