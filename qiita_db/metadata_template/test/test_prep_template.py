# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from collections import Iterable
from copy import deepcopy
from datetime import datetime
from os import close, remove
from os.path import exists, join
from tempfile import mkstemp
from unittest import TestCase, main

import numpy.testing as npt
import pandas as pd
from pandas.testing import assert_frame_equal

import qiita_db as qdb
from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.util import qiita_test_checker


@qiita_test_checker()
class TestPrepSample(TestCase):
    def setUp(self):
        self.prep_template = qdb.metadata_template.prep_template.PrepTemplate(1)
        self.sample_id = "1.SKB8.640193"
        self.tester = qdb.metadata_template.prep_template.PrepSample(
            self.sample_id, self.prep_template
        )
        self.exp_categories = {
            "center_name",
            "center_project_name",
            "emp_status",
            "barcode",
            "instrument_model",
            "library_construction_protocol",
            "primer",
            "target_subfragment",
            "target_gene",
            "run_center",
            "run_prefix",
            "run_date",
            "experiment_center",
            "experiment_design_description",
            "experiment_title",
            "platform",
            "samp_size",
            "sequencing_meth",
            "illumina_technology",
            "sample_center",
            "pcr_primers",
            "study_center",
        }

    def test_init_unknown_error(self):
        """Init errors if the PrepSample id is not found in the template"""
        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.metadata_template.prep_template.PrepSample(
                "Not_a_Sample", self.prep_template
            )

    def test_init_wrong_template(self):
        """Raises an error if using a SampleTemplate instead of PrepTemplate"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKB8.640193", qdb.metadata_template.sample_template.SampleTemplate(1)
            )

    def test_init(self):
        """Init correctly initializes the PrepSample object"""
        sample = qdb.metadata_template.prep_template.PrepSample(
            self.sample_id, self.prep_template
        )
        # Check that the internal id have been correctly set
        self.assertEqual(sample._id, "1.SKB8.640193")
        # Check that the internal template have been correctly set
        self.assertEqual(sample._md_template, self.prep_template)
        # Check that the internal dynamic table name have been correctly set
        self.assertEqual(sample._dynamic_table, "prep_1")

    def test_eq_true(self):
        """Equality correctly returns true"""
        other = qdb.metadata_template.prep_template.PrepSample(
            self.sample_id, self.prep_template
        )
        self.assertTrue(self.tester == other)

    def test_eq_false_type(self):
        """Equality returns false if types are not equal"""
        other = qdb.metadata_template.sample_template.Sample(
            self.sample_id, qdb.metadata_template.sample_template.SampleTemplate(1)
        )
        self.assertFalse(self.tester == other)

    def test_eq_false_id(self):
        """Equality returns false if ids are different"""
        other = qdb.metadata_template.prep_template.PrepSample(
            "1.SKD8.640184", self.prep_template
        )
        self.assertFalse(self.tester == other)

    def test_exists_true(self):
        """Exists returns true if the PrepSample exists"""
        self.assertTrue(
            qdb.metadata_template.prep_template.PrepSample.exists(
                self.sample_id, self.prep_template
            )
        )

    def test_exists_false(self):
        """Exists returns false if the PrepSample does not exists"""
        self.assertFalse(
            qdb.metadata_template.prep_template.PrepSample.exists(
                "Not_a_Sample", self.prep_template
            )
        )

    def test_get_categories(self):
        """Correctly returns the set of category headers"""
        obs = self.tester._get_categories()
        self.assertEqual(obs, self.exp_categories)

    def test_len(self):
        """Len returns the correct number of categories"""
        self.assertEqual(len(self.tester), 22)

    def test_getitem_required(self):
        """Get item returns the correct metadata value from the required table"""
        self.assertEqual(self.tester["center_name"], "ANL")
        self.assertTrue(self.tester["center_project_name"] is None)

    def test_getitem_dynamic(self):
        """Get item returns the correct metadata value from the dynamic table"""
        self.assertEqual(
            self.tester["pcr_primers"],
            "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT",
        )
        self.assertEqual(self.tester["barcode"], "AGCGCTCACATC")

    def test_getitem_id_column(self):
        """Get item returns the correct metadata value from the changed column"""
        self.assertEqual(self.tester["emp_status"], "EMP")

    def test_getitem_error(self):
        """Get item raises an error if category does not exists"""
        with self.assertRaises(KeyError):
            self.tester["Not_a_Category"]

    def test_iter(self):
        """iter returns an iterator over the category headers"""
        obs = self.tester.__iter__()
        self.assertTrue(isinstance(obs, Iterable))
        self.assertEqual(set(obs), self.exp_categories)

    def test_contains_true(self):
        """contains returns true if the category header exists"""
        self.assertTrue("Barcode" in self.tester)
        self.assertTrue("barcode" in self.tester)

    def test_contains_false(self):
        """contains returns false if the category header does not exists"""
        self.assertFalse("Not_a_Category" in self.tester)

    def test_keys(self):
        """keys returns an iterator over the metadata headers"""
        obs = self.tester.keys()
        self.assertTrue(isinstance(obs, Iterable))
        self.assertEqual(set(obs), self.exp_categories)

    def test_values(self):
        """values returns an iterator over the values"""
        obs = self.tester.values()
        self.assertTrue(isinstance(obs, Iterable))
        exp = {
            "ANL",
            None,
            None,
            None,
            "EMP",
            "AGCGCTCACATC",
            "This analysis was done as in Caporaso et al 2011 Genome "
            "research. The PCR primers (F515/R806) were developed against "
            "the V4 region of the 16S rRNA (both bacteria and archaea), "
            "which we determined would yield optimal community clustering "
            "with reads of this length using a procedure similar to that of"
            " ref. 15. [For reference, this primer pair amplifies the "
            "region 533_786 in the Escherichia coli strain 83972 sequence "
            "(greengenes accession no. prokMSA_id:470367).] The reverse PCR"
            " primer is barcoded with a 12-base error-correcting Golay code"
            " to facilitate multiplexing of up to 1,500 samples per lane, "
            "and both PCR primers contain sequencer adapter regions.",
            "GTGCCAGCMGCCGCGGTAA",
            "V4",
            "16S rRNA",
            "ANL",
            "s_G1_L001_sequences",
            "8/1/12",
            "ANL",
            "micro biome of soil and rhizosphere of cannabis plants from CA",
            "Cannabis Soil Microbiome",
            "Illumina",
            "Illumina MiSeq",
            ".25,g",
            "Sequencing by synthesis",
            "MiSeq",
            "ANL",
            "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT",
            "CCME",
        }
        self.assertEqual(set(obs), exp)

    def test_items(self):
        """items returns an iterator over the (key, value) tuples"""
        obs = self.tester.items()
        self.assertTrue(isinstance(obs, Iterable))
        exp = {
            ("center_name", "ANL"),
            ("center_project_name", None),
            ("emp_status", "EMP"),
            ("barcode", "AGCGCTCACATC"),
            (
                "library_construction_protocol",
                "This analysis was done as in Caporaso et al 2011 Genome "
                "research. The PCR primers (F515/R806) were developed against "
                "the V4 region of the 16S rRNA (both bacteria and archaea), "
                "which we determined would yield optimal community clustering "
                "with reads of this length using a procedure similar to that "
                "of ref. 15. [For reference, this primer pair amplifies the "
                "region 533_786 in the Escherichia coli strain 83972 sequence "
                "(greengenes accession no. prokMSA_id:470367).] The reverse "
                "PCR primer is barcoded with a 12-base error-correcting Golay "
                "code to facilitate multiplexing of up to 1,500 samples per "
                "lane, and both PCR primers contain sequencer adapter "
                "regions.",
            ),
            ("primer", "GTGCCAGCMGCCGCGGTAA"),
            ("target_subfragment", "V4"),
            ("target_gene", "16S rRNA"),
            ("run_center", "ANL"),
            ("run_prefix", "s_G1_L001_sequences"),
            ("run_date", "8/1/12"),
            ("experiment_center", "ANL"),
            (
                "experiment_design_description",
                "micro biome of soil and rhizosphere of cannabis plants from CA",
            ),
            ("experiment_title", "Cannabis Soil Microbiome"),
            ("platform", "Illumina"),
            ("instrument_model", "Illumina MiSeq"),
            ("samp_size", ".25,g"),
            ("sequencing_meth", "Sequencing by synthesis"),
            ("illumina_technology", "MiSeq"),
            ("sample_center", "ANL"),
            ("pcr_primers", "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT"),
            ("study_center", "CCME"),
        }
        self.assertEqual(set(obs), exp)

    def test_get(self):
        """get returns the correct sample object"""
        self.assertEqual(self.tester.get("barcode"), "AGCGCTCACATC")

    def test_get_none(self):
        """get returns none if the sample id is not present"""
        self.assertTrue(self.tester.get("Not_a_Category") is None)

    def test_columns_restrictions(self):
        """that it returns SAMPLE_TEMPLATE_COLUMNS"""
        exp = deepcopy(qdb.metadata_template.constants.PREP_TEMPLATE_COLUMNS)
        exp.update(qdb.metadata_template.constants.PREP_TEMPLATE_COLUMNS_TARGET_GENE)
        self.assertEqual(self.prep_template.columns_restrictions, exp)

    def test_can_be_updated(self):
        """test if the template can be updated"""
        # you can't update restricted colums in a pt with data
        self.assertFalse(self.prep_template.can_be_updated({"barcode"}))
        # but you can if not restricted
        self.assertTrue(self.prep_template.can_be_updated({"center_name"}))

    def test_can_be_extended(self):
        """test if the template can be extended"""
        # You can always add columns
        obs_bool, obs_msg = self.prep_template.can_be_extended([], ["NEW_COL"])
        self.assertTrue(obs_bool)
        self.assertEqual(obs_msg, "")
        # You can't add samples if there are preprocessed data generated
        obs_bool, obs_msg = self.prep_template.can_be_extended(["NEW_SAMPLE"], [])
        self.assertFalse(obs_bool)
        exp_msg = (
            "The artifact attached to the prep template has already "
            "been processed. No new samples can be added to the prep "
            "template"
        )
        self.assertEqual(obs_msg, exp_msg)

    def test_can_be_extended_duplicated_column(self):
        """test if the template can be extended"""
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            self.prep_template.can_be_extended([], ["season_environment"])

    def test_metadata_headers(self):
        PT = qdb.metadata_template.prep_template.PrepTemplate
        obs = PT.metadata_headers()
        exp = [
            "barcode",
            "center_name",
            "center_project_name",
            "emp_status",
            "experiment_center",
            "experiment_design_description",
            "experiment_title",
            "illumina_technology",
            "instrument_model",
            "library_construction_protocol",
            "pcr_primers",
            "platform",
            "primer",
            "run_center",
            "run_date",
            "run_prefix",
            "samp_size",
            "sample_center",
            "sequencing_meth",
            "study_center",
            "target_gene",
            "target_subfragment",
        ]
        self.assertCountEqual(obs, exp)

    def test_setitem(self):
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            self.tester["column that does not exist"] = 0.3

        tester = qdb.metadata_template.prep_template.PrepSample(
            "1.SKD8.640184", self.prep_template
        )

        self.assertEqual(tester["center_name"], "ANL")
        tester["center_name"] = "FOO"
        self.assertEqual(tester["center_name"], "FOO")

    def test_delitem(self):
        """delitem raises an error (currently not allowed)"""
        with self.assertRaises(qdb.exceptions.QiitaDBNotImplementedError):
            del self.tester["pcr_primers"]


@qiita_test_checker()
class TestPrepTemplate(TestCase):
    def setUp(self):
        # qdb.metadata_template.base_metadata_template.QIITA_COLUMN_NAME is
        # the name of the sample where we store all columns for a sample/prep
        # information and in this tests we want to avoid having to import it
        # in different places so adding to the setUp
        self.QCN = qdb.metadata_template.base_metadata_template.QIITA_COLUMN_NAME
        self.metadata_dict = {
            "SKB8.640193": {
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "ebi_submission_accession": None,
                "EMP_status": "EMP",
                "str_column": "Value for sample 1",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "barcode": "GTCCGCAAGTTA",
                "run_prefix": "s_G1_L001_sequences",
                "platform": "Illumina",
                "qiita_prep_id": 1000,
                "instrument_model": "Illumina MiSeq",
                "library_construction_protocol": "AAAA",
                "insdc_nulls": "3.6",
                "experiment_design_description": "BBBB",
            },
            "SKD8.640184": {
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "ebi_submission_accession": None,
                "EMP_status": "EMP",
                "str_column": "Value for sample 2",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "barcode": "CGTAGAGCTCTC",
                "run_prefix": "s_G1_L001_sequences",
                "platform": "Illumina",
                "qiita_prep_id": 1000,
                "instrument_model": "Illumina MiSeq",
                "library_construction_protocol": "AAAA",
                "insdc_nulls": "NoT applicable",
                "experiment_design_description": "BBBB",
            },
            "SKB7.640196": {
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "ebi_submission_accession": None,
                "EMP_status": "EMP",
                "str_column": "Value for sample 3",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "barcode": "CCTCTGAGAGCT",
                "run_prefix": "s_G1_L002_sequences",
                "platform": "Illumina",
                "qiita_prep_id": 1000,
                "instrument_model": "Illumina MiSeq",
                "library_construction_protocol": "AAAA",
                "insdc_nulls": "unspecified",
                "experiment_design_description": "BBBB",
            },
        }
        self.metadata = pd.DataFrame.from_dict(
            self.metadata_dict, orient="index", dtype=str
        )

        metadata_prefixed_dict = {
            "1.SKB8.640193": {
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "ebi_submission_accession": None,
                "EMP_status": "EMP",
                "str_column": "Value for sample 1",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "barcode": "GTCCGCAAGTTA",
                "run_prefix": "s_G1_L001_sequences",
                "platform": "Illumina",
                "qiita_prep_id": 1000,
                "instrument_model": "Illumina MiSeq",
                "library_construction_protocol": "AAAA",
                "insdc_nulls": "3.6",
                "experiment_design_description": "BBBB",
            },
            "1.SKD8.640184": {
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "ebi_submission_accession": None,
                "EMP_status": "EMP",
                "str_column": "Value for sample 2",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "barcode": "CGTAGAGCTCTC",
                "run_prefix": "s_G1_L001_sequences",
                "platform": "Illumina",
                "qiita_prep_id": 1000,
                "instrument_model": "Illumina MiSeq",
                "library_construction_protocol": "AAAA",
                "insdc_nulls": "not applicable",
                "experiment_design_description": "BBBB",
            },
            "1.SKB7.640196": {
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "ebi_submission_accession": None,
                "EMP_status": "EMP",
                "str_column": "Value for sample 3",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "barcode": "CCTCTGAGAGCT",
                "run_prefix": "s_G1_L002_sequences",
                "platform": "Illumina",
                "qiita_prep_id": 1000,
                "instrument_model": "Illumina MiSeq",
                "library_construction_protocol": "AAAA",
                "insdc_nulls": "not applicable",
                "experiment_design_description": "BBBB",
            },
        }
        self.metadata_prefixed = pd.DataFrame.from_dict(
            metadata_prefixed_dict, orient="index"
        )

        self.test_study = qdb.study.Study(1)
        self.data_type = "18S"
        self.data_type_id = 2

        self.tester = qdb.metadata_template.prep_template.PrepTemplate(1)
        self.exp_sample_ids = {
            "1.SKB1.640202",
            "1.SKB2.640194",
            "1.SKB3.640195",
            "1.SKB4.640189",
            "1.SKB5.640181",
            "1.SKB6.640176",
            "1.SKB7.640196",
            "1.SKB8.640193",
            "1.SKB9.640200",
            "1.SKD1.640179",
            "1.SKD2.640178",
            "1.SKD3.640198",
            "1.SKD4.640185",
            "1.SKD5.640186",
            "1.SKD6.640190",
            "1.SKD7.640191",
            "1.SKD8.640184",
            "1.SKD9.640182",
            "1.SKM1.640183",
            "1.SKM2.640199",
            "1.SKM3.640197",
            "1.SKM4.640180",
            "1.SKM5.640177",
            "1.SKM6.640187",
            "1.SKM7.640188",
            "1.SKM8.640201",
            "1.SKM9.640192",
        }

        # Generate some files for new artifact
        fd, fp1 = mkstemp(suffix="_seqs.fastq")
        close(fd)
        with open(fp1, "w") as f:
            f.write(
                "@HWI-ST753:189:D1385ACXX:1:1101:1214:1906 1:N:0:\n"
                "NACGTAGGGTGCAAGCGTTGTCCGGAATNA\n"
                "+\n"
                "#1=DDFFFHHHHHJJJJJJJJJJJJGII#0\n"
            )
        fd, fp2 = mkstemp(suffix="_barcodes.fastq")
        close(fd)
        with open(fp2, "w") as f:
            f.write(
                "@HWI-ST753:189:D1385ACXX:1:1101:1214:1906 2:N:0:\n"
                "NNNCNNNNNNNNN\n"
                "+\n"
                "#############\n"
            )
        self.filepaths = [(fp1, 1), (fp2, 3)]
        self._clean_up_files = [fp1, fp2]

    def tearDown(self):
        for f in self._clean_up_files:
            if exists(f):
                remove(f)

    def test_study_id(self):
        """Ensure that the correct study ID is returned"""
        self.assertEqual(self.tester.study_id, 1)

    def test_init_unknown_error(self):
        """Init raises an error if the id is not known"""
        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.metadata_template.prep_template.PrepTemplate(30000)

    def test_init(self):
        """Init successfully instantiates the object"""
        st = qdb.metadata_template.prep_template.PrepTemplate(1)
        self.assertTrue(st.id, 1)

    def test_unique_ids(self):
        obs = self.tester.unique_ids()
        exp = {name: idx for idx, name in enumerate(sorted(self.tester.keys()), 1)}
        self.assertEqual(obs, exp)

        # verify a repeat call is unchanged
        obs = self.tester.unique_ids()
        self.assertEqual(obs, exp)

    def test_table_name(self):
        """Table name return the correct string"""
        obs = qdb.metadata_template.prep_template.PrepTemplate._table_name(1)
        self.assertEqual(obs, "prep_1")

    def test_exists_true(self):
        """Exists returns true when the PrepTemplate already exists"""
        self.assertTrue(qdb.metadata_template.prep_template.PrepTemplate.exists(1))

    def test_exists_false(self):
        """Exists returns false when the PrepTemplate does not exists"""
        self.assertFalse(qdb.metadata_template.prep_template.PrepTemplate.exists(30000))

    def test_get_sample_ids(self):
        """get_sample_ids returns the correct set of sample ids"""
        obs = self.tester._get_sample_ids()
        self.assertEqual(obs, self.exp_sample_ids)

    def test_len(self):
        """Len returns the correct number of sample ids"""
        self.assertEqual(len(self.tester), 27)

    def test_getitem(self):
        """Get item returns the correct sample object"""
        obs = self.tester["1.SKM7.640188"]
        exp = qdb.metadata_template.prep_template.PrepSample(
            "1.SKM7.640188", self.tester
        )
        self.assertEqual(obs, exp)

    def test_getitem_error(self):
        """Get item raises an error if key does not exists"""
        with self.assertRaises(KeyError):
            self.tester["Not_a_Sample"]

    def test_iter(self):
        """iter returns an iterator over the sample ids"""
        obs = self.tester.__iter__()
        self.assertTrue(isinstance(obs, Iterable))
        self.assertEqual(set(obs), self.exp_sample_ids)

    def test_contains_true(self):
        """contains returns true if the sample id exists"""
        self.assertTrue("1.SKM7.640188" in self.tester)

    def test_contains_false(self):
        """contains returns false if the sample id does not exists"""
        self.assertFalse("Not_a_Sample" in self.tester)

    def test_keys(self):
        """keys returns an iterator over the sample ids"""
        obs = self.tester.keys()
        self.assertTrue(isinstance(obs, Iterable))
        self.assertEqual(set(obs), self.exp_sample_ids)

    def test_values(self):
        """values returns an iterator over the values"""
        obs = self.tester.values()
        self.assertTrue(isinstance(obs, Iterable))
        exp = {
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKB1.640202", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKB2.640194", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKB3.640195", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKB4.640189", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKB5.640181", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKB6.640176", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKB7.640196", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKB8.640193", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKB9.640200", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKD1.640179", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKD2.640178", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKD3.640198", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKD4.640185", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKD5.640186", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKD6.640190", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKD7.640191", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKD8.640184", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKD9.640182", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKM1.640183", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKM2.640199", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKM3.640197", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKM4.640180", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKM5.640177", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKM6.640187", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKM7.640188", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKM8.640201", self.tester
            ),
            qdb.metadata_template.prep_template.PrepSample(
                "1.SKM9.640192", self.tester
            ),
        }
        # Creating a list and looping over it since unittest does not call
        # the __eq__ function on the objects
        for o, e in zip(
            sorted(list(obs), key=lambda x: x.id), sorted(exp, key=lambda x: x.id)
        ):
            self.assertEqual(o, e)

    def test_items(self):
        """items returns an iterator over the (key, value) tuples"""
        obs = self.tester.items()
        self.assertTrue(isinstance(obs, Iterable))
        exp = [
            (
                "1.SKB1.640202",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKB1.640202", self.tester
                ),
            ),
            (
                "1.SKB2.640194",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKB2.640194", self.tester
                ),
            ),
            (
                "1.SKB3.640195",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKB3.640195", self.tester
                ),
            ),
            (
                "1.SKB4.640189",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKB4.640189", self.tester
                ),
            ),
            (
                "1.SKB5.640181",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKB5.640181", self.tester
                ),
            ),
            (
                "1.SKB6.640176",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKB6.640176", self.tester
                ),
            ),
            (
                "1.SKB7.640196",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKB7.640196", self.tester
                ),
            ),
            (
                "1.SKB8.640193",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKB8.640193", self.tester
                ),
            ),
            (
                "1.SKB9.640200",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKB9.640200", self.tester
                ),
            ),
            (
                "1.SKD1.640179",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKD1.640179", self.tester
                ),
            ),
            (
                "1.SKD2.640178",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKD2.640178", self.tester
                ),
            ),
            (
                "1.SKD3.640198",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKD3.640198", self.tester
                ),
            ),
            (
                "1.SKD4.640185",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKD4.640185", self.tester
                ),
            ),
            (
                "1.SKD5.640186",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKD5.640186", self.tester
                ),
            ),
            (
                "1.SKD6.640190",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKD6.640190", self.tester
                ),
            ),
            (
                "1.SKD7.640191",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKD7.640191", self.tester
                ),
            ),
            (
                "1.SKD8.640184",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKD8.640184", self.tester
                ),
            ),
            (
                "1.SKD9.640182",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKD9.640182", self.tester
                ),
            ),
            (
                "1.SKM1.640183",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKM1.640183", self.tester
                ),
            ),
            (
                "1.SKM2.640199",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKM2.640199", self.tester
                ),
            ),
            (
                "1.SKM3.640197",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKM3.640197", self.tester
                ),
            ),
            (
                "1.SKM4.640180",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKM4.640180", self.tester
                ),
            ),
            (
                "1.SKM5.640177",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKM5.640177", self.tester
                ),
            ),
            (
                "1.SKM6.640187",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKM6.640187", self.tester
                ),
            ),
            (
                "1.SKM7.640188",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKM7.640188", self.tester
                ),
            ),
            (
                "1.SKM8.640201",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKM8.640201", self.tester
                ),
            ),
            (
                "1.SKM9.640192",
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKM9.640192", self.tester
                ),
            ),
        ]
        # Creating a list and looping over it since unittest does not call
        # the __eq__ function on the objects
        for o, e in zip(sorted(list(obs)), sorted(exp)):
            self.assertEqual(o, e)

    def test_get(self):
        """get returns the correct PrepSample object"""
        obs = self.tester.get("1.SKM7.640188")
        exp = qdb.metadata_template.prep_template.PrepSample(
            "1.SKM7.640188", self.tester
        )
        self.assertEqual(obs, exp)

    def test_get_none(self):
        """get returns none if the sample id is not present"""
        self.assertTrue(self.tester.get("Not_a_Sample") is None)

    def test_data_type(self):
        """data_type returns the string with the data_type"""
        self.assertTrue(self.tester.data_type(), "18S")

    def test_data_type_id(self):
        """data_type returns the int with the data_type_id"""
        self.assertTrue(self.tester.data_type(ret_id=True), 2)

    def test_investigation_type(self):
        """investigation_type works correctly"""
        self.assertEqual(self.tester.investigation_type, "Metagenomics")

    def test_to_dataframe(self):
        obs = self.tester.to_dataframe()
        # We don't test the specific values as this would blow up the size
        # of this file as the amount of lines would go to ~1000

        # 27 samples
        self.assertEqual(len(obs), 27)
        self.assertEqual(
            set(obs.index),
            {
                "1.SKB1.640202",
                "1.SKB2.640194",
                "1.SKB3.640195",
                "1.SKB4.640189",
                "1.SKB5.640181",
                "1.SKB6.640176",
                "1.SKB7.640196",
                "1.SKB8.640193",
                "1.SKB9.640200",
                "1.SKD1.640179",
                "1.SKD2.640178",
                "1.SKD3.640198",
                "1.SKD4.640185",
                "1.SKD5.640186",
                "1.SKD6.640190",
                "1.SKD7.640191",
                "1.SKD8.640184",
                "1.SKD9.640182",
                "1.SKM1.640183",
                "1.SKM2.640199",
                "1.SKM3.640197",
                "1.SKM4.640180",
                "1.SKM5.640177",
                "1.SKM6.640187",
                "1.SKM7.640188",
                "1.SKM8.640201",
                "1.SKM9.640192",
            },
        )

        self.assertEqual(
            set(obs.columns),
            {
                "center_name",
                "center_project_name",
                "emp_status",
                "barcode",
                "library_construction_protocol",
                "primer",
                "target_subfragment",
                "target_gene",
                "run_center",
                "run_prefix",
                "run_date",
                "experiment_center",
                "experiment_design_description",
                "experiment_title",
                "platform",
                "instrument_model",
                "samp_size",
                "sequencing_meth",
                "illumina_technology",
                "sample_center",
                "pcr_primers",
                "study_center",
                "qiita_prep_id",
            },
        )

        # test with add_ebi_accessions as True
        obs = self.tester.to_dataframe(True)
        self.assertEqual(
            self.tester.ebi_experiment_accessions,
            obs.qiita_ebi_experiment_accessions.to_dict(),
        )

    def test_clean_validate_template_error_bad_chars(self):
        """Raises an error if there are invalid characters in the sample names"""
        self.metadata.index = ["o()xxxx[{::::::::>", "sample.1", "sample.3"]
        PT = qdb.metadata_template.prep_template.PrepTemplate
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            PT._clean_validate_template(self.metadata, 2)

    def test_clean_validate_template_error_duplicate_cols(self):
        """Raises an error if there are duplicated columns in the template"""
        self.metadata["STR_COLUMN"] = pd.Series(["", "", ""], index=self.metadata.index)
        PT = qdb.metadata_template.prep_template.PrepTemplate
        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateHeaderError):
            PT._clean_validate_template(self.metadata, 2)

    def test_clean_validate_template_error_duplicate_samples(self):
        """Raises an error if there are duplicated samples in the templates"""
        self.metadata.index = ["sample.1", "sample.1", "sample.3"]
        PT = qdb.metadata_template.prep_template.PrepTemplate
        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateSamplesError):
            PT._clean_validate_template(self.metadata, 2)

    def test_clean_validate_template(self):
        PT = qdb.metadata_template.prep_template.PrepTemplate
        # modify input to make sure we hit all cases
        md = self.metadata.copy()
        md.loc["SKB7.640196"]["str_column"] = "UnSpeciFied"
        obs = PT._clean_validate_template(md, 2)
        metadata_dict = {
            "2.SKB8.640193": {
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "ebi_submission_accession": None,
                "emp_status": "EMP",
                "str_column": "Value for sample 1",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "barcode": "GTCCGCAAGTTA",
                "run_prefix": "s_G1_L001_sequences",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "library_construction_protocol": "AAAA",
                "insdc_nulls": "3.6",
                "experiment_design_description": "BBBB",
            },
            "2.SKD8.640184": {
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "ebi_submission_accession": None,
                "emp_status": "EMP",
                "str_column": "Value for sample 2",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "barcode": "CGTAGAGCTCTC",
                "run_prefix": "s_G1_L001_sequences",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "library_construction_protocol": "AAAA",
                "insdc_nulls": "not applicable",
                "experiment_design_description": "BBBB",
            },
            "2.SKB7.640196": {
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "ebi_submission_accession": None,
                "emp_status": "EMP",
                "str_column": "not applicable",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "barcode": "CCTCTGAGAGCT",
                "run_prefix": "s_G1_L002_sequences",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "library_construction_protocol": "AAAA",
                "insdc_nulls": "not applicable",
                "experiment_design_description": "BBBB",
            },
        }
        exp = pd.DataFrame.from_dict(metadata_dict, orient="index", dtype=str)

        obs.sort_index(axis=0, inplace=True)
        obs.sort_index(axis=1, inplace=True)
        exp.sort_index(axis=0, inplace=True)
        exp.sort_index(axis=1, inplace=True)

        assert_frame_equal(obs, exp, check_like=True)

    def test_clean_validate_template_no_forbidden_words1(self):
        PT = qdb.metadata_template.prep_template.PrepTemplate
        self.metadata.rename(columns={"center_name": "sampleid"}, inplace=True)
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            PT._clean_validate_template(self.metadata, 2)

    def test_clean_validate_template_no_forbidden_words2(self):
        PT = qdb.metadata_template.prep_template.PrepTemplate
        self.metadata.rename(
            columns={"center_name": "linkerprimersequence"}, inplace=True
        )
        raised = False
        try:
            PT._clean_validate_template(self.metadata, 2)
        except qdb.exceptions.QiitaDBColumnError:
            raised = True
        self.assertFalse(raised, "Exception raised")

    def test_clean_validate_template_no_pgsql_reserved_words(self):
        PT = qdb.metadata_template.prep_template.PrepTemplate
        self.metadata.rename(columns={"center_name": "select"}, inplace=True)
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            PT._clean_validate_template(self.metadata, 2)

    def test_clean_validate_template_no_qiime2_reserved_words(self):
        PT = qdb.metadata_template.prep_template.PrepTemplate
        self.metadata.rename(columns={"center_name": "featureid"}, inplace=True)
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            PT._clean_validate_template(self.metadata, 2)

    def test_clean_validate_template_no_invalid_chars(self):
        PT = qdb.metadata_template.prep_template.PrepTemplate
        self.metadata.rename(columns={"center_name": "taxon id"}, inplace=True)
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            PT._clean_validate_template(self.metadata, 2)

    def test_clean_validate_template_no_invalid_chars2(self):
        PT = qdb.metadata_template.prep_template.PrepTemplate
        self.metadata.rename(columns={"center_name": "bla."}, inplace=True)
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            PT._clean_validate_template(self.metadata, 2)

    def test_get_category(self):
        pt = qdb.metadata_template.prep_template.PrepTemplate(1)
        obs = pt.get_category("primer")
        exp = {
            "1.SKB2.640194": "GTGCCAGCMGCCGCGGTAA",
            "1.SKM4.640180": "GTGCCAGCMGCCGCGGTAA",
            "1.SKB3.640195": "GTGCCAGCMGCCGCGGTAA",
            "1.SKB6.640176": "GTGCCAGCMGCCGCGGTAA",
            "1.SKD6.640190": "GTGCCAGCMGCCGCGGTAA",
            "1.SKM6.640187": "GTGCCAGCMGCCGCGGTAA",
            "1.SKD9.640182": "GTGCCAGCMGCCGCGGTAA",
            "1.SKM8.640201": "GTGCCAGCMGCCGCGGTAA",
            "1.SKM2.640199": "GTGCCAGCMGCCGCGGTAA",
            "1.SKD2.640178": "GTGCCAGCMGCCGCGGTAA",
            "1.SKB7.640196": "GTGCCAGCMGCCGCGGTAA",
            "1.SKD4.640185": "GTGCCAGCMGCCGCGGTAA",
            "1.SKB8.640193": "GTGCCAGCMGCCGCGGTAA",
            "1.SKM3.640197": "GTGCCAGCMGCCGCGGTAA",
            "1.SKD5.640186": "GTGCCAGCMGCCGCGGTAA",
            "1.SKB1.640202": "GTGCCAGCMGCCGCGGTAA",
            "1.SKM1.640183": "GTGCCAGCMGCCGCGGTAA",
            "1.SKD1.640179": "GTGCCAGCMGCCGCGGTAA",
            "1.SKD3.640198": "GTGCCAGCMGCCGCGGTAA",
            "1.SKB5.640181": "GTGCCAGCMGCCGCGGTAA",
            "1.SKB4.640189": "GTGCCAGCMGCCGCGGTAA",
            "1.SKB9.640200": "GTGCCAGCMGCCGCGGTAA",
            "1.SKM9.640192": "GTGCCAGCMGCCGCGGTAA",
            "1.SKD8.640184": "GTGCCAGCMGCCGCGGTAA",
            "1.SKM5.640177": "GTGCCAGCMGCCGCGGTAA",
            "1.SKM7.640188": "GTGCCAGCMGCCGCGGTAA",
            "1.SKD7.640191": "GTGCCAGCMGCCGCGGTAA",
        }
        self.assertEqual(obs, exp)

    def test_get_category_no_exists(self):
        pt = qdb.metadata_template.prep_template.PrepTemplate(1)
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            pt.get_category("DOESNOTEXIST")

    def test_create_duplicate_header(self):
        """Create raises an error when duplicate headers are present"""
        self.metadata["STR_COLUMN"] = pd.Series(["", "", ""], index=self.metadata.index)
        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateHeaderError):
            qdb.metadata_template.prep_template.PrepTemplate.create(
                self.metadata, self.test_study, self.data_type
            )

    def test_create_bad_sample_names(self):
        # set a horrible list of sample names
        self.metadata.index = ["o()xxxx[{::::::::>", "sample.1", "sample.3"]
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            qdb.metadata_template.prep_template.PrepTemplate.create(
                self.metadata, self.test_study, self.data_type
            )

    def test_create_unknown_sample_names(self):
        # set two real and one fake sample name
        self.metadata_dict["NOTREAL"] = self.metadata_dict["SKB7.640196"]
        del self.metadata_dict["SKB7.640196"]
        self.metadata = pd.DataFrame.from_dict(
            self.metadata_dict, orient="index", dtype=str
        )
        # Test error raised and correct error given
        with self.assertRaises(qdb.exceptions.QiitaDBExecutionError) as err:
            qdb.metadata_template.prep_template.PrepTemplate.create(
                self.metadata, self.test_study, self.data_type
            )
        self.assertEqual(
            str(err.exception),
            "Samples found in prep template but not sample template: 1.NOTREAL",
        )

    def test_create_shorter_prep_template(self):
        # remove one sample so not all samples in the prep template
        del self.metadata_dict["SKB7.640196"]
        self.metadata = pd.DataFrame.from_dict(
            self.metadata_dict, orient="index", dtype=str
        )
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type
        )

        with qdb.sql_connection.TRN:
            sql = """SELECT sample_id
                     FROM qiita.prep_%d
                     WHERE sample_id != '%s'""" % (pt.id, self.QCN)
            qdb.sql_connection.TRN.add(sql)
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        exp = [["1.SKB8.640193"], ["1.SKD8.640184"]]
        self.assertEqual(obs, exp)
        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def _common_creation_checks(self, pt, fp_count, name):
        self.assertEqual(pt.name, name)
        self.assertEqual(pt.data_type(), self.data_type)
        self.assertEqual(pt.data_type(ret_id=True), self.data_type_id)
        self.assertEqual(pt.artifact, None)
        self.assertEqual(pt.investigation_type, "AMPLICON")
        self.assertEqual(pt.study_id, self.test_study.id)
        self.assertEqual(pt.status, "sandbox")
        exp_sample_ids = {
            "%s.SKB8.640193" % self.test_study.id,
            "%s.SKD8.640184" % self.test_study.id,
            "%s.SKB7.640196" % self.test_study.id,
        }
        self.assertEqual(pt._get_sample_ids(), exp_sample_ids)
        self.assertEqual(len(pt), 3)
        exp_categories = {
            "str_column",
            "ebi_submission_accession",
            "run_prefix",
            "barcode",
            "primer",
            "platform",
            "instrument_model",
            "experiment_design_description",
            "library_construction_protocol",
            "center_name",
            "center_project_name",
            "insdc_nulls",
            "emp_status",
        }
        self.assertCountEqual(pt.categories, exp_categories)
        exp_dict = {
            "%s.SKB7.640196" % self.test_study.id: {
                "barcode": "CCTCTGAGAGCT",
                "ebi_submission_accession": None,
                "experiment_design_description": "BBBB",
                "library_construction_protocol": "AAAA",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "run_prefix": "s_G1_L002_sequences",
                "str_column": "Value for sample 3",
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "insdc_nulls": "not applicable",
                "emp_status": "EMP",
            },
            "%s.SKB8.640193" % self.test_study.id: {
                "barcode": "GTCCGCAAGTTA",
                "ebi_submission_accession": None,
                "experiment_design_description": "BBBB",
                "library_construction_protocol": "AAAA",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "run_prefix": "s_G1_L001_sequences",
                "str_column": "Value for sample 1",
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "insdc_nulls": "3.6",
                "emp_status": "EMP",
            },
            "%s.SKD8.640184" % self.test_study.id: {
                "barcode": "CGTAGAGCTCTC",
                "ebi_submission_accession": None,
                "experiment_design_description": "BBBB",
                "library_construction_protocol": "AAAA",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "run_prefix": "s_G1_L001_sequences",
                "str_column": "Value for sample 2",
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "insdc_nulls": "not applicable",
                "emp_status": "EMP",
            },
        }
        for s_id in exp_sample_ids:
            self.assertEqual(pt[s_id]._to_dict(), exp_dict[s_id])

        # prep files have been created
        filepaths = pt.get_filepaths()
        self.assertEqual(len(filepaths), 1)

    def test_validate_restrictions(self):
        PT = qdb.metadata_template.prep_template.PrepTemplate
        pt = PT.create(
            self.metadata, self.test_study, self.data_type, name="New Prep For Test"
        )
        success, message = pt.validate_restrictions()
        self.assertEqual(
            message,
            'prep %d is missing columns "target_gene, target_subfragment"' % pt.id,
        )
        self.assertFalse(success)

        metadata = self.metadata.copy()
        metadata["target_gene"] = "Should Warn"
        metadata["target_subfragment"] = "V4"
        pt.extend(metadata)
        success, message = pt.validate_restrictions()
        self.assertEqual(
            message,
            'prep %d has invalid values: "Should '
            'Warn", valid values are: "16S rRNA, 18S rRNA, '
            'ITS1/2, LSU"' % pt.id,
        )
        self.assertFalse(success)

        metadata["target_gene"] = "16S rRNA"
        # as we are testing the update functionality of a prep info file, we
        # can also test that the timestamps are working correctly
        current_ct = pt.creation_timestamp
        current_mt = pt.modification_timestamp
        self.assertTrue(current_ct < current_mt)
        pt.update(metadata)
        self.assertEqual(current_ct, pt.creation_timestamp)
        self.assertTrue(current_mt < pt.modification_timestamp)
        success, message = pt.validate_restrictions()
        success, message = pt.validate_restrictions()
        self.assertEqual(message, "")
        self.assertTrue(success)

        # cleaning
        PT.delete(pt.id)

    def test_create(self):
        """Creates a new PrepTemplate"""
        fp_count = qdb.util.get_count("qiita.filepath")
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type, name="New Prep For Test"
        )
        self._common_creation_checks(pt, fp_count, "New Prep For Test")
        # checking that the creation and modification timestamps are within
        # 2 seconds of current time
        dsecs = (datetime.now() - pt.modification_timestamp).total_seconds()
        self.assertTrue(dsecs < 2)
        dsecs = (datetime.now() - pt.creation_timestamp).total_seconds()
        self.assertTrue(dsecs < 2)
        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_create_already_prefixed_samples(self):
        """Creates a new PrepTemplate"""
        fp_count = qdb.util.get_count("qiita.filepath")
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata_prefixed, self.test_study, self.data_type
        )
        self._common_creation_checks(pt, fp_count, "Prep information %s" % pt.id)
        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_empty_prep(self):
        """Creates a new PrepTemplate"""
        metadata = pd.DataFrame.from_dict(
            {"SKB8.640193": {}, "SKD8.640184": {}}, orient="index", dtype=str
        )
        with self.assertRaises(ValueError):
            qdb.metadata_template.prep_template.PrepTemplate.create(
                metadata, self.test_study, self.data_type
            )

    def test_generate_files(self):
        fp_count = qdb.util.get_count("qiita.filepath")
        self.tester.generate_files()
        obs = qdb.util.get_count("qiita.filepath")
        # We just make sure that the count has been increased by 1, since
        # the contents of the files have been tested elsewhere.
        self.assertEqual(obs, fp_count + 1)

    def test_create_data_type_id(self):
        """Creates a new PrepTemplate passing the data_type_id"""
        fp_count = qdb.util.get_count("qiita.filepath")
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type_id
        )
        self._common_creation_checks(pt, fp_count, "Prep information %s" % pt.id)
        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_create_warning(self):
        """Warns if a required columns is missing for a given functionality"""
        del self.metadata["barcode"]
        pt = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning,
            qdb.metadata_template.prep_template.PrepTemplate.create,
            self.metadata,
            self.test_study,
            self.data_type,
        )

        self.assertEqual(pt.data_type(), self.data_type)
        self.assertEqual(pt.data_type(ret_id=True), self.data_type_id)
        self.assertEqual(pt.artifact, None)
        self.assertEqual(pt.investigation_type, "AMPLICON")
        self.assertEqual(pt.study_id, self.test_study.id)
        self.assertEqual(pt.status, "sandbox")
        exp_sample_ids = {
            "%s.SKB8.640193" % self.test_study.id,
            "%s.SKD8.640184" % self.test_study.id,
            "%s.SKB7.640196" % self.test_study.id,
        }
        self.assertEqual(pt._get_sample_ids(), exp_sample_ids)
        self.assertEqual(len(pt), 3)
        exp_categories = {
            "str_column",
            "ebi_submission_accession",
            "run_prefix",
            "primer",
            "platform",
            "insdc_nulls",
            "instrument_model",
            "experiment_design_description",
            "library_construction_protocol",
            "center_name",
            "center_project_name",
            "emp_status",
        }
        self.assertCountEqual(pt.categories, exp_categories)
        exp_dict = {
            "%s.SKB7.640196" % self.test_study.id: {
                "ebi_submission_accession": None,
                "experiment_design_description": "BBBB",
                "library_construction_protocol": "AAAA",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "run_prefix": "s_G1_L002_sequences",
                "str_column": "Value for sample 3",
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "insdc_nulls": "not applicable",
                "emp_status": "EMP",
            },
            "%s.SKB8.640193" % self.test_study.id: {
                "ebi_submission_accession": None,
                "experiment_design_description": "BBBB",
                "library_construction_protocol": "AAAA",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "run_prefix": "s_G1_L001_sequences",
                "str_column": "Value for sample 1",
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "insdc_nulls": "3.6",
                "emp_status": "EMP",
            },
            "%s.SKD8.640184" % self.test_study.id: {
                "ebi_submission_accession": None,
                "experiment_design_description": "BBBB",
                "library_construction_protocol": "AAAA",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "run_prefix": "s_G1_L001_sequences",
                "str_column": "Value for sample 2",
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "insdc_nulls": "not applicable",
                "emp_status": "EMP",
            },
        }
        for s_id in exp_sample_ids:
            self.assertEqual(pt[s_id]._to_dict(), exp_dict[s_id])

        # prep files have been created
        filepaths = pt.get_filepaths()
        self.assertEqual(len(filepaths), 1)

        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_create_investigation_type_error(self):
        """Create raises an error if the investigation_type does not exists"""
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            qdb.metadata_template.prep_template.PrepTemplate.create(
                self.metadata, self.test_study, self.data_type_id, "Not a term"
            )

    def test_create_duplicated_column_error(self):
        """Create raises an error if the prep has a duplicated column name"""
        self.metadata["season_environment"] = self.metadata["primer"]
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            qdb.metadata_template.prep_template.PrepTemplate.create(
                self.metadata, self.test_study, self.data_type_id
            )

    def test_delete_error(self):
        """Try to delete a prep template that already has preprocessed data"""
        with self.assertRaises(qdb.exceptions.QiitaDBExecutionError):
            qdb.metadata_template.prep_template.PrepTemplate.delete(1)

    def test_delete_unkonwn_id_error(self):
        """Try to delete a non existent prep template"""
        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.metadata_template.prep_template.PrepTemplate.delete(30000)

    def test_delete_error_raw_data(self):
        """Try to delete a prep template with a raw data attached to id"""
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type_id
        )
        artifact = qdb.artifact.Artifact.create(
            self.filepaths, "FASTQ", prep_template=pt
        )

        with self.assertRaises(qdb.exceptions.QiitaDBExecutionError):
            qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)
        # cleaning
        qdb.artifact.Artifact.delete(artifact.id)
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_delete(self):
        """Deletes prep template 2"""
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type_id
        )
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

        exp = []
        with qdb.sql_connection.TRN:
            sql = """SELECT *
                     FROM qiita.prep_template
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [pt.id])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        self.assertEqual(obs, exp)

        with qdb.sql_connection.TRN:
            sql = """SELECT *
                     FROM qiita.study_prep_template
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [pt.id])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        self.assertEqual(obs, exp)

        with qdb.sql_connection.TRN:
            sql = """SELECT *
                     FROM qiita.prep_template_sample
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [pt.id])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        self.assertEqual(obs, exp)

        with self.assertRaises(ValueError):
            with qdb.sql_connection.TRN:
                sql = (
                    """SELECT *
                         FROM qiita.prep_%d"""
                    % pt.id
                )
                qdb.sql_connection.TRN.add(sql)

    def test_setitem(self):
        """setitem raises an error (currently not allowed)"""
        with self.assertRaises(qdb.exceptions.QiitaDBNotImplementedError):
            self.tester["1.SKM7.640188"] = (
                qdb.metadata_template.prep_template.PrepSample(
                    "1.SKM7.640188", self.tester
                )
            )

    def test_delitem(self):
        """delitem raises an error (currently not allowed)"""
        with self.assertRaises(qdb.exceptions.QiitaDBNotImplementedError):
            del self.tester["1.SKM7.640188"]

    def test_to_file(self):
        """to file writes a tab delimited file with all the metadata"""
        fd, fp = mkstemp()
        close(fd)
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type
        )
        pt.to_file(fp)
        self._clean_up_files.append(fp)
        with open(fp, newline=None) as f:
            obs = f.read()

        self.assertEqual(obs, EXP_PREP_TEMPLATE.format(pt.id))

        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_investigation_type_setter(self):
        """Able to update the investigation type"""
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type_id
        )
        self.assertEqual(pt.investigation_type, "AMPLICON")
        pt.investigation_type = "Other"
        self.assertEqual(pt.investigation_type, "Other")
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            pt.investigation_type = "should fail"

        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_investigation_type_instance_setter(self):
        pt = qdb.metadata_template.prep_template.PrepTemplate(1)
        pt.investigation_type = "RNA-Seq"
        self.assertEqual(pt.investigation_type, "RNA-Seq")

    def test_deprecated_setter(self):
        pt = qdb.metadata_template.prep_template.PrepTemplate(1)
        self.assertFalse(pt.deprecated)
        pt.deprecated = True
        self.assertTrue(pt.deprecated)
        pt.deprecated = False
        self.assertFalse(pt.deprecated)

    def test_status(self):
        pt = qdb.metadata_template.prep_template.PrepTemplate(1)
        self.assertEqual(pt.status, "private")

        # Check that changing the status of the processed data, the status
        # of the prep template changes
        a = qdb.artifact.Artifact(1)
        a.visibility = "public"
        self.assertEqual(pt.status, "public")

        # New prep templates have the status to sandbox because there is no
        # processed data associated with them
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type_id
        )
        self.assertEqual(pt.status, "sandbox")

        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_update_category(self):
        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            self.tester.update_category("barcode", {"foo": "bar"})

        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            self.tester.update_category("missing column", {"1.SKB7.640196": "bar"})

        neg_test = self.tester["1.SKB7.640196"]["barcode"]
        mapping = {"1.SKB8.640193": "AAAAAAAAAAAA", "1.SKD8.640184": "CCCCCCCCCCCC"}

        self.tester.update_category("barcode", mapping)

        self.assertEqual(self.tester["1.SKB7.640196"]["barcode"], neg_test)
        self.assertEqual(self.tester["1.SKB8.640193"]["barcode"], "AAAAAAAAAAAA")
        self.assertEqual(self.tester["1.SKD8.640184"]["barcode"], "CCCCCCCCCCCC")

        neg_test = self.tester["1.SKB7.640196"]["center_name"]
        mapping = {"1.SKB8.640193": "FOO", "1.SKD8.640184": "BAR"}

        self.tester.update_category("center_name", mapping)

        self.assertEqual(self.tester["1.SKB7.640196"]["center_name"], neg_test)
        self.assertEqual(self.tester["1.SKB8.640193"]["center_name"], "FOO")
        self.assertEqual(self.tester["1.SKD8.640184"]["center_name"], "BAR")

    def test_qiime_map_fp(self):
        pt = qdb.metadata_template.prep_template.PrepTemplate(1)
        exp = join(
            qdb.util.get_mountpoint("templates")[0][1],
            "1_prep_1_qiime_[0-9]*-[0-9]*.txt",
        )
        self.assertRegex(pt.qiime_map_fp, exp)

    def test_check_restrictions(self):
        obs = self.tester.check_restrictions(
            [qdb.metadata_template.constants.PREP_TEMPLATE_COLUMNS["EBI"]]
        )
        self.assertEqual(obs, set())

        del self.metadata["primer"]
        pt = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning,
            qdb.metadata_template.prep_template.PrepTemplate.create,
            self.metadata,
            self.test_study,
            self.data_type,
        )

        obs = pt.check_restrictions(
            [
                qdb.metadata_template.constants.PREP_TEMPLATE_COLUMNS["EBI"],
                qdb.metadata_template.constants.PREP_TEMPLATE_COLUMNS_TARGET_GENE[
                    "demultiplex"
                ],
            ]
        )
        self.assertEqual(obs, set())
        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_artifact(self):
        """Returns the artifact associated with the prep template"""
        self.assertEqual(self.tester.artifact, qdb.artifact.Artifact(1))

        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type_id
        )
        self.assertEqual(pt.artifact, None)
        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_artifact_setter_error(self):
        a = qdb.artifact.Artifact(1)
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            self.tester.artifact = a

    def test_artifact_setter(self):
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, "16S"
        )
        self.assertEqual(pt.artifact, None)
        artifact = qdb.artifact.Artifact.create(
            self.filepaths, "FASTQ", prep_template=pt
        )
        self.assertEqual(pt.artifact, artifact)

        # here we can test that we can properly create a workflow but we are
        # going to add lot more steps to make it more complex by adding a
        # few more scenarios
        # 1/4. adds a new path that should be kept separate all the way; this
        #      is to emulate what happens with different trimming (different
        #      default parameter) and deblur (same for each of the previous
        #      steps)
        sql = """
            INSERT INTO qiita.default_workflow_node (
                default_workflow_id, default_parameter_set_id)
            VALUES (1, 2), (1, 10);
            INSERT INTO qiita.default_workflow_edge (
                parent_id, child_id)
            VALUES (7, 8);
            INSERT INTO qiita.default_workflow_edge_connections (
                default_workflow_edge_id, parent_output_id, child_input_id)
            VALUES (4, 1, 3)"""
        qdb.sql_connection.perform_as_transaction(sql)
        # 2/4. adds a new path that should be kept together and then separate;
        #      this is to simulate what happens with MTX/WGS processing, one
        #      single QC step (together) and 2 separete profilers
        sql = """
            INSERT INTO qiita.default_parameter_set (
                command_id, parameter_set_name, parameter_set)
            VALUES (3, '100%',
                    ('{"reference":1,"sortmerna_e_value":1,'
                     || '"sortmerna_max_pos":'
                     || '10000,"similarity":1.0,"sortmerna_coverage":1.00,'
                     || '"threads":1}')::json);
            INSERT INTO qiita.default_workflow_node (
                default_workflow_id, default_parameter_set_id)
            VALUES (1, 17);
            INSERT INTO qiita.default_workflow_edge (
                parent_id, child_id)
            VALUES (7, 9);
            INSERT INTO qiita.default_workflow_edge_connections (
                default_workflow_edge_id, parent_output_id, child_input_id)
            VALUES (5, 1, 3)
            """
        qdb.sql_connection.perform_as_transaction(sql)
        # 3/4. we need to "activate" the merging scheme values of the
        # commands so they are actually different:
        # 31->'Pick closed-reference OTUs', 6->'Split libraries FASTQ'
        sql = """
            UPDATE qiita.command_parameter
            SET check_biom_merge = true
            WHERE command_parameter_id IN (31, 6)"""
        qdb.sql_connection.perform_as_transaction(sql)
        # 4/4. update so we check the prep info file for a valid value
        sql = """
            UPDATE qiita.default_workflow
            SET parameters = '
                {"sample": {"scientific_name": "1118232"},
                 "prep": {"center_name": "ANL - 1"}}'::JSONB
            WHERE default_workflow_id = 1"""
        qdb.sql_connection.perform_as_transaction(sql)

        # let's check that nothing is found due to the parameters, in specific
        # "prep": {"center_name": "ANL - 1"}
        with self.assertRaisesRegex(
            ValueError,
            "This preparation data type: "
            '"16S" and/or artifact type "FASTQ" does '
            "not have valid workflows; this could be "
            "due to required parameters, please check "
            "the available workflows.",
        ):
            pt.add_default_workflow(qdb.user.User("test@foo.bar"))

        # now, let's replace the parameters for something fine
        qdb.software.DefaultWorkflow(1).parameters = {
            "sample": {"scientific_name": "1118232"},
            "prep": {"center_name": "ANL"},
        }
        wk = pt.add_default_workflow(qdb.user.User("test@foo.bar"))
        self.assertEqual(len(wk.graph.nodes), 5)
        self.assertEqual(len(wk.graph.edges), 3)
        self.assertCountEqual(
            [x.command.name for x in wk.graph.nodes],
            # we should have 2 split libraries and 3 close reference
            [
                "Split libraries FASTQ",
                "Split libraries FASTQ",
                "Pick closed-reference OTUs",
                "Pick closed-reference OTUs",
                "Pick closed-reference OTUs",
            ],
        )

        # at this point we can error all the previous steps, add a new smaller
        # workflow and make sure you get the same one as before because it will
        # have a higher match than the new one
        for pj in wk.graph.nodes:
            pj._set_error("Killed")
        sql = """UPDATE qiita.default_workflow_data_type
                 SET data_type_id = 1
                 WHERE default_workflow_id = 2"""
        qdb.sql_connection.perform_as_transaction(sql)
        wk = pt.add_default_workflow(qdb.user.User("test@foo.bar"))
        self.assertEqual(len(wk.graph.nodes), 5)
        self.assertEqual(len(wk.graph.edges), 3)
        self.assertCountEqual(
            [x.command.name for x in wk.graph.nodes],
            # we should have 2 split libraries and 3 close reference
            [
                "Split libraries FASTQ",
                "Split libraries FASTQ",
                "Pick closed-reference OTUs",
                "Pick closed-reference OTUs",
                "Pick closed-reference OTUs",
            ],
        )
        # let's return it back
        sql = """UPDATE qiita.default_workflow_data_type
                 SET data_type_id = 2
                 WHERE default_workflow_id = 2"""
        qdb.sql_connection.perform_as_transaction(sql)

        # now let's try to generate again and it should fail cause the jobs
        # are already created
        with self.assertRaisesRegex(
            ValueError, "Cannot create job because the parameters are the same as jobs"
        ):
            pt.add_default_workflow(qdb.user.User("test@foo.bar"))

        # Then, let's clean up again and add a new command/step with 2
        # BIOM input artifacts
        for pj in wk.graph.nodes:
            pj._set_error("Killed")
        cmd = qdb.software.Command.create(
            qdb.software.Software(1),
            "Multiple BIOM as inputs",
            "",
            {
                "req_artifact_1": ['artifact:["BIOM"]', None],
                "req_artifact_2": ['artifact:["BIOM"]', None],
            },
            outputs={"MB-output": "BIOM"},
        )
        cmd_dp = qdb.software.DefaultParameters.create("", cmd)
        # creating the new node for the cmd and linking it's two inputs with
        # two inputs
        sql = f"""
            INSERT INTO qiita.default_workflow_node (
                default_workflow_id, default_parameter_set_id)
            VALUES (1, {cmd_dp.id});
            INSERT INTO qiita.default_workflow_edge (
                parent_id, child_id)
            VALUES (8, 10);
            INSERT INTO qiita.default_workflow_edge (
                parent_id, child_id)
            VALUES (9, 10);
            INSERT INTO qiita.default_workflow_edge_connections (
                default_workflow_edge_id, parent_output_id, child_input_id)
            VALUES (6, 3, 99);
            INSERT INTO qiita.default_workflow_edge_connections (
                default_workflow_edge_id, parent_output_id, child_input_id)
            VALUES (7, 3, 100)
            """
        qdb.sql_connection.perform_as_transaction(sql)
        wk = pt.add_default_workflow(qdb.user.User("test@foo.bar"))
        self.assertEqual(len(wk.graph.nodes), 6)
        self.assertEqual(len(wk.graph.edges), 5)
        self.assertCountEqual(
            [x.command.name for x in wk.graph.nodes],
            # we should have 2 split libraries and 3 close reference
            [
                "Split libraries FASTQ",
                "Split libraries FASTQ",
                "Pick closed-reference OTUs",
                "Pick closed-reference OTUs",
                "Pick closed-reference OTUs",
                "Multiple BIOM as inputs",
            ],
        )

        # now let's test that an error is raised when there is no valid initial
        # input data; this moves the data type from FASTQ to taxa_summary for
        # the default_workflow_id = 1
        qdb.sql_connection.perform_as_transaction(
            "UPDATE qiita.default_workflow SET artifact_type_id = 10 WHERE "
            "default_workflow_id = 1"
        )
        with self.assertRaisesRegex(
            ValueError,
            "This preparation data type: "
            '"16S" and/or artifact type "FASTQ" does '
            "not have valid workflows",
        ):
            pt.add_default_workflow(qdb.user.User("test@foo.bar"))

        # cleaning
        qdb.artifact.Artifact.delete(artifact.id)
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_can_be_updated_on_new(self):
        """test if the template can be updated"""
        # you can update a newly created pt
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type
        )
        self.assertTrue(pt.can_be_updated({"barcode"}))
        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_extend_add_samples(self):
        """extend correctly works adding new samples"""
        md_2_samples = self.metadata.loc[("SKB8.640193", "SKD8.640184"), :]
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            md_2_samples, self.test_study, self.data_type
        )

        npt.assert_warns(qdb.exceptions.QiitaDBWarning, pt.extend, self.metadata)

        exp_sample_ids = {
            "%s.SKB8.640193" % self.test_study.id,
            "%s.SKD8.640184" % self.test_study.id,
            "%s.SKB7.640196" % self.test_study.id,
        }
        self.assertEqual(pt._get_sample_ids(), exp_sample_ids)

        # test error due to max number of samples during extend
        cmax = qdb.util.max_preparation_samples()
        sql = "UPDATE settings SET max_preparation_samples = %s"
        qdb.sql_connection.perform_as_transaction(sql, [3])
        df = pd.DataFrame.from_dict(
            {"SKB1.640202": {"barcode": "CCTCTGAGAGCT"}}, orient="index", dtype=str
        )
        with self.assertRaisesRegex(
            ValueError, "4 exceeds the max allowed number of samples: 3"
        ):
            pt.extend(df)

        # now test creation
        PT = qdb.metadata_template.prep_template.PrepTemplate
        qdb.sql_connection.perform_as_transaction(sql, [2])
        with self.assertRaisesRegex(
            ValueError, "3 exceeds the max allowed number of samples: 2"
        ):
            PT.create(self.metadata, self.test_study, self.data_type)

        # cleaning
        qdb.sql_connection.perform_as_transaction(sql, [cmax])
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_extend_add_samples_error(self):
        """extend fails adding samples to an already preprocessed template"""
        df = pd.DataFrame.from_dict(
            {"new_sample": {"barcode": "CCTCTGAGAGCT"}}, orient="index", dtype=str
        )
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.metadata_template.prep_template.PrepTemplate(1).extend(df)

    def test_extend_add_cols(self):
        """extend correctly adds a new columns"""
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type
        )
        self.metadata["new_col"] = pd.Series(
            ["val1", "val2", "val3"], index=self.metadata.index
        )

        npt.assert_warns(qdb.exceptions.QiitaDBWarning, pt.extend, self.metadata)

        with qdb.sql_connection.TRN:
            sql = """SELECT *
                     FROM qiita.prep_{0}
                     WHERE sample_id != '{1}'""".format(pt.id, self.QCN)
            qdb.sql_connection.TRN.add(sql)
            obs = dict(qdb.sql_connection.TRN.execute_fetchindex())
        exp = {
            "1.SKB7.640196": {
                "barcode": "CCTCTGAGAGCT",
                "ebi_submission_accession": None,
                "experiment_design_description": "BBBB",
                "library_construction_protocol": "AAAA",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "run_prefix": "s_G1_L002_sequences",
                "str_column": "Value for sample 3",
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "emp_status": "EMP",
                "new_col": "val1",
            },
            "1.SKB8.640193": {
                "barcode": "GTCCGCAAGTTA",
                "ebi_submission_accession": None,
                "experiment_design_description": "BBBB",
                "library_construction_protocol": "AAAA",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "run_prefix": "s_G1_L001_sequences",
                "str_column": "Value for sample 1",
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "emp_status": "EMP",
                "new_col": "val2",
            },
            "1.SKD8.640184": {
                "barcode": "CGTAGAGCTCTC",
                "ebi_submission_accession": None,
                "experiment_design_description": "BBBB",
                "library_construction_protocol": "AAAA",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "run_prefix": "s_G1_L001_sequences",
                "str_column": "Value for sample 2",
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "emp_status": "EMP",
                "new_col": "val3",
            },
        }
        self.assertCountEqual(obs, exp)
        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_extend_update(self):
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type
        )
        self.metadata["new_col"] = pd.Series(
            ["val1", "val2", "val3"], index=self.metadata.index
        )
        self.metadata["str_column"]["SKB7.640196"] = "NEW VAL"

        npt.assert_warns(
            qdb.exceptions.QiitaDBWarning, pt.extend_and_update, self.metadata
        )

        with qdb.sql_connection.TRN:
            sql = """SELECT *
                     FROM qiita.prep_{0}
                     WHERE sample_id != '{1}'""".format(pt.id, self.QCN)
            qdb.sql_connection.TRN.add(sql)
            obs = dict(qdb.sql_connection.TRN.execute_fetchindex())
        exp = {
            "1.SKB7.640196": {
                "barcode": "CCTCTGAGAGCT",
                "ebi_submission_accession": None,
                "experiment_design_description": "BBBB",
                "library_construction_protocol": "AAAA",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "run_prefix": "s_G1_L002_sequences",
                "str_column": "NEW VAL",
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "emp_status": "EMP",
                "new_col": "val1",
            },
            "1.SKB8.640193": {
                "barcode": "GTCCGCAAGTTA",
                "ebi_submission_accession": None,
                "experiment_design_description": "BBBB",
                "library_construction_protocol": "AAAA",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "run_prefix": "s_G1_L001_sequences",
                "str_column": "Value for sample 1",
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "emp_status": "EMP",
                "new_col": "val2",
            },
            "1.SKD8.640184": {
                "barcode": "CGTAGAGCTCTC",
                "ebi_submission_accession": None,
                "experiment_design_description": "BBBB",
                "library_construction_protocol": "AAAA",
                "primer": "GTGCCAGCMGCCGCGGTAA",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "run_prefix": "s_G1_L001_sequences",
                "str_column": "Value for sample 2",
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "emp_status": "EMP",
                "new_col": "val3",
            },
        }

        self.assertCountEqual(obs, exp)

    def test_ebi_experiment_accessions(self):
        obs = self.tester.ebi_experiment_accessions
        exp = {
            "1.SKB8.640193": "ERX0000000",
            "1.SKD8.640184": "ERX0000001",
            "1.SKB7.640196": "ERX0000002",
            "1.SKM9.640192": "ERX0000003",
            "1.SKM4.640180": "ERX0000004",
            "1.SKM5.640177": "ERX0000005",
            "1.SKB5.640181": "ERX0000006",
            "1.SKD6.640190": "ERX0000007",
            "1.SKB2.640194": "ERX0000008",
            "1.SKD2.640178": "ERX0000009",
            "1.SKM7.640188": "ERX0000010",
            "1.SKB1.640202": "ERX0000011",
            "1.SKD1.640179": "ERX0000012",
            "1.SKD3.640198": "ERX0000013",
            "1.SKM8.640201": "ERX0000014",
            "1.SKM2.640199": "ERX0000015",
            "1.SKB9.640200": "ERX0000016",
            "1.SKD5.640186": "ERX0000017",
            "1.SKM3.640197": "ERX0000018",
            "1.SKD9.640182": "ERX0000019",
            "1.SKB4.640189": "ERX0000020",
            "1.SKD7.640191": "ERX0000021",
            "1.SKM6.640187": "ERX0000022",
            "1.SKD4.640185": "ERX0000023",
            "1.SKB3.640195": "ERX0000024",
            "1.SKB6.640176": "ERX0000025",
            "1.SKM1.640183": "ERX0000026",
        }
        self.assertEqual(obs, exp)

        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type
        )
        obs = pt.ebi_experiment_accessions
        exp = {
            "%s.SKB8.640193" % self.test_study.id: None,
            "%s.SKD8.640184" % self.test_study.id: None,
            "%s.SKB7.640196" % self.test_study.id: None,
        }
        self.assertEqual(obs, exp)
        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_ebi_experiment_accessions_setter(self):
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            self.tester.ebi_experiment_accessions = {
                "1.SKB8.640193": "ERX1000000",
                "1.SKD8.640184": "ERX1000001",
            }

        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type
        )
        exp_acc = {
            "%s.SKB8.640193" % self.test_study.id: "ERX0000126",
            "%s.SKD8.640184" % self.test_study.id: "ERX0000127",
        }
        pt.ebi_experiment_accessions = exp_acc
        exp_acc["%s.SKB7.640196" % self.test_study.id] = None
        self.assertEqual(pt.ebi_experiment_accessions, exp_acc)
        exp_acc["%s.SKB7.640196" % self.test_study.id] = "ERX0000128"
        pt.ebi_experiment_accessions = exp_acc
        self.assertEqual(pt.ebi_experiment_accessions, exp_acc)

        # We need to wrap the assignment in a function so we can use
        # npt.assert_warns
        def f():
            pt.ebi_experiment_accessions = exp_acc

        npt.assert_warns(qdb.exceptions.QiitaDBWarning, f)
        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_ebi_experiment_accessions_setter_common_samples(self):
        # If 2 different prep templates have common samples, setting the
        # ebi_experiment_accession should affect only the prep template
        # that it was called to, not both prep templates
        pt1 = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type
        )
        pt2 = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type
        )
        exp_acc1 = {
            "%s.SKB8.640193" % self.test_study.id: "ERX0000126",
            "%s.SKD8.640184" % self.test_study.id: "ERX0000127",
        }
        pt1.ebi_experiment_accessions = exp_acc1
        exp_acc1["%s.SKB7.640196" % self.test_study.id] = None
        self.assertEqual(pt1.ebi_experiment_accessions, exp_acc1)
        exp_acc2 = {k: None for k in exp_acc1.keys()}
        self.assertEqual(pt2.ebi_experiment_accessions, exp_acc2)
        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt1.id)
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt2.id)

    def test_is_submitted_to_ebi(self):
        self.assertTrue(self.tester.is_submitted_to_ebi)
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type
        )
        self.assertFalse(pt.is_submitted_to_ebi)
        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(pt.id)

    def test_validate_template_warning_missing(self):
        """Raises an error if the template is missing a required column"""
        metadata_dict = {
            "SKB8.640193": {
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "ebi_submission_accession": None,
                "linkerprimersequence": "GTGCCAGCMGCCGCGGTAA",
                "barcodesequence": "GTCCGCAAGTTA",
                "run_prefix": "s_G1_L001_sequences",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "library_construction_protocol": "AAAA",
                "experiment_design_description": "BBBB",
            }
        }
        metadata = pd.DataFrame.from_dict(metadata_dict, orient="index", dtype=str)
        PT = qdb.metadata_template.prep_template.PrepTemplate
        obs = PT._clean_validate_template(metadata, 2)

        metadata_dict = {
            "2.SKB8.640193": {
                "center_name": "ANL",
                "center_project_name": "Test Project",
                "ebi_submission_accession": None,
                "linkerprimersequence": "GTGCCAGCMGCCGCGGTAA",
                "barcodesequence": "GTCCGCAAGTTA",
                "run_prefix": "s_G1_L001_sequences",
                "platform": "Illumina",
                "instrument_model": "Illumina MiSeq",
                "library_construction_protocol": "AAAA",
                "experiment_design_description": "BBBB",
            }
        }
        exp = pd.DataFrame.from_dict(metadata_dict, orient="index", dtype=str)
        obs.sort_index(axis=0, inplace=True)
        obs.sort_index(axis=1, inplace=True)
        exp.sort_index(axis=0, inplace=True)
        exp.sort_index(axis=1, inplace=True)
        assert_frame_equal(obs, exp, check_like=True)

    def test_delete_column(self):
        QE = qdb.exceptions
        pt = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type
        )
        pt.delete_column("str_column")
        self.assertNotIn("str_column", pt.categories)

        # testing errors
        pt = qdb.metadata_template.prep_template.PrepTemplate(1)
        with self.assertRaises(QE.QiitaDBOperationNotPermittedError):
            pt.delete_column("barcode")
        with self.assertRaises(QE.QiitaDBColumnError):
            pt.delete_column("ph")

    def test_delete_samples(self):
        QE = qdb.exceptions
        sid = self.test_study.id

        ptA = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type
        )
        ptB = qdb.metadata_template.prep_template.PrepTemplate.create(
            self.metadata, self.test_study, self.data_type
        )

        # first let's test that we cannot delete all samples from one of the
        # preps
        with self.assertRaisesRegex(
            ValueError, "You cannot delete all samples from an information file"
        ):
            ptA.delete_samples(list(ptA.keys()))

        # then continue with the regular testing
        sample1 = "%s.SKB8.640193" % sid
        sample2 = "%s.SKD8.640184" % sid
        sample3 = "%s.SKB7.640196" % sid
        ptA.delete_samples([sample1])
        self.assertNotIn(sample1, ptA)
        self.assertIn(sample2, ptA)
        self.assertIn(sample3, ptA)
        ptB.delete_samples([sample2, sample3])
        self.assertIn(sample1, ptB)
        self.assertNotIn(sample2, ptB)
        self.assertNotIn(sample3, ptB)

        pt = qdb.metadata_template.prep_template.PrepTemplate(1)
        self.assertIn(sample1, pt)

        # testing errors
        with self.assertRaises(QE.QiitaDBUnknownIDError):
            ptA.delete_samples(["not.existing.sample"])

        pt = qdb.metadata_template.prep_template.PrepTemplate(2)
        with self.assertRaises(QE.QiitaDBOperationNotPermittedError):
            pt.delete_samples(["1.SKM5.640177"])

        # cleaning
        qdb.metadata_template.prep_template.PrepTemplate.delete(ptA.id)
        qdb.metadata_template.prep_template.PrepTemplate.delete(ptB.id)

    def test_name_setter(self):
        pt = qdb.metadata_template.prep_template.PrepTemplate(1)
        self.assertEqual(pt.name, "Prep information 1")
        pt.name = "New Name"
        self.assertEqual(pt.name, "New Name")
        pt.name = "Prep information 1"
        self.assertEqual(pt.name, "Prep information 1")

    def test_current_human_filtering(self):
        pt = qdb.metadata_template.prep_template.PrepTemplate(1)
        # by default it should be false
        self.assertFalse(pt.current_human_filtering)
        pt.current_human_filtering = True
        self.assertTrue(pt.current_human_filtering)
        pt.current_human_filtering = False
        self.assertFalse(pt.current_human_filtering)

    def test_reprocess_job_id(self):
        pt = qdb.metadata_template.prep_template.PrepTemplate(1)
        # by default it should be None
        self.assertIsNone(pt.reprocess_job_id)
        # it should not accept an external_job_id
        with self.assertRaises(ValueError):
            pt.reprocess_job_id = "124567"
        # but it should work fine with an uuid
        jid = "6d368e16-2242-4cf8-87b4-a5dc40bb890b"
        pt.reprocess_job_id = jid
        self.assertEqual(pt.reprocess_job_id, jid)
        # and it should be fine to return to its default value
        pt.reprocess_job_id = None
        self.assertIsNone(pt.reprocess_job_id)


