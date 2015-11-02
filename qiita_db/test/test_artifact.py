# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from tempfile import mkstemp
from datetime import datetime
from os import close

import pandas as pd

from qiita_core.util import qiita_test_checker
from qiita_db.artifact import Artifact
from qiita_db.exceptions import QiitaDBArtifactCreationError
from qiita_db.metadata_template import PrepTemplate
from qiita_db.study import Study


@qiita_test_checker()
class ArtifactTests(TestCase):
    def setUp(self):
        fd, self.fp1 = mkstemp(suffix='_seqs.fastq')
        close(fd)
        with open(self.fp1, 'w') as f:
            f.write("@HWI-ST753:189:D1385ACXX:1:1101:1214:1906 1:N:0:\n"
                    "NACGTAGGGTGCAAGCGTTGTCCGGAATNA\n"
                    "+\n"
                    "#1=DDFFFHHHHHJJJJJJJJJJJJGII#0\n")

        fd, self.fp2 = mkstemp(suffix='_barcodes.fastq')
        close(fd)
        with open(self.fp2, 'w') as f:
            f.write("@HWI-ST753:189:D1385ACXX:1:1101:1214:1906 2:N:0:\n"
                    "NNNCNNNNNNNNN\n"
                    "+\n"
                    "#############\n")
        self.filepaths_root = [(self.fp1, 1), (self.fp2, 2)]

        # Create a new prep template
        metadata_dict = {
            'SKB8.640193': {'center_name': 'ANL',
                            'primer': 'GTGCCAGCMGCCGCGGTAA',
                            'barcode': 'GTCCGCAAGTTA',
                            'run_prefix': "s_G1_L001_sequences",
                            'platform': 'ILLUMINA',
                            'instrument_model': 'Illumina MiSeq',
                            'library_construction_protocol': 'AAAA',
                            'experiment_design_description': 'BBBB'}}
        metadata = pd.DataFrame.from_dict(metadata_dict, orient='index')
        self.prep_template = PrepTemplate.create(metadata, Study(1), "16S")

    def test_create_error_no_filepaths(self):
        with self.assertRaieses(QiitaDBArtifactCreationError):
            Artifact.create([], "FASTQ", prep_template=self.prep_template)

    def test_create_error_prep_template_and_parents(self):
        with self.assertRaieses(QiitaDBArtifactCreationError):
            Artifact.create(self.filepaths_root, "FASTQ",
                            prep_template=self.prep_template,
                            parents=[Artifact(1)])

    def test_create_error_no_prep_template_no_parents(self):
        with self.assertRaieses(QiitaDBArtifactCreationError):
            Artifact.create(self.filepaths_root, "FASTQ")

    def test_create_error_parents_no_processing_parameters(self):
        with self.assertRaieses(QiitaDBArtifactCreationError):
            Artifact.create(self.filepaths_root, "FASTQ",
                            parents=[Artifact(1)])

    def test_create_prep_template_and_processing_parameters(self):
        with self.assertRaieses(QiitaDBArtifactCreationError):
            Artifact.create(self.filepaths_root, "FASTQ",
                            prep_template=self.prep_template,
                            processing_parameters=None)

    def test_create_root(self):
        exp_timestamp = datetime(2015, 11, 1, 16, 35)
        obs = Artifact.create(self.filepaths_root, "FASTQ",
                              timestamp=exp_timestamp,
                              prep_template=self.prep_template)
        self.assertEqual(obs.timestamp, exp_timestamp)
        self.assertEqual(obs.processing_parameters, exp_params)
        self.assertEqual(obs.visibility, 'sandbox')
        self.assertEqual(obs.artifact_type, "FASTQ")
        self.assertFalse(obs.can_be_submitted_to_ebi)
        self.assertFalse(obs.can_be_submitted_to_vamps)
        self.assertFalse(obs.is_submitted_to_vamps)
        self.assertEqual(obs.filepaths, exp_fps)
        self.assertEqual(obs.parents, [])
        self.assertEqual(obs.prep_template, self.prep_template.id)
        self.assertEqual(obs.ebi_run_accessions, dict())
        self.assertEqual(obs.study, 1)

    def test_create_processed(self):
        exp_timestamp = datetime(2015, 11, 1, 16, 40)
        obs = Artifact.create(self.filepaths, "TYPE", timestamp=None,
                              prep_template=None, parents=None,
                              processing_parameters=None,
                              can_be_submitted_to_ebi=None,
                              can_be_submitted_to_vamps=False)
        self.assertEqual(obs.timestamp, exp_timestamp)
        self.assertEqual(obs.processing_parameters, exp_params)
        self.assertEqual(obs.visibility, 'sandbox')
        self.assertEqual(obs.artifact_type, "FASTQ")
        self.assertFalse(obs.can_be_submitted_to_ebi)
        self.assertFalse(obs.can_be_submitted_to_vamps)
        self.assertFalse(obs.is_submitted_to_vamps)
        self.assertEqual(obs.filepaths, exp_fps)
        self.assertEqual(obs.parents, [])
        self.assertEqual(obs.prep_template, self.prep_template.id)
        self.assertEqual(obs.ebi_run_accessions, dict())
        self.assertEqual(obs.study, 1)

    def test_delete(self):
        pass

    def test_tiemstamp(self):
        pass

    def test_processing_parameters(self):
        pass

    def test_visibility(self):
        pass

    def test_artifact_type(self):
        pass

    def test_can_be_submitted_to_ebi(self):
        pass

    def test_can_be_submitted_to_vamps(self):
        pass

    def test_is_submitted_to_vamps(self):
        pass

    def test_filepahts(self):
        pass

    def test_parents(self):
        pass

    def test_prep_template(self):
        pass

    def test_ebi_run_accessions(self):
        pass

    def test_study(self):
        pass

if __name__ == '__main__':
    main()
