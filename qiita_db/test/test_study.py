from unittest import TestCase, main
from datetime import datetime

from future.utils import viewitems

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.util import qiita_test_checker
from qiita_db.base import QiitaObject
from qiita_db.study import Study, StudyPerson
from qiita_db.investigation import Investigation
from qiita_db.user import User
from qiita_db.util import convert_to_id
from qiita_db.sql_connection import Transaction
from qiita_db.exceptions import (
    QiitaDBColumnError, QiitaDBStatusError, QiitaDBError,
    QiitaDBUnknownIDError, QiitaDBDuplicateError)

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
        new = StudyPerson.create('SomeDude', 'somedude@foo.bar', 'affil',
                                 '111 fake street', '111-121-1313')
        self.assertEqual(new.id, 4)
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study_person WHERE study_person_id = 4")
        self.assertEqual(obs, [[4, 'SomeDude', 'somedude@foo.bar', 'affil',
                         '111 fake street', '111-121-1313']])

    def test_iter(self):
        """Make sure that each and every StudyPerson is retrieved"""
        expected = [
            ('LabDude', 'lab_dude@foo.bar', 'knight lab', '123 lab street',
             '121-222-3333'),
            ('empDude', 'emp_dude@foo.bar', 'broad', None, '444-222-3333'),
            ('PIDude', 'PI_dude@foo.bar', 'Wash U', '123 PI street', None)]
        for i, person in enumerate(StudyPerson.iter()):
            self.assertTrue(person.id == i+1)
            self.assertTrue(person.name == expected[i][0])
            self.assertTrue(person.email == expected[i][1])
            self.assertTrue(person.affiliation == expected[i][2])
            self.assertTrue(person.address == expected[i][3])
            self.assertTrue(person.phone == expected[i][4])

    def test_create_studyperson_already_exists(self):
        obs = StudyPerson.create('LabDude', 'lab_dude@foo.bar', 'knight lab')
        self.assertEqual(obs.name, 'LabDude')
        self.assertEqual(obs.email, 'lab_dude@foo.bar')

    def test_retrieve_name(self):
        self.assertEqual(self.studyperson.name, 'LabDude')

    def test_set_name_fail(self):
        with self.assertRaises(AttributeError):
            self.studyperson.name = 'Fail Dude'

    def test_retrieve_email(self):
        self.assertEqual(self.studyperson.email, 'lab_dude@foo.bar')

    def test_retrieve_affiliation(self):
        self.assertEqual(self.studyperson.affiliation, 'knight lab')

    def test_set_email_fail(self):
        with self.assertRaises(AttributeError):
            self.studyperson.email = 'faildude@foo.bar'

    def test_set_affiliation_fail(self):
        with self.assertRaises(AttributeError):
            self.studyperson.affiliation = 'squire lab'

    def test_retrieve_address(self):
        self.assertEqual(self.studyperson.address, '123 lab street')

    def test_retrieve_address_null(self):
        person = StudyPerson(2)
        self.assertEqual(person.address, None)

    def test_set_address(self):
        self.studyperson.address = '123 nonsense road'
        self.assertEqual(self.studyperson.address, '123 nonsense road')

    def test_retrieve_phone(self):
        self.assertEqual(self.studyperson.phone, '121-222-3333')

    def test_retrieve_phone_null(self):
        person = StudyPerson(3)
        self.assertEqual(person.phone, None)

    def test_set_phone(self):
        self.studyperson.phone = '111111111111111111121'
        self.assertEqual(self.studyperson.phone, '111111111111111111121')


