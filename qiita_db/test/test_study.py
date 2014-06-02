from unittest import TestCase, main
from datetime import date

from qiita_db.study import Study, StudyPerson
from qiita_db.investigation import Investigation
from qiita_db.data import PreprocessedData, RawData, ProcessedData
from qiita_db.user import User
from qiita_core.util import qiita_test_checker
from qiita_db.exceptions import QiitaDBExecutionError
from qiita_db.sql_connection import SQLConnectionHandler


# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

@qiita_test_checker()
class TestStudyPerson(TestCase):
    def setUp(self):
        self.studyperson = StudyPerson(1)

    def test_create_studyperson(self):
        new = StudyPerson.create('SomeDude', 'somedude@foo.bar',
                                 '111 fake street', '111-121-1313')
        self.assertEqual(new.id, 4)
        conn = SQLConnectionHandler()
        obs = conn.execute_fetchone("SELECT * FROM qiita.study_person WHERE "
                                    "study_person_id = 4")
        self.assertEqual(obs["study_person_id"], 4)
        self.assertEqual(obs["email"], 'somedude@foo.bar')
        self.assertEqual(obs["name"], 'SomeDude')
        self.assertEqual(obs["address"], '111 fake street')
        self.assertEqual(obs["phone"], '111-121-1313')

    def test_create_studyperson_already_exists(self):
        new = StudyPerson.create('LabDude', 'lab_dude@foo.bar')
        self.assertEqual(new.id, 1)
        conn = SQLConnectionHandler()
        obs = conn.execute_fetchone("SELECT * FROM qiita.study_person WHERE "
                                    "study_person_id = 1")
        self.assertEqual(obs["study_person_id"], 1)
        self.assertEqual(obs["email"], 'lab_dude@foo.bar')
        self.assertEqual(obs["name"], 'LabDude')
        self.assertEqual(obs["address"], '123 lab street')
        self.assertEqual(obs["phone"], '121-222-3333')

    def test_retrieve_name(self):
        self.assertEqual(self.studyperson.name, 'LabDude')

    def test_set_name(self):
        self.studyperson.name = 'NewDude'
        self.assertEqual(self.studyperson.name, 'NewDude')

    def test_retrieve_email(self):
        self.assertEqual(self.studyperson.email, 'lab_dude@foo.bar')

    def test_set_email(self):
        self.studyperson.email = 'new@foo.bar'
        self.assertEqual(self.studyperson.email, 'new@foo.bar')

    def test_retrieve_address(self):
        self.assertEqual(self.studyperson.address, '123 lab street')

    def test_set_address(self):
        self.studyperson.address = '123 nonsense road'
        self.assertEqual(self.studyperson.address, '123 nonsense road')

    def test_retrieve_phone(self):
        self.assertEqual(self.studyperson.phone, '121-222-3333')

    def test_set_phone(self):
        self.studyperson.phone = '111111111111111111111'
        self.assertEqual(self.studyperson.phone, '111111111111111111111')


