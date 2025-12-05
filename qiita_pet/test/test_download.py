# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import json
from io import StringIO
from os import close, makedirs, remove
from os.path import basename, exists, isdir, join
from shutil import rmtree
from tempfile import mkdtemp, mkstemp
from unittest import main
from urllib.parse import urlparse

import pandas as pd
from biom import example_table as et
from biom.util import biom_open
from mock import Mock

from qiita_db.artifact import Artifact
from qiita_db.software import Command, Parameters
from qiita_db.study import Study
from qiita_db.user import User
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.test.tornado_test_base import TestHandlerBase


class TestDownloadHandler(TestHandlerBase):
    def setUp(self):
        super(TestDownloadHandler, self).setUp()
        self._clean_up_files = []

    def tearDown(self):
        super(TestDownloadHandler, self).tearDown()
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

    def test_download(self):
        # check success
        response = self.get("/download/1")
        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.body.decode("ascii"),
            (
                "This installation of Qiita was not equipped with nginx, so it "
                "is incapable of serving files. The file you attempted to "
                "download is located at raw_data/1_s_G1_L001_sequences.fastq.gz"
            ),
        )
        self.assertEqual(
            response.headers["Content-Disposition"],
            "attachment; filename=1_1_s_G1_L001_sequences.fastq.gz",
        )
        # other tests to validate the filename
        response = self.get("/download/2")
        self.assertEqual(
            response.headers["Content-Disposition"],
            "attachment; filename=1_1_s_G1_L001_sequences_barcodes.fastq.gz",
        )
        response = self.get("/download/3")
        self.assertEqual(
            response.headers["Content-Disposition"], "attachment; filename=2_1_seqs.fna"
        )
        response = self.get("/download/18")
        self.assertEqual(
            response.headers["Content-Disposition"],
            "attachment; filename=1_prep_1_19700101-000000.txt",
        )
        response = self.get("/download/22")
        self.assertEqual(
            response.headers["Content-Disposition"],
            "attachment; filename=7_biom_table.biom",
        )

        # failure
        response = self.get("/download/1000")
        self.assertEqual(response.code, 403)

        # directory
        a = Artifact(1)
        fd, fp = mkstemp(suffix=".html")
        close(fd)
        with open(fp, "w") as f:
            f.write("\n")
        self._clean_up_files.append(fp)
        dirpath = mkdtemp()
        fd, fp2 = mkstemp(suffix=".txt", dir=dirpath)
        close(fd)
        with open(fp2, "w") as f:
            f.write("\n")
        self._clean_up_files.append(dirpath)
        a.set_html_summary(fp, support_dir=dirpath)
        for x in a.filepaths:
            if x["fp_type"] == "html_summary_dir":
                break
        response = self.get("/download/%d" % x["fp_id"])
        self.assertEqual(response.code, 200)

        fp_name = basename(fp2)
        dirname = basename(dirpath)
        self.assertEqual(
            response.body.decode("ascii"),
            "- 1 /protected/FASTQ/1/%s/%s FASTQ/1/%s/%s\n"
            % (dirname, fp_name, dirname, fp_name),
        )