@qiita_test_checker()
class TestStudy(TestCase):
    def setUp(self):
        self.study = Study(1)

        self.info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "portal_type_id": 3,
            "study_alias": "FCM",
            "study_description": "Microbiome of people who eat nothing but "
                                 "fried chicken",
            "study_abstract": "Exploring how a high fat diet changes the "
                              "gut microbiome",
            "emp_person_id": StudyPerson(2),
            "principal_investigator_id": StudyPerson(3),
            "lab_person_id": StudyPerson(1)
        }

        self.infoexp = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "portal_type_id": 3,
            "study_alias": "FCM",
            "study_description": "Microbiome of people who eat nothing but "
                                 "fried chicken",
            "study_abstract": "Exploring how a high fat diet changes the "
                              "gut microbiome",
            "emp_person_id": 2,
            "principal_investigator_id": 3,
            "lab_person_id": 1
        }

        self.existingexp = {
            'mixs_compliant': True,
            'metadata_complete': True,
            'reprocess': False,
            'number_samples_promised': 27,
            'emp_person_id': StudyPerson(2),
            'funding': None,
            'vamps_id': None,
            'first_contact': datetime(2014, 5, 19, 16, 10),
            'principal_investigator_id': StudyPerson(3),
            'timeseries_type_id': 1,
            'study_abstract':
                "This is a preliminary study to examine the "
                "microbiota associated with the Cannabis plant. Soils samples "
                "from the bulk soil, soil associated with the roots, and the "
                "rhizosphere were extracted and the DNA sequenced. Roots "
                "from three independent plants of different strains were "
                "examined. These roots were obtained November 11, 2011 from "
                "plants that had been harvested in the summer. Future "
                "studies will attempt to analyze the soils and rhizospheres "
                "from the same location at different time points in the plant "
                "lifecycle.",
            'spatial_series': False,
            'study_description': 'Analysis of the Cannabis Plant Microbiome',
            'portal_type_id': 2,
            'study_alias': 'Cannabis Soils',
            'most_recent_contact': '2014-05-19 16:11',
            'most_recent_contact': datetime(2014, 5, 19, 16, 11),
            'lab_person_id': StudyPerson(1),
            'number_samples_collected': 27}

    def _change_processed_data_status(self, new_status):
        # Change the status of the studies by changing the status of their
        # processed data
        id_status = convert_to_id(new_status, 'processed_data_status')
        self.conn_handler.execute(
            "UPDATE qiita.processed_data SET processed_data_status_id = %s",
            (id_status,))

    def test_get_info(self):
        # Test get all info for single study
        obs = Study.get_info([1])
        self.assertEqual(len(obs), 1)
        obs = dict(obs[0])
        exp = {
            'mixs_compliant': True, 'metadata_complete': True,
            'reprocess': False, 'timeseries_type': 'None',
            'portal_description': 'EMP portal',
            'number_samples_promised': 27, 'emp_person_id': 2,
            'funding': None, 'vamps_id': None,
            'first_contact': datetime(2014, 5, 19, 16, 10),
            'principal_investigator_id': 3, 'timeseries_type_id': 1,
            'pmid': ['123456', '7891011'], 'study_alias': 'Cannabis Soils',
            'spatial_series': False,
            'study_abstract': 'This is a preliminary study to examine the '
            'microbiota associated with the Cannabis plant. Soils samples from'
            ' the bulk soil, soil associated with the roots, and the '
            'rhizosphere were extracted and the DNA sequenced. Roots from '
            'three independent plants of different strains were examined. '
            'These roots were obtained November 11, 2011 from plants that had '
            'been harvested in the summer. Future studies will attempt to '
            'analyze the soils and rhizospheres from the same location at '
            'different time points in the plant lifecycle.',
            'study_description': 'Analysis of the Cannabis Plant Microbiome',
            'portal': 'EMP',
            'portal_type_id': 2,
            'intervention_type': 'None', 'email': 'test@foo.bar',
            'study_id': 1,
            'most_recent_contact': datetime(2014, 5, 19, 16, 11),
            'lab_person_id': 1,
            'study_title': 'Identification of the Microbiomes for Cannabis '
            'Soils', 'number_samples_collected': 27}
        self.assertItemsEqual(obs, exp)

        # Test get specific keys for single study
        exp_keys = ['metadata_complete', 'reprocess', 'timeseries_type',
                    'portal_description', 'pmid', 'study_title']
        obs = Study.get_info([1], exp_keys)
        self.assertEqual(len(obs), 1)
        obs = dict(obs[0])
        exp = {
            'metadata_complete': True, 'reprocess': False,
            'timeseries_type': 'None',
            'portal_description': 'EMP portal',
            'pmid': ['123456', '7891011'],
            'study_title': 'Identification of the Microbiomes for Cannabis '
            'Soils'}
        self.assertItemsEqual(obs, exp)

        # Test get specific keys for all studies
        info = {
            'timeseries_type_id': 1,
            'portal_type_id': 1,
            'lab_person_id': None,
            'principal_investigator_id': 3,
            'metadata_complete': False,
            'mixs_compliant': True,
            'study_description': 'desc',
            'study_alias': 'alias',
            'study_abstract': 'abstract'}
        user = User('test@foo.bar')

        Study.create(user, 'test_study_1', efo=[1], info=info)
        obs = Study.get_info(info_cols=exp_keys)
        exp = [[True, ['123456', '7891011'], 'EMP portal', False,
                'Identification of the Microbiomes for Cannabis Soils',
                'None'],
               [False, None, 'QIIME portal', False, 'test_study_1', 'None']]
        self.assertEqual(obs, exp)

    def test_has_access_public(self):
        self._change_processed_data_status('public')
        self.assertTrue(self.study.has_access(User("demo@microbio.me")))

    def test_has_access_no_public(self):
        self._change_processed_data_status('public')
        self.assertFalse(self.study.has_access(User("demo@microbio.me"), True))

    def test_owner(self):
        self.assertEqual(self.study.owner(), "test@foo.bar")

        with Transaction("test_owner") as trans:
            self.assertEqual(self.study.owner(trans=trans), "test@foo.bar")

    def test_share(self):
        # Clear all sharing associations
        self._change_processed_data_status('sandbox')
        self.conn_handler.execute("delete from qiita.study_users")
        self.assertEqual(self.study.shared_with(), [])

        # Try to share with the owner, which should not work
        self.study.share(User("test@foo.bar"))
        self.assertEqual(self.study.shared_with(), [])

        with Transaction("test_share") as trans:
            self.study.share(User("test@foo.bar"), trans=trans)
        self.assertEqual(self.study.shared_with(), [])

        # Then share the study with shared@foo.bar
        self.study.share(User("shared@foo.bar"))
        self.assertEqual(self.study.shared_with(), ["shared@foo.bar"])

    def test_unshare(self):
        self._change_processed_data_status('sandbox')
        self.study.unshare(User("shared@foo.bar"))
        self.assertEqual(self.study.shared_with(), [])

    def test_unshare_transaction(self):
        self._change_processed_data_status('sandbox')
        with Transaction("test_unshare_transaction") as trans:
            self.study.unshare(User("shared@foo.bar"), trans=trans)
        self.assertEqual(self.study.shared_with(), [])

    def test_has_access_shared(self):
        self._change_processed_data_status('sandbox')
        self.assertTrue(self.study.has_access(User("shared@foo.bar")))

    def test_has_access_private(self):
        self._change_processed_data_status('sandbox')
        self.assertTrue(self.study.has_access(User("test@foo.bar")))

    def test_has_access_admin(self):
        self._change_processed_data_status('sandbox')
        self.assertTrue(self.study.has_access(User("admin@foo.bar")))

    def test_has_access_no_access(self):
        self._change_processed_data_status('sandbox')
        self.assertFalse(self.study.has_access(User("demo@microbio.me")))

    def test_get_by_status(self):
        obs = Study.get_by_status('sandbox')
        self.assertEqual(obs, set())

        Study.create(User('test@foo.bar'), 'NOT Identification of the '
                     'Microbiomes for Cannabis Soils', [1], self.info)
        obs = Study.get_by_status('private')
        self.assertEqual(obs, {1})

        obs = Study.get_by_status('sandbox')
        self.assertEqual(obs, {2})

        obs = Study.get_by_status('public')
        self.assertEqual(obs, set())

        obs = Study.get_by_status('awaiting_approval')
        self.assertEqual(obs, set())

    def test_exists(self):
        self.assertTrue(Study.exists('Identification of the Microbiomes for '
                                     'Cannabis Soils'))
        self.assertFalse(Study.exists('Not Cannabis Soils'))

        with Transaction("test_exists") as trans:
            self.assertTrue(
                Study.exists('Identification of the Microbiomes for '
                             'Cannabis Soils', trans=trans))
            self.assertFalse(Study.exists('Not Cannabis Soils', trans=trans))

    def test_create_study_min_data(self):
        """Insert a study into the database"""
        before = datetime.now()
        obs = Study.create(User('test@foo.bar'), "Fried chicken microbiome",
                           [1], self.info)
        after = datetime.now()
        self.assertEqual(obs.id, 2)
        exp = {'mixs_compliant': True, 'metadata_complete': True,
               'reprocess': False,
               'number_samples_promised': 28, 'emp_person_id': 2,
               'funding': None, 'vamps_id': None,
               'principal_investigator_id': 3,
               'timeseries_type_id': 1,
               'study_abstract': 'Exploring how a high fat diet changes the '
                                 'gut microbiome',
               'email': 'test@foo.bar', 'spatial_series': None,
               'study_description': 'Microbiome of people who eat nothing but'
                                    ' fried chicken',
               'portal_type_id': 3, 'study_alias': 'FCM', 'study_id': 2,
               'most_recent_contact': None, 'lab_person_id': 1,
               'study_title': 'Fried chicken microbiome',
               'number_samples_collected': 25}

        obsins = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study WHERE study_id = 2")
        self.assertEqual(len(obsins), 1)
        obsins = dict(obsins[0])

        # Check the timestamp separately, since it is set by the database
        # to the microsecond, and we can't predict it a priori
        ins_timestamp = obsins.pop('first_contact')
        self.assertTrue(before < ins_timestamp < after)

        self.assertEqual(obsins, exp)

        # make sure EFO went in to table correctly
        efo = self.conn_handler.execute_fetchall(
            "SELECT efo_id FROM qiita.study_experimental_factor "
            "WHERE study_id = 2")
        self.assertEqual(efo, [[1]])

    def test_create_study_with_investigation(self):
        """Insert a study into the database with an investigation"""
        obs = Study.create(User('test@foo.bar'), "Fried chicken microbiome",
                           [1], self.info, Investigation(1))
        self.assertEqual(obs.id, 2)
        # check the investigation was assigned
        obs = self.conn_handler.execute_fetchall(
            "SELECT * from qiita.investigation_study WHERE study_id = 2")
        self.assertEqual(obs, [[1, 2]])

    def test_create_study_all_data(self):
        """Insert a study into the database with every info field"""
        self.info.update({
            'vamps_id': 'MBE_1111111',
            'funding': 'FundAgency',
            'spatial_series': True,
            'metadata_complete': False,
            'reprocess': True,
            'first_contact': "10/24/2014 12:47PM",
            'study_id': 3827
            })
        obs = Study.create(User('test@foo.bar'), "Fried chicken microbiome",
                           [1], self.info)
        self.assertEqual(obs.id, 3827)
        exp = {'mixs_compliant': True, 'metadata_complete': False,
               'reprocess': True,
               'number_samples_promised': 28, 'emp_person_id': 2,
               'funding': 'FundAgency', 'vamps_id': 'MBE_1111111',
               'first_contact': datetime(2014, 10, 24, 12, 47),
               'principal_investigator_id': 3, 'timeseries_type_id': 1,
               'study_abstract': 'Exploring how a high fat diet changes the '
                                 'gut microbiome',
               'email': 'test@foo.bar', 'spatial_series': True,
               'study_description': 'Microbiome of people who eat nothing '
                                    'but fried chicken',
               'portal_type_id': 3, 'study_alias': 'FCM', 'study_id': 3827,
               'most_recent_contact': None, 'lab_person_id': 1,
               'study_title': 'Fried chicken microbiome',
               'number_samples_collected': 25}
        obsins = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study WHERE study_id = 3827")
        self.assertEqual(len(obsins), 1)
        obsins = dict(obsins[0])
        self.assertEqual(obsins, exp)

        # make sure EFO went in to table correctly
        obsefo = self.conn_handler.execute_fetchall(
            "SELECT efo_id FROM qiita.study_experimental_factor "
            "WHERE study_id = 3827")
        self.assertEqual(obsefo, [[1]])

    def test_create_duplicate(self):
        with self.assertRaises(QiitaDBDuplicateError):
            Study.create(
                User('test@foo.bar'),
                'Identification of the Microbiomes for Cannabis Soils',
                [1], self.info)

    def test_create_missing_required(self):
        """ Insert a study that is missing a required info key"""
        self.info.pop("study_alias")
        with self.assertRaises(QiitaDBColumnError):
            Study.create(User('test@foo.bar'), "Fried Chicken Microbiome",
                         [1], self.info)

    def test_create_empty_efo(self):
        """ Insert a study that is missing a required info key"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            Study.create(User('test@foo.bar'), "Fried Chicken Microbiome",
                         [], self.info)

    def test_create_study_with_not_allowed_key(self):
        """Insert a study with key from _non_info present"""
        self.info.update({"email": "wooo@sup.net"})
        with self.assertRaises(QiitaDBColumnError):
            Study.create(User('test@foo.bar'), "Fried Chicken Microbiome",
                         [1], self.info)

    def test_create_unknown_db_col(self):
        """ Insert a study with an info key not in the database"""
        self.info["SHOULDNOTBEHERE"] = "BWAHAHAHAHAHA"
        with self.assertRaises(QiitaDBColumnError):
            Study.create(User('test@foo.bar'), "Fried Chicken Microbiome",
                         [1], self.info)

    def test_delete(self):
        title = "Fried chicken microbiome"
        # the study is assigned to investigation 1
        study = Study.create(User('test@foo.bar'), title, [1], self.info,
                             Investigation(1))
        # sharing with other user
        study.share(User("shared@foo.bar"))
        study.delete(study.id)
        self.assertFalse(study.exists(title))

        with self.assertRaises(QiitaDBError):
            Study.delete(1)

        with self.assertRaises(QiitaDBUnknownIDError):
            Study.delete(41)

    def test_retrieve_title(self):
        self.assertEqual(
            self.study.title(),
            'Identification of the Microbiomes for Cannabis Soils')
        with Transaction("test_retrieve_title") as trans:
            self.assertEqual(
                self.study.title(trans=trans),
                'Identification of the Microbiomes for Cannabis Soils')

    def test_set_title(self):
        new = Study.create(User('test@foo.bar'), 'NOT Identification of the '
                           'Microbiomes for Cannabis Soils', [1], self.info)

        new.set_title("Cannabis soils")
        self.assertEqual(new.title(), "Cannabis soils")

        with Transaction("test_set_title") as trans:
            new.set_title("Cannabis soils", trans=trans)
        self.assertEqual(new.title(), "Cannabis soils")

    def test_get_efo(self):
        self.assertEqual(self.study.efo(), [1])

    def test_set_efo(self):
        """Set efo with list efo_id"""
        new = Study.create(User('test@foo.bar'), 'NOT Identification of the '
                           'Microbiomes for Cannabis Soils', [1], self.info)
        new.set_efo([3, 4])
        self.assertEqual(new.efo(), [3, 4])

    def test_set_efo_empty(self):
        """Set efo with list efo_id"""
        new = Study.create(User('test@foo.bar'), 'NOT Identification of the '
                           'Microbiomes for Cannabis Soils', [1], self.info)
        with self.assertRaises(IncompetentQiitaDeveloperError):
            new.set_efo([])

    def test_set_efo_public(self):
        """Set efo on a public study"""
        with self.assertRaises(QiitaDBStatusError):
            self.study.set_efo([6])

    def test_retrieve_info(self):
        for key, val in viewitems(self.existingexp):
            if isinstance(val, QiitaObject):
                self.existingexp[key] = val.id
        self.assertEqual(self.study.info(), self.existingexp)

        with Transaction("test_retrieve_info") as trans:
            self.assertEqual(self.study.info(trans=trans), self.existingexp)

    def test_set_info(self):
        """Set info in a study"""
        newinfo = {
            "timeseries_type_id": 2,
            "metadata_complete": False,
            "number_samples_collected": 28,
            "lab_person_id": StudyPerson(2),
            "vamps_id": 'MBE_111222',
        }
        self.info['first_contact'] = "6/11/2014"
        new = Study.create(User('test@foo.bar'), 'NOT Identification of the '
                           'Microbiomes for Cannabis Soils', [1], self.info)
        self.infoexp.update(newinfo)
        new.set_info(newinfo)
        # add missing table cols
        self.infoexp["funding"] = None
        self.infoexp["spatial_series"] = None
        self.infoexp["most_recent_contact"] = None
        self.infoexp["reprocess"] = False
        self.infoexp["lab_person_id"] = 2
        self.infoexp["first_contact"] = datetime(2014, 6, 11)

        self.assertEqual(new.info(), self.infoexp)

    def test_set_info_public(self):
        """Tests for fail if editing info of a public study"""
        self.study.set_info({"vamps_id": "12321312"})

    def test_set_info_public_error(self):
        """Tests for fail if trying to modify timeseries of a public study"""
        with self.assertRaises(QiitaDBStatusError):
            self.study.set_info({"timeseries_type_id": 2})

    def test_set_info_disallowed_keys(self):
        """Tests for fail if sending non-info keys in info dict"""
        new = Study.create(User('test@foo.bar'), 'NOT Identification of the '
                           'Microbiomes for Cannabis Soils', [1], self.info)
        with self.assertRaises(QiitaDBColumnError):
            new.set_info({"email": "fail@fail.com"})

    def test_info_empty(self):
        new = Study.create(User('test@foo.bar'), 'NOT Identification of the '
                           'Microbiomes for Cannabis Soils', [1], self.info)
        with self.assertRaises(IncompetentQiitaDeveloperError):
            new.set_info({})

    def test_retrieve_status(self):
        self.assertEqual(self.study.status(), "private")

        with Transaction("test_retrieve_status") as trans:
            self.assertEqual(self.study.status(trans=trans), "private")

    def test_retrieve_shared_with(self):
        self.assertEqual(self.study.shared_with(), ['shared@foo.bar'])
        with Transaction("test_retrieve_shared_with") as trans:
            self.assertEqual(
                self.study.shared_with(trans=trans), ['shared@foo.bar'])

    def test_retrieve_pmids(self):
        exp = ['123456', '7891011']
        self.assertEqual(self.study.pmids(), exp)

        with Transaction("test_retrieve_pmids") as trans:
            self.assertEqual(self.study.pmids(trans=trans), exp)

    def test_retrieve_pmids_empty(self):
        new = Study.create(User('test@foo.bar'), 'NOT Identification of the '
                           'Microbiomes for Cannabis Soils', [1], self.info)
        self.assertEqual(new.pmids(), [])

        with Transaction("test_retrieve_pmids_empty") as trans:
            self.assertEqual(new.pmids(trans=trans), [])

    def test_pmids_setter(self):
        exp = ['123456', '7891011']
        self.assertEqual(self.study.pmids(), exp)

        new_values = ['654321', '1101987']
        self.study.set_pmids(new_values)
        self.assertEqual(self.study.pmids(), new_values)

    def test_pmids_setter_typeerror(self):
        with self.assertRaises(TypeError):
            self.study.set_pmids('123456')

    def test_retrieve_investigation(self):
        self.assertEqual(self.study.investigation(), 1)

    def test_retrieve_investigation_empty(self):
        new = Study.create(User('test@foo.bar'), 'NOT Identification of the '
                           'Microbiomes for Cannabis Soils', [1], self.info)
        self.assertEqual(new.investigation(), None)

    def test_retrieve_sample_template(self):
        self.assertEqual(self.study.sample_template, 1)

    def test_retrieve_data_types(self):
        self.assertEqual(self.study.data_types(), ['18S'])

        with Transaction("test_retrieve_data_types") as trans:
            self.assertEqual(self.study.data_types(trans=trans), ['18S'])

    def test_retrieve_data_types_none(self):
        new = Study.create(User('test@foo.bar'), 'NOT Identification of the '
                           'Microbiomes for Cannabis Soils', [1], self.info)
        self.assertEqual(new.data_types(), [])

        with Transaction("test_retrieve_data_types_none") as trans:
            self.assertEqual(new.data_types(trans=trans), [])

    def test_retrieve_raw_data(self):
        self.assertEqual(self.study.raw_data(), [1])

        with Transaction("test_retrieve_raw_data") as trans:
            self.assertEqual(self.study.raw_data(trans=trans), [1])

    def test_retrieve_raw_data_none(self):
        new = Study.create(User('test@foo.bar'), 'NOT Identification of the '
                           'Microbiomes for Cannabis Soils', [1], self.info)
        self.assertEqual(new.raw_data(), [])

        with Transaction("test_retrieve_raw_data_none") as trans:
            self.assertEqual(new.raw_data(trans=trans), [])

    def test_retrieve_prep_templates(self):
        self.assertEqual(self.study.prep_templates(), [1])

        with Transaction("test_retrieve_prep_templates") as trans:
            self.assertEqual(self.study.prep_templates(trans=trans), [1])

    def test_retrieve_prep_templates_none(self):
        new = Study.create(User('test@foo.bar'), 'NOT Identification of the '
                           'Microbiomes for Cannabis Soils', [1], self.info)
        self.assertEqual(new.prep_templates(), [])

        with Transaction("test_retrieve_prep_templates_none") as trans:
            self.assertEqual(new.prep_templates(trans=trans), [])

    def test_retrieve_preprocessed_data(self):
        self.assertEqual(self.study.preprocessed_data(), [1, 2])

        with Transaction("test_retrieve_preprocessed_data") as trans:
            self.assertEqual(self.study.preprocessed_data(trans=trans), [1, 2])

    def test_retrieve_preprocessed_data_none(self):
        new = Study.create(User('test@foo.bar'), 'NOT Identification of the '
                           'Microbiomes for Cannabis Soils', [1], self.info)
        self.assertEqual(new.preprocessed_data(), [])

        with Transaction("test_retrieve_preprocessed_data_none") as trans:
            self.assertEqual(new.preprocessed_data(trans=trans), [])

    def test_retrieve_processed_data(self):
        self.assertEqual(self.study.processed_data(), [1])

        with Transaction("test_retrieve_processed_data") as trans:
            self.assertEqual(self.study.processed_data(trans=trans), [1])

    def test_retrieve_processed_data_none(self):
        new = Study.create(User('test@foo.bar'), 'NOT Identification of the '
                           'Microbiomes for Cannabis Soils', [1], self.info)
        self.assertEqual(new.processed_data(), [])

        with Transaction("test_retrieve_processed_data_none") as trans:
            self.assertEqual(new.processed_data(trans=trans), [])

    def test_add_pmid(self):
        self._change_processed_data_status('sandbox')
        self.study.add_pmid('4544444')
        exp = ['123456', '7891011', '4544444']
        self.assertEqual(self.study.pmids(), exp)

        with Transaction("test_add_pmid") as trans:
            self.study.add_pmid('654321', trans)
        exp = ['123456', '7891011', '4544444', '654321']
        self.assertEqual(self.study.pmids(), exp)

    def test_environmental_packages(self):
        obs = self.study.environmental_packages()
        exp = ['soil', 'plant-associated']
        self.assertEqual(sorted(obs), sorted(exp))

        with Transaction("test_environmental_packages") as trans:
            obs = self.study.environmental_packages(trans=trans)
        self.assertEqual(sorted(obs), sorted(exp))

    def test_environmental_packages_setter(self):
        new = Study.create(User('test@foo.bar'), 'NOT Identification of the '
                           'Microbiomes for Cannabis Soils', [1], self.info)
        obs = new.environmental_packages()
        exp = []
        self.assertEqual(obs, exp)

        new_values = ['air', 'human-oral']
        new.set_environmental_packages(new_values)
        obs = new.environmental_packages()
        self.assertEqual(sorted(obs), sorted(new_values))

    def test_environmental_packages_setter_typeerror(self):
        new = Study.create(User('test@foo.bar'), 'NOT Identification of the '
                           'Microbiomes for Cannabis Soils', [1], self.info)
        with self.assertRaises(TypeError):
            new.set_environmental_packages('air')

    def test_environmental_packages_setter_valueerror(self):
        new = Study.create(User('test@foo.bar'), 'NOT Identification of the '
                           'Microbiomes for Cannabis Soils', [1], self.info)
        with self.assertRaises(ValueError):
            new.set_environmental_packages(['air', 'not a package'])

    def test_environmental_packages_sandboxed(self):
        with self.assertRaises(QiitaDBStatusError):
            self.study.set_environmental_packages(['air'])


if __name__ == "__main__":
    main()
