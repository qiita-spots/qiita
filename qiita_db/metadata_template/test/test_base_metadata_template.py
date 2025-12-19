# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

import qiita_db as qdb
from qiita_core.exceptions import IncompetentQiitaDeveloperError


class TestBaseSample(TestCase):
    """Tests the BaseSample class"""

    def test_init(self):
        """BaseSample init should raise an error (it's a base class)"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            qdb.metadata_template.base_metadata_template.BaseSample(
                "SKM7.640188", qdb.metadata_template.sample_template.SampleTemplate(1)
            )

    def test_exists(self):
        """exists should raise an error if called from the base class"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            qdb.metadata_template.base_metadata_template.BaseSample.exists(
                "SKM7.640188", qdb.metadata_template.sample_template.SampleTemplate(1)
            )


class TestMetadataTemplateReadOnly(TestCase):
    """Tests the MetadataTemplate base class"""

    def setUp(self):
        self.study = qdb.study.Study(1)

    def test_init(self):
        """Init raises an error because it's not called from a subclass"""
        MT = qdb.metadata_template.base_metadata_template.MetadataTemplate
        with self.assertRaises(IncompetentQiitaDeveloperError):
            MT(1)

    def test_unique_ids(self):
        """Unique IDs raises an error because it's not called from a subclass
        """
        MT = qdb.metadata_template.base_metadata_template.MetadataTemplate
        with self.assertRaises(IncompetentQiitaDeveloperError):
            MT.unique_ids(self.study)

    def test_exists(self):
        """Exists raises an error because it's not called from a subclass"""
        MT = qdb.metadata_template.base_metadata_template.MetadataTemplate
        with self.assertRaises(IncompetentQiitaDeveloperError):
            MT.exists(self.study)

    def test_table_name(self):
        """table name raises an error because it's not called from a subclass"""
        MT = qdb.metadata_template.base_metadata_template.MetadataTemplate
        with self.assertRaises(IncompetentQiitaDeveloperError):
            MT._table_name(self.study)

    def test_common_creation_steps(self):
        """common_creation_steps raises an error from base class"""
        MT = qdb.metadata_template.base_metadata_template.MetadataTemplate
        with self.assertRaises(IncompetentQiitaDeveloperError):
            MT._common_creation_steps(None, 1)

    def test_clean_validate_template(self):
        """_clean_validate_template raises an error from base class"""
        MT = qdb.metadata_template.base_metadata_template.MetadataTemplate
        with self.assertRaises(IncompetentQiitaDeveloperError):
            MT._clean_validate_template(None, 1)

    def test_identify_pgsql_reserved_words(self):
        MT = qdb.metadata_template.base_metadata_template.MetadataTemplate
        results = MT._identify_pgsql_reserved_words_in_column_names(
            ["select", "column", "just_fine1"]
        )
        self.assertCountEqual(set(results), {"column", "select"})

    def test_identify_qiime2_reserved_words(self):
        MT = qdb.metadata_template.base_metadata_template.MetadataTemplate
        results = MT._identify_qiime2_reserved_words_in_column_names(
            [
                "feature id",
                "feature-id",
                "featureid",
                "id",
                "sample id",
                "sample-id",
                "sampleid",
            ]
        )
        self.assertCountEqual(
            set(results),
            {
                "feature id",
                "feature-id",
                "featureid",
                "id",
                "sample id",
                "sample-id",
                "sampleid",
            },
        )

    def test_identify_invalid_characters(self):
        MT = qdb.metadata_template.base_metadata_template.MetadataTemplate
        results = MT._identify_column_names_with_invalid_characters(
            [
                "tax on",
                "bla.",
                ".",
                "sampleid",
                "sample_id",
                "{",
                "bla:1",
                "bla|2",
                "bla1:2|3",
                "this&is",
                "4column",
                "just_fine2",
            ]
        )
        self.assertCountEqual(
            set(results), {"tax on", "bla.", ".", "{", "this&is", "4column"}
        )

    def test_restrictions(self):
        MT = qdb.metadata_template
        obs = MT.sample_template.SampleTemplate(1).restrictions
        exp = {
            "env_package": [
                "air",
                "built environment",
                "host-associated",
                "human-associated",
                "human-skin",
                "human-oral",
                "human-gut",
                "human-vaginal",
                "microbial mat/biofilm",
                "misc environment",
                "plant-associated",
                "sediment",
                "soil",
                "wastewater/sludge",
                "water",
            ]
        }
        self.assertEqual(obs, exp)
        obs = MT.prep_template.PrepTemplate(1).restrictions
        exp = {
            "target_gene": ["16S rRNA", "18S rRNA", "ITS1/2", "LSU"],
            "platform": [
                "DNBSEQ",
                "FASTA",
                "Illumina",
                "Ion_Torrent",
                "LS454",
                "Oxford Nanopore",
            ],
            "target_subfragment": ["V3", "V4", "V6", "V9", "ITS1/2"],
            "instrument_model": [
                "454 GS",
                "454 GS 20",
                "454 GS FLX",
                "454 GS FLX+",
                "454 GS FLX Titanium",
                "454 GS Junior",
                "DNBSEQ-G400",
                "DNBSEQ-T7",
                "DNBSEQ-G800",
                "Illumina Genome Analyzer",
                "Illumina Genome Analyzer II",
                "Illumina Genome Analyzer IIx",
                "Illumina HiScanSQ",
                "Illumina HiSeq 1000",
                "Illumina HiSeq 1500",
                "Illumina HiSeq 2000",
                "Illumina HiSeq 2500",
                "Illumina HiSeq 3000",
                "Illumina HiSeq 4000",
                "Illumina MiSeq",
                "Illumina MiniSeq",
                "Illumina NovaSeq 6000",
                "NextSeq 500",
                "NextSeq 550",
                "Ion Torrent PGM",
                "Ion Torrent Proton",
                "Ion Torrent S5",
                "Ion Torrent S5 XL",
                "MinION",
                "GridION",
                "PromethION",
                "unspecified",
            ],
        }
        self.assertEqual(obs, exp)


if __name__ == "__main__":
    main()