class TestDownloadStudyBIOMSHandler(TestHandlerBase):
    def setUp(self):
        super(TestDownloadStudyBIOMSHandler, self).setUp()
        self._clean_up_files = []

    def tearDown(self):
        super(TestDownloadStudyBIOMSHandler, self).tearDown()
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

    def test_download_study(self):
        tmp_dir = mkdtemp()
        self._clean_up_files.append(tmp_dir)

        biom_fp = join(tmp_dir, "otu_table.biom")
        smr_dir = join(tmp_dir, "sortmerna_picked_otus")
        log_dir = join(smr_dir, "seqs_otus.log")
        tgz = join(tmp_dir, "sortmerna_picked_otus.tgz")

        with biom_open(biom_fp, "w") as f:
            et.to_hdf5(f, "test")
        makedirs(smr_dir)
        with open(log_dir, "w") as f:
            f.write("\n")
        with open(tgz, "w") as f:
            f.write("\n")

        files_biom = [(biom_fp, "biom"), (smr_dir, "directory"), (tgz, "tgz")]

        params = Parameters.from_default_params(
            next(Command(3).default_parameter_sets), {"input_data": 1}
        )
        a = Artifact.create(
            files_biom, "BIOM", parents=[Artifact(2)], processing_parameters=params
        )
        for x in a.filepaths:
            self._clean_up_files.append(x["fp"])

        response = self.get("/download_study_bioms/1")
        self.assertEqual(response.code, 200)
        exp = (
            "- \\d+ /protected/processed_data/1_study_1001_closed_reference_"
            "otu_table.biom processed_data/1_study_1001_closed_reference_otu"
            "_table.biom\n"
            "- \\d+ /protected/templates/1_prep_1_qiime_19700101-000000.txt "
            "mapping_files/4_mapping_file.txt\n"
            "- \\d+ /protected/processed_data/1_study_1001_closed_reference_"
            "otu_table.biom processed_data/1_study_1001_closed_reference_otu"
            "_table.biom\n"
            "- \\d+ /protected/templates/1_prep_1_qiime_19700101-000000.txt "
            "mapping_files/5_mapping_file.txt\n"
            "- \\d+ /protected/processed_data/1_study_1001_closed_reference_"
            "otu_table_Silva.biom processed_data/1_study_1001_closed_"
            "reference_otu_table_Silva.biom\n"
            "- \\d+ /protected/templates/1_prep_1_qiime_19700101-000000.txt "
            "mapping_files/6_mapping_file.txt\n"
            "- \\d+ /protected/BIOM/7/biom_table.biom BIOM/7/biom_table.biom\n"
            "- \\d+ /protected/BIOM/10/otu_table.biom BIOM/10/otu_table.biom\n"
            "- \\d+ /protected/BIOM/10/sortmerna_picked_otus/seqs_otus.log "
            "BIOM/10/sortmerna_picked_otus/seqs_otus.log\n"
            "- \\d+ /protected/templates/1_prep_1_qiime_19700101-000000.txt "
            "mapping_files/10_mapping_file.txt\n"
        )
        self.assertRegex(response.body.decode("ascii"), exp)

        response = self.get("/download_study_bioms/200")
        self.assertEqual(response.code, 405)

        # changing user so we can test the failures
        BaseHandler.get_current_user = Mock(return_value=User("demo@microbio.me"))
        response = self.get("/download_study_bioms/1")
        self.assertEqual(response.code, 405)

        a.visibility = "public"
        response = self.get("/download_study_bioms/1")
        # returning visibility
        a.visibility = "private"
        self.assertEqual(response.code, 200)
        # we should have the same files than the previous test, except artifact
        # and mapping file 7: position 6; thus removing 6
        exp = exp.split("\n")
        exp.pop(6)
        exp = "\n".join(exp)
        self.assertRegex(response.body.decode("ascii"), exp)


class TestDownloadRelease(TestHandlerBase):
    def test_download(self):
        # check success
        response = self.get("/release/download/1")
        self.assertEqual(response.code, 200)
        self.assertIn(
            "This installation of Qiita was not equipped with nginx, so it is "
            "incapable of serving files. The file you attempted to download "
            "is located at",
            response.body.decode("ascii"),
        )


