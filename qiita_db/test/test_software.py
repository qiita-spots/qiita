# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
import qiita_db as qdb


@qiita_test_checker()
class CommandTests(TestCase):
    def setUp(self):
        self.software = qdb.software.Software(1)

    def test_exists(self):
        self.assertFalse(qdb.software.Command.exists(
            self.software, "donotexists"))
        self.assertTrue(qdb.software.Command.exists(
            self.software, "split_libraries.py"))

    def test_create_error_duplicate(self):
        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateError):
            qdb.software.Command.create(
                self.software, "Test Command", "This is a command for testing",
                "split_libraries.py", "preprocessed_spectra_params")

    def test_create(self):
        obs = qdb.software.Command.create(
            self.software, "Test Command", "This is a command for testing",
            "test_command.py", "preprocessed_spectra_params")
        self.assertEqual(obs.name, "Test Command")
        self.assertEqual(obs.description, "This is a command for testing")
        self.assertEqual(obs.cli, "test_command.py")
        self.assertEqual(obs.parameters_table, "preprocessed_spectra_params")

    def test_name(self):
        self.assertEqual(qdb.software.Command(1).name, "Split libraries FASTQ")
        self.assertEqual(qdb.software.Command(2).name, "Split libraries")

    def test_description(self):
        self.assertEqual(
            qdb.software.Command(1).description,
            "Demultiplexes and applies quality control to FASTQ data")
        self.assertEqual(
            qdb.software.Command(2).description,
            "Demultiplexes and applies quality control to FASTA data")

    def test_cli(self):
        self.assertEqual(qdb.software.Command(1).cli,
                         "split_libraries_fastq.py")
        self.assertEqual(qdb.software.Command(2).cli, "split_libraries.py")

    def test_parameters_table(self):
        self.assertEqual(qdb.software.Command(1).parameters_table,
                         "preprocessed_sequence_illumina_params")
        self.assertEqual(qdb.software.Command(2).parameters_table,
                         "preprocessed_sequence_454_params")


@qiita_test_checker()
class SoftwareTests(TestCase):
    def test_create(self):
        obs = qdb.software.Software.create(
            "New Software", "0.1.0",
            "This is adding a new software for testing")
        self.assertEqual(obs.name, "New Software")
        self.assertEqual(obs.version, "0.1.0")
        self.assertEqual(obs.description,
                         "This is adding a new software for testing")
        self.assertEqual(obs.commands, [])
        self.assertEqual(obs.publications, [])

    def test_create_with_publications(self):
        exp_publications = [['10.1000/nmeth.f.101', '12345678']]
        obs = qdb.software.Software.create(
            "Published Software", "1.0.0", "Another testing software",
            publications=exp_publications)
        self.assertEqual(obs.name, "Published Software")
        self.assertEqual(obs.version, "1.0.0")
        self.assertEqual(obs.description, "Another testing software")
        self.assertEqual(obs.commands, [])
        self.assertEqual(obs.publications, exp_publications)

    def test_name(self):
        self.assertEqual(qdb.software.Software(1).name, "QIIME")

    def test_version(self):
        self.assertEqual(qdb.software.Software(1).version, "1.9.1")

    def test_description(self):
        exp = ("Quantitative Insights Into Microbial Ecology (QIIME) is an "
               "open-source bioinformatics pipeline for performing microbiome "
               "analysis from raw DNA sequencing data")
        self.assertEqual(qdb.software.Software(1).description, exp)

    def test_commands(self):
        exp = [qdb.software.Command(1), qdb.software.Command(2),
               qdb.software.Command(3)]
        self.assertEqual(qdb.software.Software(1).commands, exp)

    def test_publications(self):
        self.assertEqual(qdb.software.Software(1).publications,
                         [['10.1038/nmeth.f.303', '20383131']])

    def test_add_publications(self):
        tester = qdb.software.Software(1)
        self.assertEqual(tester.publications,
                         [['10.1038/nmeth.f.303', '20383131']])
        tester.add_publications([['10.1000/nmeth.f.101', '12345678']])
        exp = [['10.1038/nmeth.f.303', '20383131'],
               ['10.1000/nmeth.f.101', '12345678']]
        self.assertItemsEqual(tester.publications, exp)


