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
from os import close, remove
from os.path import exists, join, basename
from functools import partial

import pandas as pd
import numpy as np
from biom.table import Table
from biom.util import biom_open

from qiita_core.util import qiita_test_checker
from qiita_db.artifact import Artifact
from qiita_db.exceptions import (QiitaDBArtifactCreationError,
                                 QiitaDBArtifactDeletionError,
                                 QiitaDBOperationNotPermittedError,
                                 QiitaDBUnknownIDError)
from qiita_db.metadata_template import PrepTemplate
from qiita_db.study import Study
from qiita_db.software import Command, Parameters
from qiita_db.util import get_mountpoint, get_count


@qiita_test_checker()
class ArtifactTests(TestCase):
    def setUp(self):
        # Generate some files for a root artifact
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
        self.filepaths_root = [(self.fp1, 1), (self.fp2, 3)]

        # Generate some files for a processed artifact
        fd, self.fp3 = mkstemp(suffix='_seqs.fna')
        close(fd)
        with open(self.fp3, 'w') as f:
            f.write(">1.sid_r4_0 M02034:17:000000000-A5U18:1:1101:15370:1394 "
                    "1:N:0:1 orig_bc=CATGAGCT new_bc=CATGAGCT bc_diffs=0\n"
                    "GTGTGCCAGCAGCCGCGGTAATACGTAGGG\n")
        self.filepaths_processed = [(self.fp3, 4)]

        # Generate some file for a BIOM
        fd, self.fp4 = mkstemp(suffix='_table.biom')
        t = Table(np.array([[1, 2], [3, 4]]), ['a', 'b'], ['x', 'y'])
        with biom_open(self.fp4, 'w') as f:
            t.to_hdf5(f, "test")
        self.filepaths_biom = [(self.fp4, 7)]

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

        self._clean_up_files = [self.fp1, self.fp2, self.fp3, self.fp4]

    def tearDown(self):
        for f in self._clean_up_files:
            if exists(f):
                remove(f)

    def test_create_error_no_filepaths(self):
        with self.assertRaises(QiitaDBArtifactCreationError):
            Artifact.create([], "FASTQ", prep_template=self.prep_template)

    def test_create_error_prep_template_and_parents(self):
        with self.assertRaises(QiitaDBArtifactCreationError):
            Artifact.create(self.filepaths_root, "FASTQ",
                            prep_template=self.prep_template,
                            parents=[Artifact(1)])

    def test_create_error_no_prep_template_no_parents(self):
        with self.assertRaises(QiitaDBArtifactCreationError):
            Artifact.create(self.filepaths_root, "FASTQ")

    def test_create_error_parents_no_processing_parameters(self):
        with self.assertRaises(QiitaDBArtifactCreationError):
            Artifact.create(self.filepaths_root, "FASTQ",
                            parents=[Artifact(1)])

    def test_create_error_prep_template_and_processing_parameters(self):
        params = Parameters(1, Command(1))
        with self.assertRaises(QiitaDBArtifactCreationError):
            Artifact.create(self.filepaths_root, "FASTQ",
                            prep_template=self.prep_template,
                            processing_parameters=params)

    def test_create_error_different_data_types(self):
        new = Artifact.create(self.filepaths_root, "FASTQ",
                              prep_template=self.prep_template)
        with self.assertRaises(QiitaDBArtifactCreationError):
            Artifact.create(self.filepaths_processed, "Demultiplexed",
                            parents=[Artifact(1), new],
                            processing_parameters=Parameters(1, Command(1)))

    def test_create_root(self):
        fp_count = get_count('qiita.filepath')
        before = datetime.now()
        obs = Artifact.create(self.filepaths_root, "FASTQ",
                              prep_template=self.prep_template)
        self.assertTrue(before < obs.timestamp < datetime.now())
        self.assertIsNone(obs.processing_parameters)
        self.assertEqual(obs.visibility, 'sandbox')
        self.assertEqual(obs.artifact_type, "FASTQ")
        self.assertEqual(obs.data_type, self.prep_template.data_type())
        self.assertFalse(obs.can_be_submitted_to_ebi)
        self.assertFalse(obs.can_be_submitted_to_vamps)

        db_fastq_dir = get_mountpoint('FASTQ')[0][1]
        path_builder = partial(join, db_fastq_dir, str(obs.id))
        exp_fps = [
            (fp_count + 1, path_builder(basename(self.fp1)),
             "raw_forward_seqs"),
            (fp_count + 2, path_builder(basename(self.fp2)), "raw_barcodes"),
        ]
        self.assertEqual(obs.filepaths, exp_fps)
        self.assertEqual(obs.parents, [])
        self.assertEqual(obs.prep_templates, [self.prep_template])

        with self.assertRaises(QiitaDBOperationNotPermittedError):
            obs.ebi_run_accessions

        with self.assertRaises(QiitaDBOperationNotPermittedError):
            obs.is_submitted_to_vamps

        self.assertEqual(obs.study, Study(1))

    def test_create_processed(self):
        fp_count = get_count('qiita.filepath')
        exp_params = Parameters(1, Command(1))
        before = datetime.now()
        obs = Artifact.create(self.filepaths_processed, "Demultiplexed",
                              parents=[Artifact(1)],
                              processing_parameters=exp_params,
                              can_be_submitted_to_ebi=True,
                              can_be_submitted_to_vamps=True)
        self.assertTrue(before < obs.timestamp < datetime.now())
        self.assertEqual(obs.processing_parameters, exp_params)
        self.assertEqual(obs.visibility, 'sandbox')
        self.assertEqual(obs.artifact_type, "Demultiplexed")
        self.assertEqual(obs.data_type, Artifact(1).data_type)
        self.assertTrue(obs.can_be_submitted_to_ebi)
        self.assertTrue(obs.can_be_submitted_to_vamps)
        self.assertFalse(obs.is_submitted_to_vamps)

        db_demultiplexed_dir = get_mountpoint('Demultiplexed')[0][1]
        path_builder = partial(join, db_demultiplexed_dir, str(obs.id))
        exp_fps = [(fp_count + 1, path_builder(basename(self.fp3)),
                    "preprocessed_fasta")]
        self.assertEqual(obs.filepaths, exp_fps)
        self.assertEqual(obs.parents, [Artifact(1)])
        self.assertEqual(obs.prep_templates, [PrepTemplate(1)])
        self.assertEqual(obs.ebi_run_accessions, dict())
        self.assertEqual(obs.study, Study(1))

    def test_create_biom(self):
        fp_count = get_count('qiita.filepath')
        before = datetime.now()
        exp_params = Parameters(1, Command(3))
        obs = Artifact.create(self.filepaths_biom, "BIOM",
                              parents=[Artifact(2)],
                              processing_parameters=exp_params)
        self.assertTrue(before < obs.timestamp < datetime.now())
        self.assertEqual(obs.processing_parameters, exp_params)
        self.assertEqual(obs.visibility, 'sandbox')
        self.assertEqual(obs.artifact_type, 'BIOM')
        self.assertEqual(obs.data_type, Artifact(2).data_type)
        self.assertFalse(obs.can_be_submitted_to_ebi)
        self.assertFalse(obs.can_be_submitted_to_vamps)
        with self.assertRaises(QiitaDBOperationNotPermittedError):
            obs.ebi_run_accessions

        with self.assertRaises(QiitaDBOperationNotPermittedError):
            obs.is_submitted_to_vamps

        db_biom_dir = get_mountpoint('BIOM')[0][1]
        path_builder = partial(join, db_biom_dir, str(obs.id))
        exp_fps = [(fp_count + 1, path_builder(basename(self.fp4)), 'biom')]
        self.assertEqual(obs.filepaths, exp_fps)
        self.assertEqual(obs.parents, [Artifact(2)])
        self.assertEqual(obs.prep_templates, [PrepTemplate(1)])
        self.assertEqual(obs.study, Study(1))

    def test_delete_error_public(self):
        test = Artifact.create(self.filepaths_root, "FASTQ",
                               prep_template=self.prep_template)
        test.visibility = "public"
        with self.assertRaises(QiitaDBArtifactDeletionError):
            Artifact.delete(test.id)

    def test_delete_error_has_children(self):
        with self.assertRaises(QiitaDBArtifactDeletionError):
            Artifact.delete(1)

    def test_delete_error_analyzed(self):
        with self.assertRaises(QiitaDBArtifactDeletionError):
            Artifact.delete(4)

    def test_delete_error_ebi(self):
        obs = Artifact.create(self.filepaths_processed, "Demultiplexed",
                              parents=[Artifact(1)],
                              processing_parameters=Parameters(1, Command(1)),
                              can_be_submitted_to_ebi=True,
                              can_be_submitted_to_vamps=True)
        obs.ebi_run_accessions = {'1.SKB1.640202': 'ERR1000001',
                                  '1.SKB2.640194': 'ERR1000002'}
        with self.assertRaises(QiitaDBArtifactDeletionError):
            Artifact.delete(obs.id)

    def test_delete_error_vamps(self):
        obs = Artifact.create(self.filepaths_processed, "Demultiplexed",
                              parents=[Artifact(1)],
                              processing_parameters=Parameters(1, Command(1)),
                              can_be_submitted_to_ebi=True,
                              can_be_submitted_to_vamps=True)
        obs.is_submitted_to_vamps = True
        with self.assertRaises(QiitaDBArtifactDeletionError):
            Artifact.delete(obs.id)

    def test_delete(self):
        test = Artifact.create(self.filepaths_root, "FASTQ",
                               prep_template=self.prep_template)

        Artifact.delete(test.id)

        with self.assertRaises(QiitaDBUnknownIDError):
            Artifact(test.id)

    def test_timestamp(self):
        self.assertEqual(Artifact(1).timestamp,
                         datetime(2012, 10, 1, 9, 30, 27))
        self.assertEqual(Artifact(2).timestamp,
                         datetime(2012, 10, 1, 10, 30, 27))
        self.assertEqual(Artifact(3).timestamp,
                         datetime(2012, 10, 1, 11, 30, 27))
        self.assertEqual(Artifact(4).timestamp,
                         datetime(2012, 10, 2, 17, 30, 00))

    def test_processing_parameters(self):
        self.assertIsNone(Artifact(1).processing_parameters)
        self.assertEqual(Artifact(2).processing_parameters,
                         Parameters(1, Command(1)))
        self.assertEqual(Artifact(3).processing_parameters,
                         Parameters(2, Command(1)))

    def test_visibility(self):
        self.assertEqual(Artifact(1).visibility, "private")

    def test_visibility_setter(self):
        a = Artifact.create(self.filepaths_root, "FASTQ",
                            prep_template=self.prep_template)
        self.assertEqual(a.visibility, "sandbox")
        a.visibility = "awaiting_approval"
        self.assertEqual(a.visibility, "awaiting_approval")
        a.visibility = "private"
        self.assertEqual(a.visibility, "private")
        a.visibility = "public"
        self.assertEqual(a.visibility, "public")

    def test_artifact_type(self):
        self.assertEqual(Artifact(1).artifact_type, "FASTQ")
        self.assertEqual(Artifact(2).artifact_type, "Demultiplexed")
        self.assertEqual(Artifact(3).artifact_type, "Demultiplexed")
        self.assertEqual(Artifact(4).artifact_type, "BIOM")

    def test_data_type(self):
        self.assertEqual(Artifact(1).data_type, "18S")
        self.assertEqual(Artifact(2).data_type, "18S")
        self.assertEqual(Artifact(3).data_type, "18S")
        self.assertEqual(Artifact(4).data_type, "18S")

    def test_can_be_submitted_to_ebi(self):
        self.assertFalse(Artifact(1).can_be_submitted_to_ebi)
        self.assertTrue(Artifact(2).can_be_submitted_to_ebi)
        self.assertTrue(Artifact(3).can_be_submitted_to_ebi)
        self.assertFalse(Artifact(4).can_be_submitted_to_ebi)

    def test_ebi_run_accessions(self):
        exp = {'1.SKB1.640202': 'ERR0000001',
               '1.SKB2.640194': 'ERR0000002',
               '1.SKB3.640195': 'ERR0000003',
               '1.SKB4.640189': 'ERR0000004',
               '1.SKB5.640181': 'ERR0000005',
               '1.SKB6.640176': 'ERR0000006',
               '1.SKB7.640196': 'ERR0000007',
               '1.SKB8.640193': 'ERR0000008',
               '1.SKB9.640200': 'ERR0000009',
               '1.SKD1.640179': 'ERR0000010',
               '1.SKD2.640178': 'ERR0000011',
               '1.SKD3.640198': 'ERR0000012',
               '1.SKD4.640185': 'ERR0000013',
               '1.SKD5.640186': 'ERR0000014',
               '1.SKD6.640190': 'ERR0000015',
               '1.SKD7.640191': 'ERR0000016',
               '1.SKD8.640184': 'ERR0000017',
               '1.SKD9.640182': 'ERR0000018',
               '1.SKM1.640183': 'ERR0000019',
               '1.SKM2.640199': 'ERR0000020',
               '1.SKM3.640197': 'ERR0000021',
               '1.SKM4.640180': 'ERR0000022',
               '1.SKM5.640177': 'ERR0000023',
               '1.SKM6.640187': 'ERR0000024',
               '1.SKM7.640188': 'ERR0000025',
               '1.SKM8.640201': 'ERR0000026',
               '1.SKM9.640192': 'ERR0000027'}
        self.assertEqual(Artifact(2).ebi_run_accessions, exp)
        self.assertEqual(Artifact(3).ebi_run_accessions, dict())

    def test_ebi_run_accessions_error(self):
        with self.assertRaises(QiitaDBOperationNotPermittedError):
            Artifact(1).ebi_run_accessions

        with self.assertRaises(QiitaDBOperationNotPermittedError):
            Artifact(4).ebi_run_accessions

    def test_ebi_run_accessions_setter(self):
        a = Artifact(3)
        self.assertEqual(a.ebi_run_accessions, dict())
        new_vals = {
            '1.SKB1.640202': 'ERR1000001',
            '1.SKB2.640194': 'ERR1000002',
            '1.SKB3.640195': 'ERR1000003',
            '1.SKB4.640189': 'ERR1000004',
            '1.SKB5.640181': 'ERR1000005',
            '1.SKB6.640176': 'ERR1000006',
            '1.SKB7.640196': 'ERR1000007',
            '1.SKB8.640193': 'ERR1000008',
            '1.SKB9.640200': 'ERR1000009',
            '1.SKD1.640179': 'ERR1000010',
            '1.SKD2.640178': 'ERR1000011',
            '1.SKD3.640198': 'ERR1000012',
            '1.SKD4.640185': 'ERR1000013',
            '1.SKD5.640186': 'ERR1000014',
            '1.SKD6.640190': 'ERR1000015',
            '1.SKD7.640191': 'ERR1000016',
            '1.SKD8.640184': 'ERR1000017',
            '1.SKD9.640182': 'ERR1000018',
            '1.SKM1.640183': 'ERR1000019',
            '1.SKM2.640199': 'ERR1000020',
            '1.SKM3.640197': 'ERR1000021',
            '1.SKM4.640180': 'ERR1000022',
            '1.SKM5.640177': 'ERR1000023',
            '1.SKM6.640187': 'ERR1000024',
            '1.SKM7.640188': 'ERR1000025',
            '1.SKM8.640201': 'ERR1000026',
            '1.SKM9.640192': 'ERR1000027'}
        a.ebi_run_accessions = new_vals
        self.assertEqual(a.ebi_run_accessions, new_vals)

    def test_can_be_submitted_to_vamps(self):
        self.assertFalse(Artifact(1).can_be_submitted_to_vamps)
        self.assertTrue(Artifact(2).can_be_submitted_to_vamps)
        self.assertTrue(Artifact(3).can_be_submitted_to_vamps)
        self.assertFalse(Artifact(4).can_be_submitted_to_vamps)

    def test_is_submitted_to_vamps(self):
        with self.assertRaises(QiitaDBOperationNotPermittedError):
            self.assertFalse(Artifact(1).is_submitted_to_vamps)
        self.assertFalse(Artifact(2).is_submitted_to_vamps)
        self.assertFalse(Artifact(3).is_submitted_to_vamps)
        with self.assertRaises(QiitaDBOperationNotPermittedError):
            self.assertFalse(Artifact(4).is_submitted_to_vamps)

    def test_is_submitted_to_vamps_setter(self):
        a = Artifact(2)
        self.assertFalse(a.is_submitted_to_vamps)
        a.is_submitted_to_vamps = True
        self.assertTrue(a.is_submitted_to_vamps)

    def test_filepaths(self):
        db_test_raw_dir = get_mountpoint('raw_data')[0][1]
        path_builder = partial(join, db_test_raw_dir)
        exp_fps = [
            (1, path_builder('1_s_G1_L001_sequences.fastq.gz'),
             "raw_forward_seqs"),
            (2, path_builder('1_s_G1_L001_sequences_barcodes.fastq.gz'),
             "raw_barcodes")]
        self.assertEqual(Artifact(1).filepaths, exp_fps)

    def test_parents(self):
        self.assertEqual(Artifact(1).parents, [])

        exp_parents = [Artifact(1)]
        self.assertEqual(Artifact(2).parents, exp_parents)
        self.assertEqual(Artifact(3).parents, exp_parents)

        exp_parents = [Artifact(2)]
        self.assertEqual(Artifact(4).parents, exp_parents)

    def test_prep_templates(self):
        self.assertEqual(Artifact(1).prep_templates, [PrepTemplate(1)])
        self.assertEqual(Artifact(1).prep_templates, [PrepTemplate(1)])
        self.assertEqual(Artifact(1).prep_templates, [PrepTemplate(1)])

    def test_study(self):
        self.assertEqual(Artifact(1).study, Study(1))

if __name__ == '__main__':
    main()