class TestDownloadRawData(TestHandlerBase):
    def setUp(self):
        super(TestDownloadRawData, self).setUp()
        self._clean_up_files = []

    def tearDown(self):
        super(TestDownloadRawData, self).tearDown()
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

    def test_download_raw_data(self):
        # it's possible that one of the tests is deleting the raw data
        # so we will make sure that the files exists so this test passes
        study = Study(1)
        all_files = [x["fp"] for a in study.artifacts() for x in a.filepaths]
        for fp in all_files:
            if not exists(fp):
                with open(fp, "w") as f:
                    f.write("")
        response = self.get("/download_raw_data/1")
        self.assertEqual(response.code, 200)

        exp = (
            "- 58 /protected/raw_data/1_s_G1_L001_sequences.fastq.gz "
            "raw_data/1_s_G1_L001_sequences.fastq.gz\n"
            "- 58 /protected/raw_data/"
            "1_s_G1_L001_sequences_barcodes.fastq.gz "
            "raw_data/1_s_G1_L001_sequences_barcodes.fastq.gz\n"
            "- [0-9]* /protected/templates/1_prep_1_qiime_[0-9]*-[0-9]*.txt "
            "mapping_files/1_mapping_file.txt\n"
            "- 1093210 /protected/BIOM/7/biom_table.biom "
            "BIOM/7/biom_table.biom\n"
        )
        self.assertRegex(response.body.decode("ascii"), exp)

        response = self.get("/download_study_bioms/200")
        self.assertEqual(response.code, 405)

        # changing user so we can test the failures
        BaseHandler.get_current_user = Mock(return_value=User("demo@microbio.me"))
        response = self.get("/download_study_bioms/1")
        self.assertEqual(response.code, 405)

        # now, let's make sure that when artifacts are public AND the
        # public_raw_download any user can download the files
        study.public_raw_download = True
        BaseHandler.get_current_user = Mock(return_value=User("demo@microbio.me"))
        response = self.get("/download_study_bioms/1")
        self.assertEqual(response.code, 405)
        # 7 is an uploaded biom, which should now be available but as it's a
        # biom, only the prep info file will be retrieved
        Artifact(7).visibility = "public"
        BaseHandler.get_current_user = Mock(return_value=User("demo@microbio.me"))
        response = self.get("/download_study_bioms/1")
        self.assertEqual(response.code, 200)
        exp = "- [0-9]* /protected/BIOM/7/biom_table.biom BIOM/7/biom_table.biom\n"
        self.assertRegex(response.body.decode("ascii"), exp)


class TestDownloadEBISampleAccessions(TestHandlerBase):
    def test_download(self):
        # check success
        response = self.get("/download_ebi_accessions/samples/1")
        exp = (
            "sample_name\tsample_accession\n1.SKB2.640194\tERS000008\n"
            "1.SKM4.640180\tERS000004\n1.SKB3.640195\tERS000024\n"
            "1.SKB6.640176\tERS000025\n1.SKD6.640190\tERS000007\n"
            "1.SKM6.640187\tERS000022\n1.SKD9.640182\tERS000019\n"
            "1.SKM8.640201\tERS000014\n1.SKM2.640199\tERS000015\n"
            "1.SKD2.640178\tERS000009\n1.SKB7.640196\tERS000002\n"
            "1.SKD4.640185\tERS000023\n1.SKB8.640193\tERS000000\n"
            "1.SKM3.640197\tERS000018\n1.SKD5.640186\tERS000017\n"
            "1.SKB1.640202\tERS000011\n1.SKM1.640183\tERS000025\n"
            "1.SKD1.640179\tERS000012\n1.SKD3.640198\tERS000013\n"
            "1.SKB5.640181\tERS000006\n1.SKB4.640189\tERS000020\n"
            "1.SKB9.640200\tERS000016\n1.SKM9.640192\tERS000003\n"
            "1.SKD8.640184\tERS000001\n1.SKM5.640177\tERS000005\n"
            "1.SKM7.640188\tERS000010\n1.SKD7.640191\tERS000021"
        )
        self.assertEqual(response.code, 200)
        # testing as lists so we ignore order
        obs = response.body.decode("ascii").split("\n")
        exp = exp.split("\n")
        self.assertCountEqual(obs, exp)

        # changing user so we can test the failures
        BaseHandler.get_current_user = Mock(return_value=User("demo@microbio.me"))
        response = self.get("/download_ebi_accessions/samples/1")
        self.assertEqual(response.code, 405)