@qiita_test_checker()
class TestStudy(TestCase):
    def setUp(self):
        self.study = Study(1)

        self.info = {
            "timeseries_type_id": 1,
            "study_experimental_factor": [1, 2],
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "portal_type_id": 3,
            "study_title": "Fried chicken microbiome",
            "study_alias": "FCM",
            "study_description": ("Microbiome of people who eat nothing but "
                                  "fried chicken"),
            "study_abstract": ("We wanted to see if we could get funding for "
                               "giving people heart attacks"),
            "emp_person_id": StudyPerson(2),
            "principal_investigator_id": StudyPerson(3),
            "lab_person_id": StudyPerson(1)
        }

    def test_create_study_min_data(self):
        """Insert a study into the database"""
        obs = Study.create(User('test@foo.bar'), self.info)
        self.assertEqual(obs.id, 2)
        exp = {'mixs_compliant': True, 'metadata_complete': True,
               'reprocess': False, 'study_status_id': 1,
               'number_samples_promised': 28, 'emp_person_id': 2,
               'funding': None, 'vamps_id': None,
               'first_contact': date.today().strftime("%B %d, %Y"),
               'principal_investigator_id': 3, 'timeseries_type_id': 1,
               'study_abstract': ('We wanted to see if we could get funding '
                                  'for giving people heart attacks'),
               'email': 'test@foo.bar', 'spatial_series': None,
               'study_description': ('Microbiome of people who eat nothing but'
                                     ' fried chicken'),
               'portal_type_id': 3, 'study_alias': 'FCM', 'study_id': 2,
               'most_recent_contact': None, 'lab_person_id': 1,
               'study_title': 'Fried chicken microbiome',
               'number_samples_collected': 25}
        conn = SQLConnectionHandler()
        obsins = dict(conn.execute_fetchone("SELECT * FROM qiita.study WHERE "
                                            "study_id = 2"))
        self.assertEqual(obsins, exp)

        # make sure EFO went in to table correctly
        efo = conn.execute_fetchall("SELECT efo_id FROM "
                                    "qiita.study_experimental_factor WHERE "
                                    "study_id = 2")
        obsefo = [x[0] for x in efo]
        self.assertEqual(obsefo, [1, 2])

    def test_create_study_with_investigation(self):
        """Insert a study into the database with an investigation"""
        obs = Study.create(User('test@foo.bar'), self.info, Investigation(1))
        self.assertEqual(obs.id, 2)
        # check the investigation was assigned
        conn = SQLConnectionHandler()
        obs3 = conn.execute_fetchall("SELECT * from qiita.investigation_study "
                                     "WHERE study_id = 2")
        self.assertEqual(obs3, [[1, 2]])

    def test_create_study_all_data(self):
        """Insert a study into the database with every info field"""
        self.info.update({
            'vamps_id': 1111111,
            'funding': 'FundAgency',
            'spatial_series': True,
            'metadata_complete': False,
            })
        obs = Study.create(User('test@foo.bar'), self.info)
        self.assertEqual(obs.id, 2)
        exp = {'mixs_compliant': True, 'metadata_complete': False,
               'reprocess': False, 'study_status_id': 1,
               'number_samples_promised': 28, 'emp_person_id': 2,
               'funding': 'FundAgency', 'vamps_id': '1111111',
               'first_contact': 'May 30, 2014',
               'principal_investigator_id': 3, 'timeseries_type_id': 1,
               'study_abstract': ('We wanted to see if we could get funding '
                                  'for giving people heart attacks'),
               'email': 'test@foo.bar', 'spatial_series': True,
               'study_description': ('Microbiome of people who eat nothing '
                                     'but fried chicken'),
               'portal_type_id': 3, 'study_alias': 'FCM', 'study_id': 2,
               'most_recent_contact': None, 'lab_person_id': 1,
               'study_title': 'Fried chicken microbiome',
               'number_samples_collected': 25}
        conn = SQLConnectionHandler()
        obsins = dict(conn.execute_fetchone("SELECT * FROM qiita.study WHERE "
                                            "study_id = 2"))
        self.assertEqual(obsins, exp)

        # make sure EFO went in to table correctly
        efo = conn.execute_fetchall("SELECT efo_id FROM "
                                    "qiita.study_experimental_factor WHERE "
                                    "study_id = 2")
        obsefo = [x[0] for x in efo]
        self.assertEqual(obsefo, [1, 2])

    def test_delete_study(self):
        raise NotImplementedError()

    def test_insert_missing_requred(self):
        """ Insert a study that is missing a required info key"""
        self.info.pop("study_title")
        self.assertRaises(RuntimeError, Study.create, 'test@foo.bar',
                          self.info)

    def test_insert_unknown_db_col(self):
        """ Insert a study with an info key not in the database"""
        self.info["SHOULDNOTBEHERE"] = "BWAHAHAHAHAHA"
        self.assertRaises(QiitaDBExecutionError, Study.create, 'test@foo.bar',
                          self.info)

    def test_retrieve_title(self):
        self.assertEqual(self.study.title, ('Identification of the Microbiomes'
                                            ' for Cannabis Soils'))

    def test_set_title(self):
        self.study.title = "Weed Soils"
        self.assertEqual(self.study.title, "Weed Soils")

    def test_retrieve_info(self):
        exp = {
            'mixs_compliant': True, 'metadata_complete': True,
            'reprocess': False, 'study_status_id': 2,
            'number_samples_promised': 27, 'emp_person_id': StudyPerson(2),
            'funding': None, 'vamps_id': None,
            'first_contact': '2014-05-19 16:10',
            'principal_investigator_id': StudyPerson(3),
            'timeseries_type_id': 1,
            'study_abstract': ("This is a preliminary study to examine the "
                               "microbiota associated with the Cannabis plant."
                               " Soils samples from the bulk soil, soil "
                               "associated with the roots, and the rhizosphere"
                               " were extracted and the DNA sequenced. Roots "
                               "from three independent plants of different "
                               "strains were examined. These roots were "
                               "obtained November 11, 2011 from plants that "
                               "had been harvested in the summer. Future "
                               "studies will attempt to analyze the soils and "
                               "rhizospheres from the same location at diff"
                               "erent time points in the plant lifecycle."),
            'email': User('test@foo.bar'), 'spatial_series': False,
            'study_description': ('Analysis of the Cannabis Plant Microbiome'),
            'study_experimental_factor': [1], 'portal_type_id': 2,
            'study_alias': 'Cannabis Soils',
            'most_recent_contact': '2014-05-19 16:11',
            'lab_person_id': StudyPerson(1),
            'study_title': ('Identification of the Microbiomes for Cannabis '
                            'Soils'),
            'number_samples_collected': 27}
        self.assertEqual(self.study.info, exp)

    def test_set_info(self):
        newinfo = {
            "timeseries_type_id": 2,
            "study_experimental_factor": [3, 4],
            "metadata_complete": False,
            "number_samples_collected": 28,
            "lab_person_id": StudyPerson(2)
        }

        exp = {
            'mixs_compliant': True, 'metadata_complete': False,
            'reprocess': False, 'study_status_id': 2,
            'number_samples_promised': 27, 'emp_person_id': StudyPerson(2),
            'funding': None, 'vamps_id': None,
            'first_contact': '2014-05-19 16:10',
            'principal_investigator_id': StudyPerson(3),
            'timeseries_type_id': 1,
            'study_abstract': ("This is a preliminary study to examine the "
                               "microbiota associated with the Cannabis plant."
                               " Soils samples from the bulk soil, soil "
                               "associated with the roots, and the rhizosphere"
                               " were extracted and the DNA sequenced. Roots "
                               "from three independent plants of different "
                               "strains were examined. These roots were "
                               "obtained November 11, 2011 from plants that "
                               "had been harvested in the summer. Future "
                               "studies will attempt to analyze the soils and "
                               "rhizospheres from the same location at diff"
                               "erent time points in the plant lifecycle."),
            'email': User('test@foo.bar'), 'spatial_series': False,
            'study_description': ('Analysis of the Cannabis Plant Microbiome'),
            'study_experimental_factor': [1, 3, 4], 'portal_type_id': 2,
            'study_alias': 'Cannabis Soils',
            'most_recent_contact': '2014-05-19 16:11',
            'lab_person_id': StudyPerson(2),
            'study_title': ('Identification of the Microbiomes for Cannabis '
                            'Soils'),
            'number_samples_collected': 28}

        self.study.info = newinfo
        self.assertEqual(self.study.info, exp)

    def test_retrieve_status(self):
        self.assertEqual(self.study.status, 2)

    def test_set_status(self):
        self.study.status = 1
        self.assertEqual(self.study.status, 1)

    def test_retrieve_sample_ids(self):
        exp = set(['SKB8.640193', 'SKD8.640184', 'SKB7.640196', 'SKM9.640192',
                   'SKM4.640180', 'SKM5.640177', 'SKB5.640181', 'SKD6.640190',
                   'SKB2.640194', 'SKD2.640178', 'SKM7.640188', 'SKB1.640202',
                   'SKD1.640179', 'SKD3.640198', 'SKM8.640201', 'SKM2.640199',
                   'SKB9.640200', 'SKD5.640186', 'SKM3.640197', 'SKD9.640182',
                   'SKB4.640189', 'SKD7.640191', 'SKM6.640187', 'SKD4.640185',
                   'SKB3.640195', 'SKB6.640176', 'SKM1.640183'])
        obs = set(self.study.sample_ids)
        self.assertEqual(obs, exp)

    def test_retrieve_shared_with(self):
        self.assertEqual(self.study.shared_with, ['shared@foo.bar'])

    def test_retrieve_pmids(self):
        exp = ['123456', '7891011']
        self.assertEqual(self.study.pmids, exp)

    def test_retrieve_investigations(self):
        self.assertEqual(self.study.investigations, [1])

    def test_retrieve_metadata(self):
        exp = ['LATITUDE', 'ENV_FEATURE', 'Description_duplicate', 'LONGITUDE',
               'TOT_ORG_CARB', 'ANONYMIZED_NAME', 'PH', 'COUNTRY', 'ENV_BIOME',
               'ALTITUDE', 'SAMP_SALINITY', 'TOT_NITRO', 'TEMP', 'ELEVATION',
               'WATER_CONTENT_SOIL', 'COMMON_NAME', 'HOST_TAXID', 'DEPTH',
               'TAXON_ID', 'TEXTURE', 'ASSIGNED_FROM_GEO',
               'SEASON_ENVIRONMENT', 'sample_id']
        self.assertEqual(self.study.metadata, exp)

    def test_retrieve_raw_data(self):
        self.assertEqual(self.raw_data, [RawData(1)])

    def test_retrieve_preprocessed_data(self):
        self.assertEqual(self.preprocessed_data, [PreprocessedData(1)])

    def test_retrieve_processed_data(self):
        self.assertEqual(self.processed_data, [ProcessedData(1)])

    def test_share_with(self):
        self.study.share_with('admin@foo.bar')
        self.assertEqual(self.study.shared_with, ['shared@foo.bar',
                                                  'admin@foo.bar'])

    def test_add_pmid(self):
        self.study.add_pmid("4544444")
        exp = ['123456', '7891011', '4544444']
        self.assertEqual(self.study.pmids, exp)


if __name__ == "__main__":
    main()