@qiita_test_checker()
class ParametersTests(TestCase):
    def test_init(self):
        obs = qdb.software.Parameters(1, qdb.software.Command(1))
        self.assertEqual(obs.id, 1)
        self.assertEqual(obs._table, "preprocessed_sequence_illumina_params")
        self.assertEqual(obs.command, qdb.software.Command(1))

    def test_exists(self):
        cmd = qdb.software.Command(1)
        obs = qdb.software.Parameters.exists(
            cmd, max_bad_run_length=3, min_per_read_length_fraction=0.75,
            sequence_max_n=0, rev_comp_barcode=False,
            rev_comp_mapping_barcodes=False, rev_comp=False,
            phred_quality_threshold=3, barcode_type="golay_12",
            max_barcode_errors=1.5)
        self.assertTrue(obs)

        obs = qdb.software.Parameters.exists(
            cmd, max_bad_run_length=3, min_per_read_length_fraction=0.75,
            sequence_max_n=0, rev_comp_barcode=False,
            rev_comp_mapping_barcodes=False, rev_comp=False,
            phred_quality_threshold=3, barcode_type="hamming_8",
            max_barcode_errors=1.5)
        self.assertFalse(obs)

    def test_create(self):
        cmd = qdb.software.Command(1)
        obs = qdb.software.Parameters.create(
            "test_create", cmd, max_bad_run_length=3,
            min_per_read_length_fraction=0.75, sequence_max_n=0,
            rev_comp_barcode=False, rev_comp_mapping_barcodes=False,
            rev_comp=False, phred_quality_threshold=3,
            barcode_type="hamming_8", max_barcode_errors=1.5)
        self.assertEqual(obs.name, "test_create")

        exp = {'max_bad_run_length': 3, 'min_per_read_length_fraction': 0.75,
               'sequence_max_n': 0, 'rev_comp_barcode': False,
               'rev_comp_mapping_barcodes': False, 'rev_comp': False,
               'phred_quality_threshold': 3, 'barcode_type': "hamming_8",
               'max_barcode_errors': 1.5}
        self.assertEqual(obs.values, exp)

        self.assertEqual(obs.command, cmd)

    def test_iter(self):
        cmd = qdb.software.Command(1)
        obs = list(qdb.software.Parameters.iter(cmd))
        exp = [qdb.software.Parameters(i, cmd) for i in range(1, 8)]
        self.assertEqual(obs, exp)

    def test_name(self):
        self.assertEqual(
            qdb.software.Parameters(1, qdb.software.Command(1)).name,
            "Defaults")

    def test_values(self):
        exp = {'min_per_read_length_fraction': 0.75,
               'max_barcode_errors': 1.5, 'max_bad_run_length': 3,
               'rev_comp': False, 'phred_quality_threshold': 3,
               'rev_comp_barcode': False, 'sequence_max_n': 0,
               'barcode_type': 'golay_12', 'rev_comp_mapping_barcodes': False}
        self.assertEqual(
            qdb.software.Parameters(1, qdb.software.Command(1)).values, exp)

    def test_to_str(self):
        exp = ("--barcode_type 'golay_12' --max_bad_run_length '3' "
               "--max_barcode_errors '1.5' "
               "--min_per_read_length_fraction '0.75' "
               "--phred_quality_threshold '3' --sequence_max_n '0'")
        self.assertEqual(
            qdb.software.Parameters(1, qdb.software.Command(1)).to_str(), exp)

    def test_command(self):
        self.assertEqual(
            qdb.software.Parameters(1, qdb.software.Command(1)).command,
            qdb.software.Command(1))

if __name__ == '__main__':
    main()