class TestDownloadEBIPrepAccessions(TestHandlerBase):
    def test_download(self):
        # check success
        response = self.get("/download_ebi_accessions/experiments/1")
        exp = (
            "sample_name\texperiment_accession\n1.SKB2.640194\tERX0000008\n"
            "1.SKM4.640180\tERX0000004\n1.SKB3.640195\tERX0000024\n"
            "1.SKB6.640176\tERX0000025\n1.SKD6.640190\tERX0000007\n"
            "1.SKM6.640187\tERX0000022\n1.SKD9.640182\tERX0000019\n"
            "1.SKM8.640201\tERX0000014\n1.SKM2.640199\tERX0000015\n"
            "1.SKD2.640178\tERX0000009\n1.SKB7.640196\tERX0000002\n"
            "1.SKD4.640185\tERX0000023\n1.SKB8.640193\tERX0000000\n"
            "1.SKM3.640197\tERX0000018\n1.SKD5.640186\tERX0000017\n"
            "1.SKB1.640202\tERX0000011\n1.SKM1.640183\tERX0000026\n"
            "1.SKD1.640179\tERX0000012\n1.SKD3.640198\tERX0000013\n"
            "1.SKB5.640181\tERX0000006\n1.SKB4.640189\tERX0000020\n"
            "1.SKB9.640200\tERX0000016\n1.SKM9.640192\tERX0000003\n"
            "1.SKD8.640184\tERX0000001\n1.SKM5.640177\tERX0000005\n"
            "1.SKM7.640188\tERX0000010\n1.SKD7.640191\tERX0000021"
        )
        self.assertEqual(response.code, 200)
        # testing as lists so we ignore order
        obs = response.body.decode("ascii").split("\n")
        exp = exp.split("\n")
        self.assertCountEqual(obs, exp)

        # changing user so we can test the failures
        BaseHandler.get_current_user = Mock(return_value=User("demo@microbio.me"))
        response = self.get("/download_ebi_accessions/experiments/1")
        self.assertEqual(response.code, 405)


class TestDownloadSampleInfoPerPrep(TestHandlerBase):
    def test_download(self):
        # check success
        response = self.get("/download_sample_info_per_prep/1")
        self.assertEqual(response.code, 200)

        df = pd.read_csv(StringIO(response.body.decode("ascii")), sep="\t")
        # just testing shape as the actual content is tested in the dataframe
        # generation
        self.assertEqual(df.shape, (27, 33))

        # changing user so we can test the failures
        BaseHandler.get_current_user = Mock(return_value=User("demo@microbio.me"))
        response = self.get("/download_sample_info_per_prep/1")
        self.assertEqual(response.code, 405)


class TestDownloadUpload(TestHandlerBase):
    def test_download(self):
        # check failure
        response = self.get("/download_upload/1/uploaded_file.txt")
        self.assertEqual(response.code, 403)

        # check success
        BaseHandler.get_current_user = Mock(return_value=User("admin@foo.bar"))
        response = self.get("/download_upload/1/uploaded_file.txt")
        self.assertEqual(response.code, 200)