EXP_PREP_TEMPLATE = (
    "sample_name\tbarcode\tcenter_name\tcenter_project_name\t"
    "ebi_submission_accession\temp_status\texperiment_design_description\t"
    "insdc_nulls\tinstrument_model\tlibrary_construction_protocol\tplatform\t"
    "primer\tqiita_prep_id\trun_prefix\tstr_column\n"
    "1.SKB7.640196\tCCTCTGAGAGCT\tANL\tTest Project\t\tEMP\tBBBB\t"
    "not applicable\tIllumina MiSeq\tAAAA\tIllumina\tGTGCCAGCMGCCGCGGTAA\t"
    "{0}\ts_G1_L002_sequences\tValue for sample 3\n"
    "1.SKB8.640193\tGTCCGCAAGTTA\tANL\tTest Project\t\tEMP\tBBBB\t"
    "3.6\tIllumina MiSeq\tAAAA\tIllumina\tGTGCCAGCMGCCGCGGTAA\t"
    "{0}\ts_G1_L001_sequences\tValue for sample 1\n"
    "1.SKD8.640184\tCGTAGAGCTCTC\tANL\tTest Project\t\tEMP\tBBBB\t"
    "not applicable\tIllumina MiSeq\tAAAA\tIllumina\tGTGCCAGCMGCCGCGGTAA\t"
    "{0}\ts_G1_L001_sequences\tValue for sample 2\n"
)


if __name__ == "__main__":
    main()
