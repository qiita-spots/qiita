# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os import remove
from os.path import exists, join
from tarfile import open as topen
from unittest import TestCase, main

import numpy.testing as npt
import pandas as pd

import qiita_db as qdb
from qiita_core.qiita_settings import qiita_config, r_client
from qiita_core.util import qiita_test_checker


@qiita_test_checker()
class MetaUtilTests(TestCase):
    def setUp(self):
        self.old_portal = qiita_config.portal
        self.files_to_remove = []

    def tearDown(self):
        qiita_config.portal = self.old_portal
        for fp in self.files_to_remove:
            if exists(fp):
                remove(fp)

    def _set_artifact_private(self):
        id_status = qdb.util.convert_to_id("private", "visibility")
        qdb.sql_connection.perform_as_transaction(
            "UPDATE qiita.artifact SET visibility_id = %d" % id_status
        )

    def _set_artifact_public(self):
        id_status = qdb.util.convert_to_id("public", "visibility")
        qdb.sql_connection.perform_as_transaction(
            "UPDATE qiita.artifact SET visibility_id = %d" % id_status
        )

    def test_validate_filepath_access_by_user(self):
        self._set_artifact_private()

        # shared has access to all study files and analysis files
        user = qdb.user.User("shared@foo.bar")
        for i in [1, 2, 3, 4, 5, 9, 12, 15, 16, 17, 18, 19, 20, 21]:
            self.assertTrue(qdb.meta_util.validate_filepath_access_by_user(user, i))

        # Now shared should not have access to the study files
        qdb.study.Study(1).unshare(user)
        for i in [1, 2, 3, 4, 5, 9, 12, 17, 18, 19, 20, 21]:
            self.assertFalse(qdb.meta_util.validate_filepath_access_by_user(user, i))

        # Note that 15 is the biom from the analysis and 16 is the
        # analysis mapping file and here we are testing access
        for i in [15, 16]:
            self.assertTrue(qdb.meta_util.validate_filepath_access_by_user(user, i))

        # Now shared should not have access to any files
        qdb.analysis.Analysis(1).unshare(user)
        for i in [1, 2, 3, 4, 5, 9, 12, 15, 16, 17, 18, 19, 20, 21]:
            self.assertFalse(qdb.meta_util.validate_filepath_access_by_user(user, i))

        # Now the Analysis is public so the user should have access again. Note
        # that we are not using the internal Analysis methods to skip
        # validation; thus simplifying the test code
        for a in qdb.analysis.Analysis(1).artifacts:
            a.visibility = "public"
        # Note that 15 is the biom from the analysis and 16 is the
        # analysis mapping file and here we are testing access
        for i in [15, 16]:
            self.assertTrue(qdb.meta_util.validate_filepath_access_by_user(user, i))
        # returning to private
        for a in qdb.analysis.Analysis(1).artifacts:
            a.visibility = "private"

        # Now shared has access to public study files
        self._set_artifact_public()
        for i in [1, 2, 3, 4, 5, 9, 12, 17, 18, 19, 20, 21]:
            obs = qdb.meta_util.validate_filepath_access_by_user(user, i)
            if i < 3:
                self.assertFalse(obs)
            else:
                self.assertTrue(obs)

        # testing that if study.public_raw_download is true we get access
        qdb.study.Study(1).public_raw_download = True
        for i in [1, 2, 3]:
            obs = qdb.meta_util.validate_filepath_access_by_user(user, i)
            self.assertTrue(obs)
        qdb.study.Study(1).public_raw_download = False

        # Test that it doesn't break: if the SampleTemplate hasn't been added
        info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "study_alias": "TestStudy",
            "study_description": "Description of a test study",
            "study_abstract": "No abstract right now...",
            "principal_investigator_id": 1,
            "lab_person_id": 1,
        }
        study = qdb.study.Study.create(
            qdb.user.User("test@foo.bar"), "Test study", info
        )
        for i in [1, 2, 3, 4, 5, 9, 12, 17, 18, 19, 20, 21]:
            obs = qdb.meta_util.validate_filepath_access_by_user(user, i)
            if i < 3:
                self.assertFalse(obs)
            else:
                self.assertTrue(obs)

        # test in case there is a prep template that failed
        qdb.sql_connection.perform_as_transaction(
            "INSERT INTO qiita.prep_template (data_type_id) VALUES (2)"
        )
        for i in [1, 2, 3, 4, 5, 9, 12, 17, 18, 19, 20, 21]:
            obs = qdb.meta_util.validate_filepath_access_by_user(user, i)
            if i < 3:
                self.assertFalse(obs)
            else:
                self.assertTrue(obs)

        # admin should have access to everything
        admin = qdb.user.User("admin@foo.bar")
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add("SELECT filepath_id FROM qiita.filepath")
            fids = qdb.sql_connection.TRN.execute_fetchflatten()
        for i in fids:
            self.assertTrue(qdb.meta_util.validate_filepath_access_by_user(admin, i))

        # testing access to a prep info file without artifacts
        # returning artifacts to private
        self._set_artifact_private()
        PT = qdb.metadata_template.prep_template.PrepTemplate
        md_dict = {
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
        md = pd.DataFrame.from_dict(md_dict, orient="index", dtype=str)
        # creating prep info on Study(1), which is our default Study
        pt = npt.assert_warns(
            qdb.exceptions.QiitaDBWarning, PT.create, md, qdb.study.Study(1), "18S"
        )
        for idx, _ in pt.get_filepaths():
            self.assertFalse(qdb.meta_util.validate_filepath_access_by_user(user, idx))

        # returning to original sharing
        PT.delete(pt.id)
        qdb.study.Study(1).share(user)
        qdb.analysis.Analysis(1).share(user)
        qdb.study.Study.delete(study.id)

    def test_get_lat_longs(self):
        # no public studies should return an empty array
        obs = qdb.meta_util.get_lat_longs()
        self.assertCountEqual(obs, [])

        old_visibility = {}
        for pt in qdb.study.Study(1).prep_templates():
            old_visibility[pt] = pt.artifact.visibility
            pt.artifact.visibility = "public"
        exp = [
            [1, 74.0894932572, 65.3283470202],
            [1, 57.571893782, 32.5563076447],
            [1, 13.089194595, 92.5274472082],
            [1, 12.7065957714, 84.9722975792],
            [1, 44.9725384282, 66.1920014699],
            [1, 10.6655599093, 70.784770579],
            [1, 29.1499460692, 82.1270418227],
            [1, 35.2374368957, 68.5041623253],
            [1, 53.5050692395, 31.6056761814],
            [1, 60.1102854322, 74.7123248382],
            [1, 4.59216095574, 63.5115213108],
            [1, 68.0991287718, 34.8360987059],
            [1, 84.0030227585, 66.8954849864],
            [1, 3.21190859967, 26.8138925876],
            [1, 82.8302905615, 86.3615778099],
            [1, 12.6245524972, 96.0693176066],
            [1, 85.4121476399, 15.6526750776],
            [1, 23.1218032799, 42.838497795],
            [1, 43.9614715197, 82.8516734159],
            [1, 68.51099627, 2.35063674718],
            [1, 0.291867635913, 68.5945325743],
            [1, 40.8623799474, 6.66444220187],
            [1, 95.2060749748, 27.3592668624],
            [1, 78.3634273709, 74.423907894],
            [1, 38.2627021402, 3.48274264219],
        ]
        obs = qdb.meta_util.get_lat_longs()
        self.assertCountEqual(obs, exp)

        for k, v in old_visibility.items():
            k.artifact.visibility = v

    def test_get_lat_longs_EMP_portal(self):
        info = {
            "timeseries_type_id": 1,
            "lab_person_id": None,
            "principal_investigator_id": 3,
            "metadata_complete": False,
            "mixs_compliant": True,
            "study_description": "desc",
            "study_alias": "alias",
            "study_abstract": "abstract",
        }

        study = qdb.study.Study.create(
            qdb.user.User("test@foo.bar"), "test_study_1", info=info
        )
        qdb.portal.Portal("EMP").add_studies([study.id])

        md = {
            "my.sample": {
                "physical_specimen_location": "location1",
                "physical_specimen_remaining": True,
                "dna_extracted": True,
                "sample_type": "type1",
                "collection_timestamp": "2014-05-29 12:24:51",
                "host_subject_id": "NotIdentified",
                "Description": "Test Sample 4",
                "str_column": "Value for sample 4",
                "int_column": 4,
                "latitude": 42.42,
                "longitude": 41.41,
                "taxon_id": 9606,
                "scientific_name": "homo sapiens",
            }
        }

        md_ext = pd.DataFrame.from_dict(md, orient="index", dtype=str)
        st = qdb.metadata_template.sample_template.SampleTemplate.create(md_ext, study)

        qiita_config.portal = "EMP"

        obs = qdb.meta_util.get_lat_longs()
        exp = []

        self.assertCountEqual(obs, exp)
        qdb.metadata_template.sample_template.SampleTemplate.delete(st.id)
        qdb.study.Study.delete(study.id)

    def test_update_redis_stats(self):
        # helper function to get the values in the stats_daily table
        def _get_daily_stats():
            with qdb.sql_connection.TRN:
                qdb.sql_connection.TRN.add("SELECT * FROM qiita.stats_daily")
                return qdb.sql_connection.TRN.execute_fetchindex()

        # checking empty status of stats in DB
        self.assertEqual([], _get_daily_stats())

        # generate daily stats
        qdb.meta_util.update_redis_stats()

        portal = qiita_config.portal
        # let's first test the dictionaries
        vals = [
            (
                "number_studies",
                {b"sandbox": b"0", b"public": b"0", b"private": b"1"},
                r_client.hgetall,
            ),
            (
                "number_of_samples",
                {b"sandbox": b"0", b"public": b"0", b"private": b"27"},
                r_client.hgetall,
            ),
            ("per_data_type_stats", {b"No data": b"0"}, r_client.hgetall),
        ]
        for k, exp, f in vals:
            redis_key = "%s:stats:%s" % (portal, k)
            self.assertDictEqual(f(redis_key), exp)
        # then the unique values
        vals = [
            ("num_users", b"7", r_client.get),
            ("lat_longs", b"[]", r_client.get),
            ("num_studies_ebi", b"1", r_client.get),
            ("num_samples_ebi", b"27", r_client.get),
            ("number_samples_ebi_prep", b"54", r_client.get),
            ("num_processing_jobs", b"474", r_client.get),
            # not testing img/time for simplicity
            # ('img', r_client.get),
            # ('time', r_client.get)
        ]
        # checking empty status of stats in DB
        db_stats = _get_daily_stats()
        # there should be only one set of values
        self.assertEqual(1, len(db_stats))
        db_stats = dict(db_stats[0])

        for k, exp, f in vals:
            redis_key = "%s:stats:%s" % (portal, k)
            # checking redis values
            self.assertEqual(f(redis_key), exp)
            # checking DB values; note that redis stores all values as bytes,
            # thus we have to convert what's in the DB to bytes
            self.assertEqual(f(redis_key), str.encode(str(db_stats["stats"][k])))

        # regenerating stats to make sure that we have 2 rows in the DB
        qdb.meta_util.update_redis_stats()

        db_stats = _get_daily_stats()
        # there should be only one set of values
        self.assertEqual(2, len(db_stats))

    def test_generate_biom_and_metadata_release(self):
        level = "private"
        qdb.meta_util.generate_biom_and_metadata_release(level)
        portal = qiita_config.portal
        working_dir = qiita_config.working_dir

        vals = [
            ("filepath", r_client.get),
            ("md5sum", r_client.get),
            ("time", r_client.get),
        ]
        # we are storing the [0] filepath, [1] md5sum and [2] time but we are
        # only going to check the filepath contents so ignoring the others
        tgz = vals[0][1]("%s:release:%s:%s" % (portal, level, vals[0][0]))
        tgz = join(working_dir, tgz.decode("ascii"))

        self.files_to_remove.extend([tgz])

        tmp = topen(tgz, "r:gz")
        tgz_obs = [ti.name for ti in tmp]
        tmp.close()
        # files names might change due to updates and patches so just check
        # that the prefix exists.
        fn = "processed_data/1_study_1001_closed_reference_otu_table.biom"
        self.assertTrue(fn in tgz_obs)
        tgz_obs.remove(fn)
        # yes, this file is there twice
        self.assertTrue(fn in tgz_obs)
        tgz_obs.remove(fn)
        # let's check the next biom
        fn = "processed_data/1_study_1001_closed_reference_otu_table_Silva.biom"
        self.assertTrue(fn in tgz_obs)
        tgz_obs.remove(fn)
        # now let's check prep info files based on their suffix, just take
        # the first one and check/rm the occurances of that file
        fn_prep = [f for f in tgz_obs if f.startswith("templates/1_prep_1_")][0]
        # 3 times
        self.assertTrue(fn_prep in tgz_obs)
        tgz_obs.remove(fn_prep)
        self.assertTrue(fn_prep in tgz_obs)
        tgz_obs.remove(fn_prep)
        self.assertTrue(fn_prep in tgz_obs)
        tgz_obs.remove(fn_prep)
        fn_sample = [f for f in tgz_obs if f.startswith("templates/1_")][0]
        # 3 times
        self.assertTrue(fn_sample in tgz_obs)
        tgz_obs.remove(fn_sample)
        self.assertTrue(fn_sample in tgz_obs)
        tgz_obs.remove(fn_sample)
        self.assertTrue(fn_sample in tgz_obs)
        tgz_obs.remove(fn_sample)
        # now we should only have the text file
        txt = tgz_obs.pop()
        # now it should be empty
        self.assertEqual(tgz_obs, [])

        tmp = topen(tgz, "r:gz")
        fhd = tmp.extractfile(txt)
        txt_obs = [line.decode("ascii") for line in fhd.readlines()]
        tmp.close()
        txt_exp = [
            "biom fp\tsample fp\tprep fp\tqiita artifact id\tplatform\t"
            "target gene\tmerging scheme\tartifact software\t"
            "parent software\n",
            "processed_data/1_study_1001_closed_reference_otu_table.biom\t"
            "%s\t%s\t4\tIllumina\t16S rRNA\t"
            "Pick closed-reference OTUs | Split libraries FASTQ\t"
            "QIIMEq2 v1.9.1\tQIIMEq2 v1.9.1\n" % (fn_sample, fn_prep),
            "processed_data/1_study_1001_closed_reference_otu_table.biom\t"
            "%s\t%s\t5\tIllumina\t16S rRNA\t"
            "Pick closed-reference OTUs | Split libraries FASTQ\t"
            "QIIMEq2 v1.9.1\tQIIMEq2 v1.9.1\n" % (fn_sample, fn_prep),
            "processed_data/1_study_1001_closed_reference_otu_table_Silva.bio"
            "m\t%s\t%s\t6\tIllumina\t16S rRNA\t"
            "Pick closed-reference OTUs | Split libraries FASTQ\t"
            "QIIMEq2 v1.9.1\tQIIMEq2 v1.9.1" % (fn_sample, fn_prep),
        ]
        self.assertEqual(txt_obs, txt_exp)

        # whatever the configuration was, we will change to settings so we can
        # test the other option when dealing with the end '/'
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add("SELECT base_data_dir FROM settings")
            obdr = qdb.sql_connection.TRN.execute_fetchlast()
            if obdr[-1] == "/":
                bdr = obdr[:-1]
            else:
                bdr = obdr + "/"

            qdb.sql_connection.TRN.add("UPDATE settings SET base_data_dir = '%s'" % bdr)
            bdr = qdb.sql_connection.TRN.execute()

        qdb.meta_util.generate_biom_and_metadata_release(level)
        # we are storing the [0] filepath, [1] md5sum and [2] time but we are
        # only going to check the filepath contents so ignoring the others
        tgz = vals[0][1]("%s:release:%s:%s" % (portal, level, vals[0][0]))
        tgz = join(working_dir, tgz.decode("ascii"))

        tmp = topen(tgz, "r:gz")
        tgz_obs = [ti.name for ti in tmp]
        tmp.close()
        # files names might change due to updates and patches so just check
        # that the prefix exists.
        fn = "processed_data/1_study_1001_closed_reference_otu_table.biom"
        self.assertTrue(fn in tgz_obs)
        tgz_obs.remove(fn)
        # yes, this file is there twice
        self.assertTrue(fn in tgz_obs)
        tgz_obs.remove(fn)
        # let's check the next biom
        fn = "processed_data/1_study_1001_closed_reference_otu_table_Silva.biom"
        self.assertTrue(fn in tgz_obs)
        tgz_obs.remove(fn)
        # now let's check prep info files based on their suffix, just take
        # the first one and check/rm the occurances of that file
        fn_prep = [f for f in tgz_obs if f.startswith("templates/1_prep_1_")][0]
        # 3 times
        self.assertTrue(fn_prep in tgz_obs)
        tgz_obs.remove(fn_prep)
        self.assertTrue(fn_prep in tgz_obs)
        tgz_obs.remove(fn_prep)
        self.assertTrue(fn_prep in tgz_obs)
        tgz_obs.remove(fn_prep)
        fn_sample = [f for f in tgz_obs if f.startswith("templates/1_")][0]
        # 3 times
        self.assertTrue(fn_sample in tgz_obs)
        tgz_obs.remove(fn_sample)
        self.assertTrue(fn_sample in tgz_obs)
        tgz_obs.remove(fn_sample)
        self.assertTrue(fn_sample in tgz_obs)
        tgz_obs.remove(fn_sample)
        # now we should only have the text file
        txt = tgz_obs.pop()
        # now it should be empty
        self.assertEqual(tgz_obs, [])

        tmp = topen(tgz, "r:gz")
        fhd = tmp.extractfile(txt)
        txt_obs = [line.decode("ascii") for line in fhd.readlines()]
        tmp.close()

        txt_exp = [
            "biom fp\tsample fp\tprep fp\tqiita artifact id\tplatform\t"
            "target gene\tmerging scheme\tartifact software\t"
            "parent software\n",
            "processed_data/1_study_1001_closed_reference_otu_table.biom\t"
            "%s\t%s\t4\tIllumina\t16S rRNA\t"
            "Pick closed-reference OTUs | Split libraries FASTQ\t"
            "QIIMEq2 v1.9.1\tQIIMEq2 v1.9.1\n" % (fn_sample, fn_prep),
            "processed_data/1_study_1001_closed_reference_otu_table.biom\t"
            "%s\t%s\t5\tIllumina\t16S rRNA\t"
            "Pick closed-reference OTUs | Split libraries FASTQ\t"
            "QIIMEq2 v1.9.1\tQIIMEq2 v1.9.1\n" % (fn_sample, fn_prep),
            "processed_data/1_study_1001_closed_reference_otu_table_Silva.bio"
            "m\t%s\t%s\t6\tIllumina\t16S rRNA\t"
            "Pick closed-reference OTUs | Split libraries FASTQ"
            "\tQIIMEq2 v1.9.1\tQIIMEq2 v1.9.1" % (fn_sample, fn_prep),
        ]
        self.assertEqual(txt_obs, txt_exp)

        # returning configuration
        qdb.sql_connection.perform_as_transaction(
            "UPDATE settings SET base_data_dir = '%s'" % obdr
        )

        # testing public/default release
        qdb.meta_util.generate_biom_and_metadata_release()
        # we are storing the [0] filepath, [1] md5sum and [2] time but we are
        # only going to check the filepath contents so ignoring the others
        tgz = vals[0][1]("%s:release:%s:%s" % (portal, "public", vals[0][0]))
        tgz = join(working_dir, tgz.decode("ascii"))

        tmp = topen(tgz, "r:gz")
        tgz_obs = [ti.name for ti in tmp]
        tmp.close()
        # the public release should only have the txt file
        self.assertEqual(len(tgz_obs), 1)
        txt = tgz_obs.pop()

        tmp = topen(tgz, "r:gz")
        fhd = tmp.extractfile(txt)
        txt_obs = [line.decode("ascii") for line in fhd.readlines()]
        tmp.close()

        # we should only get the header
        txt_exp = [
            "biom fp\tsample fp\tprep fp\tqiita artifact id\tplatform\t"
            "target gene\tmerging scheme\tartifact software\t"
            "parent software"
        ]
        self.assertEqual(txt_obs, txt_exp)

    def test_generate_plugin_releases(self):
        qdb.meta_util.generate_plugin_releases()

        working_dir = qiita_config.working_dir
        tgz = r_client.get("release-archive:filepath")
        with topen(join(working_dir, tgz.decode("ascii")), "r:gz") as tmp:
            tgz_obs = [ti.name for ti in tmp]
        # the expected folder/file in the tgz should be named as the time
        # when it was created so let's test that
        time = (
            r_client.get("release-archive:time")
            .decode("ascii")
            .replace("-", "")
            .replace(":", "")
            .replace(" ", "-")
        )
        self.assertEqual(tgz_obs, [time])

    def test_update_resource_allocation_redis(self):
        cname = "Split libraries FASTQ"
        sname = "QIIMEq2"
        col_name = "samples * columns"
        version = "1.9.1"
        qdb.meta_util.update_resource_allocation_redis(False)
        title_mem_str = "resources$#%s$#%s$#%s$#%s:%s" % (
            cname,
            sname,
            version,
            col_name,
            "title_mem",
        )
        title_mem = str(r_client.get(title_mem_str))
        self.assertTrue(
            "model: (k * (np.log(x))) + "
            "(b * ((np.log(x))**2)) + "
            "(a * ((np.log(x))**2.5))" in title_mem
        )

        title_time_str = "resources$#%s$#%s$#%s$#%s:%s" % (
            cname,
            sname,
            version,
            col_name,
            "title_time",
        )
        title_time = str(r_client.get(title_time_str))
        self.assertTrue(
            "model: (a * ((np.log(x))**3)) + "
            "(b * ((np.log(x))**2)) + "
            "((np.log(x)) * k)" in title_time
        )


if __name__ == "__main__":
    main()