class TestDownloadPublicHandler(TestHandlerBase):
    def test_download(self):
        # check failures
        response = self.get("/public_download/")
        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.reason,
            "You need to specify "
            "both data (the data type you want to download - "
            "raw/biom/sample_information/prep_information) and "
            "study_id or prep_id",
        )

        response = self.get("/public_download/?data=raw&study_id=10000")
        self.assertEqual(response.code, 422)
        self.assertEqual(response.reason, "Study does not exist")

        response = self.get("/public_download/?data=raw&study_id=1")
        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.reason,
            "Study is not public. If this is a mistake contact: foo@bar.com",
        )

        # 7 is an uploaded biom, which should now be available but as it's a
        # biom, only the prep info file will be retrieved
        Artifact(7).visibility = "public"
        response = self.get("/public_download/?data=raw&study_id=1")
        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.reason,
            "No raw data access. If this is a mistake contact: foo@bar.com",
        )

        # check success
        response = self.get("/public_download/?data=biom&study_id=1")
        self.assertEqual(response.code, 200)
        exp = "- [0-9]* /protected/BIOM/7/biom_table.biom BIOM/7/biom_table.biom\n"
        self.assertRegex(response.body.decode("ascii"), exp)

        Study(1).public_raw_download = True
        # check success
        response = self.get("/public_download/?data=raw&study_id=1")
        self.assertEqual(response.code, 200)
        exp = "- [0-9]* /protected/BIOM/7/biom_table.biom BIOM/7/biom_table.biom\n"
        self.assertRegex(response.body.decode("ascii"), exp)

        # testing data_type
        response = self.get("/public_download/?data=raw&study_id=1&data_type=X")
        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.reason,
            "Not a valid data_type. Valid types "
            "are: 16S, 18S, ITS, Proteomic, Metabolomic, "
            "Metagenomic, Multiomic, Metatranscriptomics, "
            "Viromics, Genomics, Transcriptomics, "
            "Job Output Folder",
        )

        response = self.get("/public_download/?data=raw&study_id=1&data_type=Genomics")
        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.reason,
            "Nothing to download. If this is a mistake contact: foo@bar.com",
        )
        response = self.get("/public_download/?data=biom&study_id=1&data_type=Genomics")
        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.reason,
            "Nothing to download. If this is a mistake contact: foo@bar.com",
        )

        # check success
        Artifact(5).visibility = "public"
        response = self.get("/public_download/?data=raw&study_id=1&data_type=18S")
        self.assertEqual(response.code, 200)
        exp = (
            "[0-9]* [0-9]* /protected/raw_data/1_s_G1_L001_sequences_barcodes"
            ".fastq.gz raw_data/1_s_G1_L001_sequences_barcodes.fastq.gz\n"
            "- [0-9]* /protected/templates/1_prep_1_qiime_19700101-000000.txt "
            "mapping_files/1_mapping_file.txt"
        )
        self.assertRegex(response.body.decode("ascii"), exp)

        response = self.get("/public_download/?data=biom&study_id=1&data_type=18S")
        self.assertEqual(response.code, 200)
        exp = (
            "- [0-9]* /protected/processed_data/1_study_1001_closed_"
            "reference_otu_table.biom processed_data/1_study_1001_closed_"
            "reference_otu_table.biom\n- [0-9]* /protected/templates/1_prep_"
            "1_qiime_19700101-000000.txt mapping_files/4_mapping_file.txt\n"
            "- [0-9]* /protected/processed_data/1_study_1001_closed_"
            "reference_otu_table.biom processed_data/1_study_1001_closed_"
            "reference_otu_table.biom\n- [0-9]* /protected/templates/1_prep_"
            "1_qiime_19700101-000000.txt mapping_files/5_mapping_file.txt\n"
        )

        self.assertRegex(response.body.decode("ascii"), exp)

    def test_download_sample_information(self):
        response = self.get("/public_download/?data=sample_information")
        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.reason,
            "You need to specify both data (the data type "
            "you want to download - raw/biom/sample_information/"
            "prep_information) and study_id or prep_id",
        )

        response = self.get(
            "/public_download/?data=sample_information&data_type=16S&study_id=1"
        )
        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.reason,
            "If requesting an information file you cannot specify the data_type",
        )

        response = self.get("/public_download/?data=sample_information&prep_id=1")
        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.reason, "Review your parameters, not a valid combination"
        )

        response = self.get("/public_download/?data=sample_information&study_id=10000")
        self.assertEqual(response.code, 422)
        self.assertEqual(response.reason, "Sample information does not exist")

        response = self.get("/public_download/?data=prep_information&prep_id=10000")
        self.assertEqual(response.code, 422)
        self.assertEqual(response.reason, "Preparation information does not exist")

        response = self.get("/public_download/?data=sample_information&study_id=1")
        self.assertEqual(response.code, 200)
        exp = (
            "[0-9]* [0-9]* /protected/templates/1_[0-9]*-[0-9]*.txt "
            "templates/1_[0-9]*-[0-9]*.txt\n"
        )
        self.assertRegex(response.body.decode("ascii"), exp)

        response = self.get("/public_download/?data=prep_information&prep_id=1")
        self.assertEqual(response.code, 200)
        exp = (
            "- [0-9]* /protected/templates/1_prep_1_qiime_[0-9]*-[0-9]"
            "*.txt templates/1_prep_1_qiime_[0-9]*-[0-9]*.txt\n"
        )
        self.assertRegex(response.body.decode("ascii"), exp)


