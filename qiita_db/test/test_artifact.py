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
import networkx as nx
from biom import example_table as et
from biom.util import biom_open

from qiita_core.util import qiita_test_checker
import qiita_db as qdb


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
        with biom_open(self.fp4, 'w') as f:
            et.to_hdf5(f, "test")
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
        self.prep_template = \
            qdb.metadata_template.prep_template.PrepTemplate.create(
                metadata, qdb.study.Study(1), "16S")

        self._clean_up_files = [self.fp1, self.fp2, self.fp3, self.fp4]

    def tearDown(self):
        for f in self._clean_up_files:
            if exists(f):
                remove(f)

    def test_iter(self):
        obs = list(qdb.artifact.Artifact.iter_by_visibility('public'))
        self.assertEqual(obs, [])

        obs = list(qdb.artifact.Artifact.iter_by_visibility('private'))
        exp = [qdb.artifact.Artifact(1),
               qdb.artifact.Artifact(2),
               qdb.artifact.Artifact(3),
               qdb.artifact.Artifact(4)]
        self.assertEqual(obs, exp)

    def test_iter_public(self):
        obs = list(qdb.artifact.Artifact.iter_public())
        exp = []
        self.assertEqual(obs, exp)

        a4 = qdb.artifact.Artifact(4)
        a4.visibility = 'public'
        obs = list(qdb.artifact.Artifact.iter_public())
        exp = [a4]
        self.assertEqual(obs, exp)

        a1 = qdb.artifact.Artifact(1)
        a1.visibility = 'public'
        obs = list(qdb.artifact.Artifact.iter_public())
        exp = [a1, a4]
        self.assertEqual(obs, exp)

    def test_copy(self):
        src = qdb.artifact.Artifact(1)
        # Create the files to the first artifact
        for _, fp, _ in src.filepaths:
            with open(fp, 'w') as f:
                f.write("\n")
            self._clean_up_files.append(fp)
        fp_count = qdb.util.get_count('qiita.filepath')
        before = datetime.now()
        obs = qdb.artifact.Artifact.copy(src, self.prep_template)

        self.assertTrue(before < obs.timestamp < datetime.now())
        self.assertIsNone(obs.processing_parameters)
        self.assertEqual(obs.visibility, 'sandbox')
        self.assertEqual(obs.artifact_type, src.artifact_type)
        self.assertEqual(obs.data_type, self.prep_template.data_type())
        self.assertEqual(obs.can_be_submitted_to_ebi,
                         src.can_be_submitted_to_ebi)
        self.assertEqual(obs.can_be_submitted_to_vamps,
                         src.can_be_submitted_to_vamps)

        db_dir = qdb.util.get_mountpoint(src.artifact_type)[0][1]
        path_builder = partial(join, db_dir, str(obs.id))
        exp_fps = []
        for fp_id, fp, fp_type in src.filepaths:
            fp_count += 1
            new_fp = path_builder(basename(fp))
            exp_fps.append((fp_count, new_fp, fp_type))
            self._clean_up_files.append(new_fp)

        self.assertEqual(obs.filepaths, exp_fps)
        self.assertEqual(obs.parents, [])
        self.assertEqual(obs.prep_templates, [self.prep_template])

        self.assertEqual(obs.study, qdb.study.Study(1))

    def test_create_error_no_filepaths(self):
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactCreationError):
            qdb.artifact.Artifact.create(
                [], "FASTQ", prep_template=self.prep_template)

    def test_create_error_prep_template_and_parents(self):
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactCreationError):
            qdb.artifact.Artifact.create(
                self.filepaths_root, "FASTQ", prep_template=self.prep_template,
                parents=[qdb.artifact.Artifact(1)])

    def test_create_error_no_prep_template_no_parents(self):
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactCreationError):
            qdb.artifact.Artifact.create(self.filepaths_root, "FASTQ")

    def test_create_error_parents_no_processing_parameters(self):
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactCreationError):
            qdb.artifact.Artifact.create(
                self.filepaths_root, "FASTQ",
                parents=[qdb.artifact.Artifact(1)])

    def test_create_error_prep_template_and_processing_parameters(self):
        parameters = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {'input_data': 1})
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactCreationError):
            qdb.artifact.Artifact.create(
                self.filepaths_root, "FASTQ", prep_template=self.prep_template,
                processing_parameters=parameters)

    def test_create_error_different_data_types(self):
        new = qdb.artifact.Artifact.create(
            self.filepaths_root, "FASTQ", prep_template=self.prep_template)
        parameters = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {'input_data': 1})
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactCreationError):
            qdb.artifact.Artifact.create(
                self.filepaths_processed, "Demultiplexed",
                parents=[qdb.artifact.Artifact(1), new],
                processing_parameters=parameters)

    def test_create_root(self):
        fp_count = qdb.util.get_count('qiita.filepath')
        before = datetime.now()
        obs = qdb.artifact.Artifact.create(
            self.filepaths_root, "FASTQ", prep_template=self.prep_template)
        self.assertTrue(before < obs.timestamp < datetime.now())
        self.assertIsNone(obs.processing_parameters)
        self.assertEqual(obs.visibility, 'sandbox')
        self.assertEqual(obs.artifact_type, "FASTQ")
        self.assertEqual(obs.data_type, self.prep_template.data_type())
        self.assertFalse(obs.can_be_submitted_to_ebi)
        self.assertFalse(obs.can_be_submitted_to_vamps)

        db_fastq_dir = qdb.util.get_mountpoint('FASTQ')[0][1]
        path_builder = partial(join, db_fastq_dir, str(obs.id))
        exp_fps = [
            (fp_count + 1, path_builder(basename(self.fp1)),
             "raw_forward_seqs"),
            (fp_count + 2, path_builder(basename(self.fp2)), "raw_barcodes"),
        ]
        self.assertEqual(obs.filepaths, exp_fps)
        self.assertEqual(obs.parents, [])
        self.assertEqual(obs.prep_templates, [self.prep_template])

        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            obs.ebi_run_accessions

        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            obs.is_submitted_to_vamps

        self.assertEqual(obs.study, qdb.study.Study(1))

    def test_create_processed(self):
        fp_count = qdb.util.get_count('qiita.filepath')
        exp_params = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {'input_data': 1})
        before = datetime.now()
        obs = qdb.artifact.Artifact.create(
            self.filepaths_processed, "Demultiplexed",
            parents=[qdb.artifact.Artifact(1)],
            processing_parameters=exp_params, can_be_submitted_to_ebi=True,
            can_be_submitted_to_vamps=True)
        self.assertTrue(before < obs.timestamp < datetime.now())
        self.assertEqual(obs.processing_parameters, exp_params)
        self.assertEqual(obs.visibility, 'sandbox')
        self.assertEqual(obs.artifact_type, "Demultiplexed")
        self.assertEqual(obs.data_type, qdb.artifact.Artifact(1).data_type)
        self.assertTrue(obs.can_be_submitted_to_ebi)
        self.assertTrue(obs.can_be_submitted_to_vamps)
        self.assertFalse(obs.is_submitted_to_vamps)

        db_demultiplexed_dir = qdb.util.get_mountpoint('Demultiplexed')[0][1]
        path_builder = partial(join, db_demultiplexed_dir, str(obs.id))
        exp_fps = [(fp_count + 1, path_builder(basename(self.fp3)),
                    "preprocessed_fasta")]
        self.assertEqual(obs.filepaths, exp_fps)
        self.assertEqual(obs.parents, [qdb.artifact.Artifact(1)])
        self.assertEqual(
            obs.prep_templates,
            [qdb.metadata_template.prep_template.PrepTemplate(1)])
        self.assertEqual(obs.ebi_run_accessions, dict())
        self.assertEqual(obs.study, qdb.study.Study(1))

    def test_create_biom(self):
        fp_count = qdb.util.get_count('qiita.filepath')
        before = datetime.now()
        cmd = qdb.software.Command(3)
        exp_params = qdb.software.Parameters.from_default_params(
            cmd.default_parameter_sets.next(), {'input_data': 1})
        obs = qdb.artifact.Artifact.create(
            self.filepaths_biom, "BIOM", parents=[qdb.artifact.Artifact(2)],
            processing_parameters=exp_params)
        self.assertTrue(before < obs.timestamp < datetime.now())
        self.assertEqual(obs.processing_parameters, exp_params)
        self.assertEqual(obs.visibility, 'sandbox')
        self.assertEqual(obs.artifact_type, 'BIOM')
        self.assertEqual(obs.data_type, qdb.artifact.Artifact(2).data_type)
        self.assertFalse(obs.can_be_submitted_to_ebi)
        self.assertFalse(obs.can_be_submitted_to_vamps)
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            obs.ebi_run_accessions

        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            obs.is_submitted_to_vamps

        db_biom_dir = qdb.util.get_mountpoint('BIOM')[0][1]
        path_builder = partial(join, db_biom_dir, str(obs.id))
        exp_fps = [(fp_count + 1, path_builder(basename(self.fp4)), 'biom')]
        self.assertEqual(obs.filepaths, exp_fps)
        self.assertEqual(obs.parents, [qdb.artifact.Artifact(2)])
        self.assertEqual(obs.prep_templates,
                         [qdb.metadata_template.prep_template.PrepTemplate(1)])
        self.assertEqual(obs.study, qdb.study.Study(1))

    def test_delete_error_public(self):
        test = qdb.artifact.Artifact.create(
            self.filepaths_root, "FASTQ", prep_template=self.prep_template)
        test.visibility = "public"
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactDeletionError):
            qdb.artifact.Artifact.delete(test.id)

    def test_delete_error_has_children(self):
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactDeletionError):
            qdb.artifact.Artifact.delete(1)

    def test_delete_error_analyzed(self):
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactDeletionError):
            qdb.artifact.Artifact.delete(4)

    def test_delete_error_ebi(self):
        parameters = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {'input_data': 1})
        obs = qdb.artifact.Artifact.create(
            self.filepaths_processed, "Demultiplexed",
            parents=[qdb.artifact.Artifact(1)],
            processing_parameters=parameters, can_be_submitted_to_ebi=True,
            can_be_submitted_to_vamps=True)
        obs.ebi_run_accessions = {'1.SKB1.640202': 'ERR1000001',
                                  '1.SKB2.640194': 'ERR1000002'}
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactDeletionError):
            qdb.artifact.Artifact.delete(obs.id)

    def test_delete_error_vamps(self):
        parameters = qdb.software.Parameters.from_default_params(
            qdb.software.DefaultParameters(1), {'input_data': 1})
        obs = qdb.artifact.Artifact.create(
            self.filepaths_processed, "Demultiplexed",
            parents=[qdb.artifact.Artifact(1)],
            processing_parameters=parameters,
            can_be_submitted_to_ebi=True, can_be_submitted_to_vamps=True)
        obs.is_submitted_to_vamps = True
        with self.assertRaises(qdb.exceptions.QiitaDBArtifactDeletionError):
            qdb.artifact.Artifact.delete(obs.id)

    def test_delete(self):
        test = qdb.artifact.Artifact.create(
            self.filepaths_root, "FASTQ", prep_template=self.prep_template)

        uploads_fp = join(qdb.util.get_mountpoint("uploads")[0][1],
                          str(test.study.id))
        self._clean_up_files.extend(
            [join(uploads_fp, basename(fp)) for _, fp, _ in test.filepaths])

        qdb.artifact.Artifact.delete(test.id)

        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.artifact.Artifact(test.id)

    def test_timestamp(self):
        self.assertEqual(qdb.artifact.Artifact(1).timestamp,
                         datetime(2012, 10, 1, 9, 30, 27))
        self.assertEqual(qdb.artifact.Artifact(2).timestamp,
                         datetime(2012, 10, 1, 10, 30, 27))
        self.assertEqual(qdb.artifact.Artifact(3).timestamp,
                         datetime(2012, 10, 1, 11, 30, 27))
        self.assertEqual(qdb.artifact.Artifact(4).timestamp,
                         datetime(2012, 10, 2, 17, 30, 00))

    def test_processing_parameters(self):
        self.assertIsNone(qdb.artifact.Artifact(1).processing_parameters)
        obs = qdb.artifact.Artifact(2).processing_parameters
        exp = qdb.software.Parameters.load(
            qdb.software.Command(1),
            values_dict={'max_barcode_errors': 1.5, 'sequence_max_n': 0,
                         'max_bad_run_length': 3, 'rev_comp': False,
                         'phred_quality_threshold': 3, 'input_data': 1,
                         'rev_comp_barcode': False,
                         'rev_comp_mapping_barcodes': False,
                         'min_per_read_length_fraction': 0.75,
                         'barcode_type': 'golay_12'})
        self.assertEqual(obs, exp)
        obs = qdb.artifact.Artifact(3).processing_parameters
        exp = qdb.software.Parameters.load(
            qdb.software.Command(1),
            values_dict={'max_barcode_errors': 1.5, 'sequence_max_n': 0,
                         'max_bad_run_length': 3, 'rev_comp': False,
                         'phred_quality_threshold': 3, 'input_data': 1,
                         'rev_comp_barcode': False,
                         'rev_comp_mapping_barcodes': True,
                         'min_per_read_length_fraction': 0.75,
                         'barcode_type': 'golay_12'})
        self.assertEqual(obs, exp)

    def test_visibility(self):
        self.assertEqual(qdb.artifact.Artifact(1).visibility, "private")

    def test_visibility_setter(self):
        a = qdb.artifact.Artifact.create(
            self.filepaths_root, "FASTQ", prep_template=self.prep_template)
        self.assertEqual(a.visibility, "sandbox")
        a.visibility = "awaiting_approval"
        self.assertEqual(a.visibility, "awaiting_approval")
        a.visibility = "private"
        self.assertEqual(a.visibility, "private")
        a.visibility = "public"
        self.assertEqual(a.visibility, "public")

    def test_artifact_type(self):
        self.assertEqual(qdb.artifact.Artifact(1).artifact_type, "FASTQ")
        self.assertEqual(qdb.artifact.Artifact(2).artifact_type,
                         "Demultiplexed")
        self.assertEqual(qdb.artifact.Artifact(3).artifact_type,
                         "Demultiplexed")
        self.assertEqual(qdb.artifact.Artifact(4).artifact_type, "BIOM")

    def test_data_type(self):
        self.assertEqual(qdb.artifact.Artifact(1).data_type, "18S")
        self.assertEqual(qdb.artifact.Artifact(2).data_type, "18S")
        self.assertEqual(qdb.artifact.Artifact(3).data_type, "18S")
        self.assertEqual(qdb.artifact.Artifact(4).data_type, "18S")

    def test_can_be_submitted_to_ebi(self):
        self.assertFalse(qdb.artifact.Artifact(1).can_be_submitted_to_ebi)
        self.assertTrue(qdb.artifact.Artifact(2).can_be_submitted_to_ebi)
        self.assertTrue(qdb.artifact.Artifact(3).can_be_submitted_to_ebi)
        self.assertFalse(qdb.artifact.Artifact(4).can_be_submitted_to_ebi)

    def test_is_submitted_to_ebi(self):
        self.assertTrue(qdb.artifact.Artifact(2).is_submitted_to_ebi)
        self.assertFalse(qdb.artifact.Artifact(3).is_submitted_to_ebi)

    def test_is_submitted_to_ebi_error(self):
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            qdb.artifact.Artifact(1).is_submitted_to_ebi
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            qdb.artifact.Artifact(4).is_submitted_to_ebi

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
        self.assertEqual(qdb.artifact.Artifact(2).ebi_run_accessions, exp)
        self.assertEqual(qdb.artifact.Artifact(3).ebi_run_accessions, dict())

    def test_ebi_run_accessions_error(self):
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            qdb.artifact.Artifact(1).ebi_run_accessions

        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            qdb.artifact.Artifact(4).ebi_run_accessions

    def test_ebi_run_accessions_setter(self):
        a = qdb.artifact.Artifact(3)
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
        self.assertFalse(qdb.artifact.Artifact(1).can_be_submitted_to_vamps)
        self.assertTrue(qdb.artifact.Artifact(2).can_be_submitted_to_vamps)
        self.assertTrue(qdb.artifact.Artifact(3).can_be_submitted_to_vamps)
        self.assertFalse(qdb.artifact.Artifact(4).can_be_submitted_to_vamps)

    def test_is_submitted_to_vamps(self):
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.assertFalse(qdb.artifact.Artifact(1).is_submitted_to_vamps)
        self.assertFalse(qdb.artifact.Artifact(2).is_submitted_to_vamps)
        self.assertFalse(qdb.artifact.Artifact(3).is_submitted_to_vamps)
        with self.assertRaises(
                qdb.exceptions.QiitaDBOperationNotPermittedError):
            self.assertFalse(qdb.artifact.Artifact(4).is_submitted_to_vamps)

    def test_is_submitted_to_vamps_setter(self):
        a = qdb.artifact.Artifact(2)
        self.assertFalse(a.is_submitted_to_vamps)
        a.is_submitted_to_vamps = True
        self.assertTrue(a.is_submitted_to_vamps)

    def test_filepaths(self):
        db_test_raw_dir = qdb.util.get_mountpoint('raw_data')[0][1]
        path_builder = partial(join, db_test_raw_dir)
        exp_fps = [
            (1, path_builder('1_s_G1_L001_sequences.fastq.gz'),
             "raw_forward_seqs"),
            (2, path_builder('1_s_G1_L001_sequences_barcodes.fastq.gz'),
             "raw_barcodes")]
        self.assertEqual(qdb.artifact.Artifact(1).filepaths, exp_fps)

    def test_parents(self):
        self.assertEqual(qdb.artifact.Artifact(1).parents, [])

        exp_parents = [qdb.artifact.Artifact(1)]
        self.assertEqual(qdb.artifact.Artifact(2).parents, exp_parents)
        self.assertEqual(qdb.artifact.Artifact(3).parents, exp_parents)

        exp_parents = [qdb.artifact.Artifact(2)]
        self.assertEqual(qdb.artifact.Artifact(4).parents, exp_parents)

    def test_create_lineage_graph_from_edge_list_empty(self):
        tester = qdb.artifact.Artifact(1)
        obs = tester._create_lineage_graph_from_edge_list([])
        self.assertTrue(isinstance(obs, nx.DiGraph))
        self.assertEqual(obs.nodes(), [tester])
        self.assertEqual(obs.edges(), [])

    def test_create_lineage_graph_from_edge_list(self):
        tester = qdb.artifact.Artifact(1)
        obs = tester._create_lineage_graph_from_edge_list(
            [(1, 2), (2, 4), (1, 3), (3, 4)])
        self.assertTrue(isinstance(obs, nx.DiGraph))
        exp = [qdb.artifact.Artifact(1), qdb.artifact.Artifact(2),
               qdb.artifact.Artifact(3), qdb.artifact.Artifact(4)]
        self.assertItemsEqual(obs.nodes(), exp)
        exp = [(qdb.artifact.Artifact(1), qdb.artifact.Artifact(2)),
               (qdb.artifact.Artifact(2), qdb.artifact.Artifact(4)),
               (qdb.artifact.Artifact(1), qdb.artifact.Artifact(3)),
               (qdb.artifact.Artifact(3), qdb.artifact.Artifact(4))]
        self.assertItemsEqual(obs.edges(), exp)

    def test_ancestors(self):
        obs = qdb.artifact.Artifact(1).ancestors
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        self.assertEqual(obs_nodes, [qdb.artifact.Artifact(1)])
        obs_edges = obs.edges()
        self.assertEqual(obs_edges, [])

        obs = qdb.artifact.Artifact(2).ancestors
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        exp_nodes = [qdb.artifact.Artifact(1), qdb.artifact.Artifact(2)]
        self.assertItemsEqual(obs_nodes, exp_nodes)
        obs_edges = obs.edges()
        exp_edges = [(qdb.artifact.Artifact(1), qdb.artifact.Artifact(2))]
        self.assertItemsEqual(obs_edges, exp_edges)

        obs = qdb.artifact.Artifact(3).ancestors
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        exp_nodes = [qdb.artifact.Artifact(1), qdb.artifact.Artifact(3)]
        self.assertItemsEqual(obs_nodes, exp_nodes)
        obs_edges = obs.edges()
        exp_edges = [(qdb.artifact.Artifact(1), qdb.artifact.Artifact(3))]
        self.assertItemsEqual(obs_edges, exp_edges)

        obs = qdb.artifact.Artifact(4).ancestors
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        exp_nodes = [qdb.artifact.Artifact(1), qdb.artifact.Artifact(2),
                     qdb.artifact.Artifact(4)]
        self.assertItemsEqual(obs_nodes, exp_nodes)
        obs_edges = obs.edges()
        exp_edges = [(qdb.artifact.Artifact(1), qdb.artifact.Artifact(2)),
                     (qdb.artifact.Artifact(2), qdb.artifact.Artifact(4))]
        self.assertItemsEqual(obs_edges, exp_edges)

    def test_descendants(self):
        obs = qdb.artifact.Artifact(1).descendants
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        exp_nodes = [qdb.artifact.Artifact(1), qdb.artifact.Artifact(2),
                     qdb.artifact.Artifact(3), qdb.artifact.Artifact(4)]
        self.assertItemsEqual(obs_nodes, exp_nodes)
        obs_edges = obs.edges()
        exp_edges = [(qdb.artifact.Artifact(1), qdb.artifact.Artifact(2)),
                     (qdb.artifact.Artifact(1), qdb.artifact.Artifact(3)),
                     (qdb.artifact.Artifact(2), qdb.artifact.Artifact(4))]
        self.assertItemsEqual(obs_edges, exp_edges)

        obs = qdb.artifact.Artifact(2).descendants
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        exp_nodes = [qdb.artifact.Artifact(2), qdb.artifact.Artifact(4)]
        self.assertItemsEqual(obs_nodes, exp_nodes)
        obs_edges = obs.edges()
        exp_edges = [(qdb.artifact.Artifact(2), qdb.artifact.Artifact(4))]
        self.assertItemsEqual(obs_edges, exp_edges)

        obs = qdb.artifact.Artifact(3).descendants
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        self.assertItemsEqual(obs_nodes, [qdb.artifact.Artifact(3)])
        obs_edges = obs.edges()
        self.assertItemsEqual(obs_edges, [])

        obs = qdb.artifact.Artifact(4).descendants
        self.assertTrue(isinstance(obs, nx.DiGraph))
        obs_nodes = obs.nodes()
        self.assertItemsEqual(obs_nodes, [qdb.artifact.Artifact(4)])
        obs_edges = obs.edges()
        self.assertItemsEqual(obs_edges, [])

    def test_children(self):
        exp = [qdb.artifact.Artifact(2), qdb.artifact.Artifact(3)]
        self.assertEqual(qdb.artifact.Artifact(1).children, exp)
        exp = [qdb.artifact.Artifact(4)]
        self.assertEqual(qdb.artifact.Artifact(2).children, exp)
        self.assertEqual(qdb.artifact.Artifact(3).children, [])
        self.assertEqual(qdb.artifact.Artifact(4).children, [])

    def test_prep_templates(self):
        self.assertEqual(
            qdb.artifact.Artifact(1).prep_templates,
            [qdb.metadata_template.prep_template.PrepTemplate(1)])
        self.assertEqual(
            qdb.artifact.Artifact(2).prep_templates,
            [qdb.metadata_template.prep_template.PrepTemplate(1)])
        self.assertEqual(
            qdb.artifact.Artifact(3).prep_templates,
            [qdb.metadata_template.prep_template.PrepTemplate(1)])
        self.assertEqual(
            qdb.artifact.Artifact(4).prep_templates,
            [qdb.metadata_template.prep_template.PrepTemplate(1)])

    def test_study(self):
        self.assertEqual(qdb.artifact.Artifact(1).study, qdb.study.Study(1))

    def test_jobs(self):
        obs = qdb.artifact.Artifact(1).jobs()
        exp = [
            qdb.processing_job.ProcessingJob(
                '6d368e16-2242-4cf8-87b4-a5dc40bb890b'),
            qdb.processing_job.ProcessingJob(
                '4c7115e8-4c8e-424c-bf25-96c292ca1931'),
            qdb.processing_job.ProcessingJob(
                '063e553b-327c-4818-ab4a-adfe58e49860'),
            qdb.processing_job.ProcessingJob(
                'bcc7ebcd-39c1-43e4-af2d-822e3589f14d'),
            qdb.processing_job.ProcessingJob(
                'b72369f9-a886-4193-8d3d-f7b504168e75')
            ]
        self.assertEqual(obs, exp)

    def test_jobs_cmd(self):
        cmd = qdb.software.Command(1)
        obs = qdb.artifact.Artifact(1).jobs(cmd=cmd)
        exp = [
            qdb.processing_job.ProcessingJob(
                '6d368e16-2242-4cf8-87b4-a5dc40bb890b'),
            qdb.processing_job.ProcessingJob(
                '4c7115e8-4c8e-424c-bf25-96c292ca1931'),
            qdb.processing_job.ProcessingJob(
                '063e553b-327c-4818-ab4a-adfe58e49860'),
            qdb.processing_job.ProcessingJob(
                'b72369f9-a886-4193-8d3d-f7b504168e75')
            ]
        self.assertEqual(obs, exp)

        cmd = qdb.software.Command(2)
        obs = qdb.artifact.Artifact(1).jobs(cmd=cmd)
        exp = [qdb.processing_job.ProcessingJob(
            'bcc7ebcd-39c1-43e4-af2d-822e3589f14d')]
        self.assertEqual(obs, exp)

    def test_jobs_status(self):
        obs = qdb.artifact.Artifact(1).jobs(status='success')
        exp = [
            qdb.processing_job.ProcessingJob(
                '6d368e16-2242-4cf8-87b4-a5dc40bb890b'),
            qdb.processing_job.ProcessingJob(
                '4c7115e8-4c8e-424c-bf25-96c292ca1931'),
            qdb.processing_job.ProcessingJob(
                'b72369f9-a886-4193-8d3d-f7b504168e75')
            ]
        self.assertEqual(obs, exp)

        obs = qdb.artifact.Artifact(1).jobs(status='running')
        exp = [qdb.processing_job.ProcessingJob(
            'bcc7ebcd-39c1-43e4-af2d-822e3589f14d')]
        self.assertEqual(obs, exp)

        obs = qdb.artifact.Artifact(1).jobs(status='queued')
        exp = [qdb.processing_job.ProcessingJob(
            '063e553b-327c-4818-ab4a-adfe58e49860')]
        self.assertEqual(obs, exp)

    def test_jobs_cmd_and_status(self):
        cmd = qdb.software.Command(1)
        obs = qdb.artifact.Artifact(1).jobs(cmd=cmd, status='success')
        exp = [
            qdb.processing_job.ProcessingJob(
                '6d368e16-2242-4cf8-87b4-a5dc40bb890b'),
            qdb.processing_job.ProcessingJob(
                '4c7115e8-4c8e-424c-bf25-96c292ca1931'),
            qdb.processing_job.ProcessingJob(
                'b72369f9-a886-4193-8d3d-f7b504168e75')
            ]
        self.assertEqual(obs, exp)

        obs = qdb.artifact.Artifact(1).jobs(cmd=cmd, status='queued')
        exp = [qdb.processing_job.ProcessingJob(
            '063e553b-327c-4818-ab4a-adfe58e49860')]
        self.assertEqual(obs, exp)

        cmd = qdb.software.Command(2)
        obs = qdb.artifact.Artifact(1).jobs(cmd=cmd, status='queued')
        exp = []
        self.assertEqual(obs, exp)

if __name__ == '__main__':
    main()