class TestDownloadPublicArtifactHandler(TestHandlerBase):
    def test_download(self):
        # check failures
        response = self.get("/public_artifact_download/")
        self.assertEqual(response.code, 422)
        self.assertEqual(response.reason, "You need to specify an artifact id")

        response = self.get("/public_artifact_download/?artifact_id=10000")
        self.assertEqual(response.code, 404)
        self.assertEqual(response.reason, "Artifact does not exist")

        response = self.get("/public_artifact_download/?artifact_id=3")
        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.reason,
            "Artifact is not public. If this is a mistake contact: foo@bar.com",
        )

        # check success
        Artifact(5).visibility = "public"
        response = self.get("/public_artifact_download/?artifact_id=5")
        self.assertEqual(response.code, 200)
        exp = (
            "- [0-9]* /protected/processed_data/"
            "1_study_1001_closed_reference_otu_table.biom "
            "processed_data/1_study_1001_closed_reference_otu_table.biom\n"
            "- [0-9]* /protected/templates/1_prep_1_qiime_19700101-000000.txt "
            "mapping_files/5_mapping_file.txt"
        )
        self.assertRegex(response.body.decode("ascii"), exp)

        # Now let's check download prep with no raw data access
        response = self.get("/public_download/?data=raw&prep_id=1")
        self.assertTrue(response.reason.startswith("No raw data access."))

        # Now success
        Study(1).public_raw_download = True
        response = self.get("/public_download/?data=raw&prep_id=1")
        self.assertEqual(response.code, 200)
        exp = (
            "- [0-9]* /protected/raw_data/1_s_G1_L001_sequences.fastq.gz "
            "raw_data/1_s_G1_L001_sequences.fastq.gz\n- [0-9]* /protected"
            "/raw_data/1_s_G1_L001_sequences_barcodes.fastq.gz raw_data/"
            "1_s_G1_L001_sequences_barcodes.fastq.gz\n- [0-9]* /protected/"
            "templates/1_prep_1_qiime_19700101-000000.txt mapping_files/"
            "1_mapping_file.txt\n"
        )
        self.assertRegex(response.body.decode("ascii"), exp)

        # for simplicity, let's just check respose.code
        response = self.get("/public_download/?data=biom&prep_id=1")
        self.assertEqual(response.code, 200)

    def test_download_sample_information(self):
        response = self.get("/public_artifact_download/")
        self.assertEqual(response.code, 422)
        self.assertEqual(response.reason, "You need to specify an artifact id")


class TestDownloadPrivateArtifactHandler(TestHandlerBase):
    def test_download(self):
        # you can't post None, you must post an empty byte array
        response = self.post("/private_download/1", b"")
        self.assertEqual(response.code, 200)

        resp_dict = json.loads(response.body)
        o = urlparse(resp_dict["url"])
        response_file = self.get(o.path)
        self.assertEqual(response_file.code, 200)
        exp = (
            "- 58 /protected/raw_data/1_s_G1_L001_sequences.fastq.gz "
            "raw_data/1_s_G1_L001_sequences.fastq.gz\n"
            "- 58 /protected/raw_data/1_s_G1_L001_sequences_barcodes."
            "fastq.gz raw_data/1_s_G1_L001_sequences_barcodes.fastq.gz\n"
            "- [0-9]* /protected/templates/1_prep_1_qiime_19700101-000000.txt "
            "mapping_files/1_mapping_file.txt\n"
        )
        self.assertRegex(response_file.body.decode("ascii"), exp)


if __name__ == "__main__":
    main()
