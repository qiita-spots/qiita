from unittest import TestCase, main
from datetime import datetime

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.qiita_settings import qiita_config
from qiita_core.util import qiita_test_checker
import qiita_db as qdb

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
        self.studyperson = qdb.study.StudyPerson(1)

    def test_create_studyperson(self):
        new = qdb.study.StudyPerson.create(
            'SomeDude', 'somedude@foo.bar', 'affil', '111 fake street',
            '111-121-1313')
        nid = new.id
        self.assertEqual(nid, 4)
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add("SELECT * FROM qiita.study_person "
                                       "WHERE study_person_id = %d" % nid)
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        self.assertEqual(obs, [[nid, 'SomeDude', 'somedude@foo.bar', 'affil',
                         '111 fake street', '111-121-1313']])

        qdb.study.StudyPerson.delete(nid)

    def test_delete(self):
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.study.StudyPerson.delete(1)

        obs = qdb.study.StudyPerson.create(
            'SomeDude', 'somedude@foo.bar', 'affil', '111 fake street',
            '111-121-1313')

        self.assertTrue(
            qdb.study.StudyPerson.exists('SomeDude', 'affil'))
        qdb.study.StudyPerson.delete(obs.id)
        self.assertFalse(
            qdb.study.StudyPerson.exists('SomeDude', 'affil'))

    def test_retrieve_non_existant_people(self):
        with self.assertRaises(qdb.exceptions.QiitaDBLookupError):
            qdb.study.StudyPerson.from_name_and_affiliation('Boaty McBoatFace',
                                                            'UCSD')

        p = qdb.study.StudyPerson.from_name_and_affiliation('LabDude',
                                                            'knight lab')
        self.assertEqual(p.name, 'LabDude')
        self.assertEqual(p.affiliation, 'knight lab')
        self.assertEqual(p.address, '123 lab street')
        self.assertEqual(p.phone, '121-222-3333')
        self.assertEqual(p.email, 'lab_dude@foo.bar')

    def test_iter(self):
        """Make sure that each and every StudyPerson is retrieved"""
        expected = [
            ('LabDude', 'lab_dude@foo.bar', 'knight lab', '123 lab street',
             '121-222-3333'),
            ('empDude', 'emp_dude@foo.bar', 'broad', None, '444-222-3333'),
            ('PIDude', 'PI_dude@foo.bar', 'Wash U', '123 PI street', None)]
        for i, person in enumerate(qdb.study.StudyPerson.iter()):
            self.assertEqual(person.id, i+1)
            self.assertEqual(person.name, expected[i][0])
            self.assertEqual(person.email, expected[i][1])
            self.assertEqual(person.affiliation, expected[i][2])
            self.assertEqual(person.address, expected[i][3])
            self.assertEqual(person.phone, expected[i][4])

    def test_exists(self):
        self.assertTrue(qdb.study.StudyPerson.exists('LabDude', 'knight lab'))
        self.assertFalse(qdb.study.StudyPerson.exists(
            'AnotherDude', 'knight lab'))
        self.assertFalse(qdb.study.StudyPerson.exists(
            'LabDude', 'Another lab'))

    def test_create_studyperson_already_exists(self):
        obs = qdb.study.StudyPerson.create(
            'LabDude', 'lab_dude@foo.bar', 'knight lab')
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
        person = qdb.study.StudyPerson(2)
        self.assertEqual(person.address, None)

    def test_set_address(self):
        self.studyperson.address = '123 nonsense road'
        self.assertEqual(self.studyperson.address, '123 nonsense road')

    def test_retrieve_phone(self):
        self.assertEqual(self.studyperson.phone, '121-222-3333')

    def test_retrieve_phone_null(self):
        person = qdb.study.StudyPerson(3)
        self.assertEqual(person.phone, None)

    def test_set_phone(self):
        self.studyperson.phone = '111111111111111111121'
        self.assertEqual(self.studyperson.phone, '111111111111111111121')


@qiita_test_checker()
class TestStudy(TestCase):
    def setUp(self):
        self.study = qdb.study.Study(1)
        self.portal = qiita_config.portal

        self.info = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "study_alias": "FCM",
            "study_description": "Microbiome of people who eat nothing but "
                                 "fried chicken",
            "study_abstract": "Exploring how a high fat diet changes the "
                              "gut microbiome",
            "principal_investigator_id": qdb.study.StudyPerson(3),
            "lab_person_id": qdb.study.StudyPerson(1),
            'specimen_id_column': None
        }

        self.infoexp = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "study_alias": "FCM",
            "study_description": "Microbiome of people who eat nothing but "
                                 "fried chicken",
            "study_abstract": "Exploring how a high fat diet changes the "
                              "gut microbiome",
            "principal_investigator": qdb.study.StudyPerson(3),
            "lab_person": qdb.study.StudyPerson(1),
            'specimen_id_column': None,
            'public_raw_download': False
        }

        self.existingexp = {
            'mixs_compliant': True,
            'metadata_complete': True,
            'reprocess': False,
            'funding': None,
            'vamps_id': None,
            'first_contact': datetime(2014, 5, 19, 16, 10),
            'principal_investigator': qdb.study.StudyPerson(3),
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
            'study_alias': 'Cannabis Soils',
            'most_recent_contact': datetime(2014, 5, 19, 16, 11),
            'lab_person': qdb.study.StudyPerson(1),
            'specimen_id_column': None}

    def tearDown(self):
        qiita_config.portal = self.portal
        self._change_processed_data_status('private')

    def _change_processed_data_status(self, new_status):
        # Change the status of the studies by changing the status of their
        # artifacts
        id_status = qdb.util.convert_to_id(new_status, 'visibility')
        qdb.sql_connection.perform_as_transaction(
            "UPDATE qiita.artifact SET visibility_id = %s", (id_status,))

    def test_get_info(self):
        # Test get all info for single study
        qiita_config.portal = 'QIITA'
        obs = qdb.study.Study.get_info([1])
        self.assertEqual(len(obs), 1)
        obs = dict(obs[0])
        exp = {
            'mixs_compliant': True, 'metadata_complete': True,
            'reprocess': False, 'timeseries_type': 'None',
            'funding': None, 'vamps_id': None, 'public_raw_download': False,
            'first_contact': datetime(2014, 5, 19, 16, 10),
            'principal_investigator_id': 3, 'timeseries_type_id': 1,
            'publications': [{'f1': '10.100/123456', 'f2': True},
                             {'f1': '123456', 'f2': False},
                             {'f1': '10.100/7891011', 'f2': True},
                             {'f1': '7891011', 'f2': False}],
            'study_alias': 'Cannabis Soils',
            'spatial_series': False, 'notes': '',
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
            'intervention_type': 'None', 'email': 'test@foo.bar',
            'study_id': 1,
            'most_recent_contact': datetime(2014, 5, 19, 16, 11),
            'lab_person_id': 1,
            'study_title': 'Identification of the Microbiomes for Cannabis '
            'Soils',
            'ebi_submission_status': 'submitted',
            'ebi_study_accession': 'EBI123456-BB',
            'autoloaded': False,
            'specimen_id_column': None}
        self.assertDictEqual(obs, exp)

        # Test get specific keys for single study
        exp_keys = ['metadata_complete', 'reprocess', 'timeseries_type',
                    'publications', 'study_title']
        obs = qdb.study.Study.get_info([1], exp_keys)
        self.assertEqual(len(obs), 1)
        exp = [{
            'metadata_complete': True, 'reprocess': False,
            'timeseries_type': 'None',
            'publications': [{'f1': '10.100/123456', 'f2': True},
                             {'f1': '123456', 'f2': False},
                             {'f1': '10.100/7891011', 'f2': True},
                             {'f1': '7891011', 'f2': False}],
            'study_title': 'Identification of the Microbiomes for Cannabis '
            'Soils'}]
        self.assertEqual(obs, exp)

        # Test get specific keys for all studies
        info = {
            'timeseries_type_id': 1,
            'lab_person_id': None,
            'principal_investigator_id': 3,
            'metadata_complete': False,
            'mixs_compliant': True,
            'study_description': 'desc',
            'study_alias': 'alias',
            'study_abstract': 'abstract'}
        user = qdb.user.User('test@foo.bar')

        s = qdb.study.Study.create(user, 'test_study_1', info=info)
        obs = qdb.study.Study.get_info(info_cols=exp_keys)
        exp = [
            {'metadata_complete': True, 'reprocess': False,
             'timeseries_type': 'None', 'publications': [
                {'f1': '10.100/123456', 'f2': True},
                {'f1': '123456', 'f2': False},
                {'f1': '10.100/7891011', 'f2': True},
                {'f1': '7891011', 'f2': False}],
             'study_title': ('Identification of the Microbiomes for '
                             'Cannabis Soils')},
            {'metadata_complete': False, 'reprocess': False,
             'timeseries_type': 'None', 'publications': None,
             'study_title': 'test_study_1'}]
        self.assertEqual(obs, exp)
        qdb.study.Study.delete(s.id)

        # test portal restriction working
        qiita_config.portal = 'EMP'
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.study.Study.get_info([1])

    def test_has_access_public(self):
        self._change_processed_data_status('public')

        qiita_config.portal = 'QIITA'
        self.assertTrue(
            self.study.has_access(qdb.user.User("demo@microbio.me")))
        qiita_config.portal = 'EMP'
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.study.Study(1).has_access(qdb.user.User("demo@microbio.me"))

    def test_has_access_no_public(self):
        self._change_processed_data_status('public')
        self.assertFalse(
            self.study.has_access(qdb.user.User("demo@microbio.me"), True))

    def test_can_edit(self):
        self.assertTrue(self.study.can_edit(qdb.user.User('test@foo.bar')))
        self.assertTrue(self.study.can_edit(qdb.user.User('shared@foo.bar')))
        self.assertTrue(self.study.can_edit(qdb.user.User('admin@foo.bar')))
        self.assertFalse(
            self.study.can_edit(qdb.user.User('demo@microbio.me')))

    def test_owner(self):
        self.assertEqual(self.study.owner, qdb.user.User("test@foo.bar"))

    def test_autoloaded(self):
        self.assertFalse(self.study.autoloaded)
        self.study.autoloaded = True
        self.assertTrue(self.study.autoloaded)
        self.study.autoloaded = False
        self.assertFalse(self.study.autoloaded)

    def test_public_raw_download(self):
        self.assertFalse(self.study.public_raw_download)
        self.study.public_raw_download = True
        self.assertTrue(self.study.public_raw_download)
        self.study.public_raw_download = False
        self.assertFalse(self.study.public_raw_download)

    def test_share(self):
        # Clear all sharing associations
        self._change_processed_data_status('sandbox')
        qdb.sql_connection.perform_as_transaction(
            "delete from qiita.study_users")
        self.assertEqual(self.study.shared_with, [])

        # Try to share with the owner, which should not work
        self.study.share(qdb.user.User("test@foo.bar"))
        self.assertEqual(self.study.shared_with, [])

        # Then share the study with shared@foo.bar
        self.study.share(qdb.user.User("shared@foo.bar"))
        self.assertEqual(self.study.shared_with,
                         [qdb.user.User("shared@foo.bar")])

    def test_unshare(self):
        self._change_processed_data_status('sandbox')
        self.study.unshare(qdb.user.User("shared@foo.bar"))
        self.assertEqual(self.study.shared_with, [])

    def test_has_access_shared(self):
        self._change_processed_data_status('sandbox')
        self.assertTrue(self.study.has_access(qdb.user.User("shared@foo.bar")))

    def test_has_access_private(self):
        self._change_processed_data_status('sandbox')
        self.assertTrue(self.study.has_access(qdb.user.User("test@foo.bar")))

    def test_has_access_admin(self):
        self._change_processed_data_status('sandbox')
        self.assertTrue(self.study.has_access(qdb.user.User("admin@foo.bar")))

    def test_has_access_no_access(self):
        self._change_processed_data_status('sandbox')
        self.assertFalse(
            self.study.has_access(qdb.user.User("demo@microbio.me")))

    def test_get_by_status(self):
        obs = qdb.study.Study.get_by_status('sandbox')
        self.assertEqual(obs, set())

        s = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils',
            self.info)
        obs = qdb.study.Study.get_by_status('private')
        self.assertEqual(obs, {qdb.study.Study(1)})

        obs = qdb.study.Study.get_by_status('sandbox')
        self.assertEqual(obs, {s})

        obs = qdb.study.Study.get_by_status('public')
        self.assertEqual(obs, set())

        obs = qdb.study.Study.get_by_status('awaiting_approval')
        self.assertEqual(obs, set())

        qdb.study.Study.delete(s.id)

    def test_exists(self):
        self.assertTrue(qdb.study.Study.exists(
            'Identification of the Microbiomes for Cannabis Soils'))
        self.assertFalse(qdb.study.Study.exists('Not Cannabis Soils'))

    def test_create_duplicate(self):
        to_test = [
            'Identification of the Microbiomes for Cannabis Soils',
            'Identification  of  the Microbiomes for Cannabis Soils',
            ' Identification of the Microbiomes for Cannabis Soils',
            'Identification of the Microbiomes for Cannabis Soils ',
            '  Identification of the Microbiomes for Cannabis Soils  '
        ]
        for tt in to_test:
            with self.assertRaises(qdb.exceptions.QiitaDBDuplicateError):
                qdb.study.Study.create(
                    qdb.user.User('test@foo.bar'), tt, self.info)

    def test_create_study_min_data(self):
        """Insert a study into the database"""
        before = datetime.now()
        obs = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "Fried chicken microbiome 1",
            self.info)
        after = datetime.now()
        self.assertEqual(obs.status, 'sandbox')
        self.assertEqual(obs.title, "Fried chicken microbiome 1")
        obs_info = obs.info
        insertion_timestamp = obs_info.pop('first_contact')
        exp = {'mixs_compliant': True, 'metadata_complete': True,
               'reprocess': False, 'public_raw_download': False,
               'funding': None, 'vamps_id': None,
               'principal_investigator': qdb.study.StudyPerson(3),
               'timeseries_type_id': 1,
               'study_abstract': 'Exploring how a high fat diet changes the '
                                 'gut microbiome',
               'spatial_series': None,
               'study_description': 'Microbiome of people who eat nothing but'
                                    ' fried chicken',
               'study_alias': 'FCM',
               'most_recent_contact': None,
               'lab_person': qdb.study.StudyPerson(1),
               'notes': '',
               'specimen_id_column': None}
        self.assertEqual(obs_info, exp)
        # Check the timestamp separately, since it is set by the database
        # to the microsecond, and we can't predict it a priori
        self.assertTrue(before < insertion_timestamp < after)
        self.assertEqual(obs.shared_with, [])
        self.assertEqual(obs.publications, [])
        self.assertEqual(obs.investigation, None)
        self.assertEqual(obs.sample_template, None)
        self.assertEqual(obs.data_types, [])
        self.assertEqual(obs.owner, qdb.user.User('test@foo.bar'))
        self.assertEqual(obs.environmental_packages, [])
        self.assertEqual(obs._portals, ['QIITA'])
        self.assertEqual(obs.ebi_study_accession, None)
        self.assertEqual(obs.ebi_submission_status, "not submitted")
        qdb.study.Study.delete(obs.id)

    def test_create_nonqiita_portal(self):
        qiita_config.portal = "EMP"
        s = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "NEW!", self.info,
            qdb.investigation.Investigation(1))

        # make sure portal is associated
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add(
                "SELECT * from qiita.study_portal WHERE study_id = %s", [s.id])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        self.assertEqual(obs, [[s.id, 2], [s.id, 1]])
        qdb.study.Study.delete(s.id)

    def test_create_study_with_investigation(self):
        """Insert a study into the database with an investigation"""
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "Fried chicken microbiome 2",
            self.info, qdb.investigation.Investigation(1))
        # check the investigation was assigned
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add(
                "SELECT * from qiita.investigation_study WHERE study_id = %s",
                [new.id])
            obs = qdb.sql_connection.TRN.execute_fetchindex()
        self.assertEqual(obs, [[1, new.id]])

        # testing Study.iter()
        self.assertCountEqual(list(qdb.study.Study.iter()),
                              [qdb.study.Study(1), new])

        qdb.study.Study.delete(new.id)

    def test_create_study_all_data(self):
        """Insert a study into the database with every info field"""
        self.info.update({
            'vamps_id': 'MBE_1111111',
            'funding': 'FundAgency',
            'spatial_series': True,
            'metadata_complete': False,
            'reprocess': True,
            'first_contact': "10/24/2014 12:47PM",
            'study_id': 3827,
            'notes': 'an analysis was performed \n here and \n here'
            })
        obs = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "Fried chicken microbiome 3",
            self.info)
        self.assertEqual(obs.id, 3827)
        self.assertEqual(obs.status, 'sandbox')
        self.assertEqual(obs.title, "Fried chicken microbiome 3")
        exp = {'mixs_compliant': True, 'metadata_complete': False,
               'reprocess': True, 'public_raw_download': False,
               'funding': 'FundAgency', 'vamps_id': 'MBE_1111111',
               'first_contact': datetime(2014, 10, 24, 12, 47),
               'principal_investigator': qdb.study.StudyPerson(3),
               'timeseries_type_id': 1,
               'study_abstract': 'Exploring how a high fat diet changes the '
                                 'gut microbiome',
               'spatial_series': True,
               'study_description': 'Microbiome of people who eat nothing '
                                    'but fried chicken',
               'study_alias': 'FCM',
               'most_recent_contact': None,
               'lab_person': qdb.study.StudyPerson(1),
               'notes': 'an analysis was performed \n here and \n here',
               'specimen_id_column': None}
        self.assertEqual(obs.info, exp)
        self.assertEqual(obs.shared_with, [])
        self.assertEqual(obs.publications, [])
        self.assertEqual(obs.investigation, None)
        self.assertEqual(obs.sample_template, None)
        self.assertEqual(obs.data_types, [])
        self.assertEqual(obs.owner, qdb.user.User('test@foo.bar'))
        self.assertEqual(obs.environmental_packages, [])
        self.assertEqual(obs._portals, ['QIITA'])
        self.assertEqual(obs.ebi_study_accession, None)
        self.assertEqual(obs.ebi_submission_status, "not submitted")

        # testing Study.iter()
        self.assertCountEqual(list(qdb.study.Study.iter()),
                              [qdb.study.Study(1), obs])

        qdb.study.Study.delete(obs.id)

    def test_create_missing_required(self):
        """ Insert a study that is missing a required info key"""
        self.info.pop("study_alias")
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            qdb.study.Study.create(
                qdb.user.User('test@foo.bar'), "Fried Chicken Microbiome 4",
                self.info)

    def test_create_study_with_not_allowed_key(self):
        """Insert a study with key from _non_info present"""
        self.info.update({"email": "wooo@sup.net"})
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            qdb.study.Study.create(
                qdb.user.User('test@foo.bar'), "Fried Chicken Microbiome 6",
                self.info)

    def test_create_unknown_db_col(self):
        """ Insert a study with an info key not in the database"""
        self.info["SHOULDNOTBEHERE"] = "BWAHAHAHAHAHA"
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            qdb.study.Study.create(
                qdb.user.User('test@foo.bar'), "Fried Chicken Microbiome 7",
                self.info)

    def test_delete(self):
        title = "Fried chicken microbiome 8"
        # the study is assigned to investigation 1
        study = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), title, self.info,
            qdb.investigation.Investigation(1))
        # sharing with other user
        study.share(qdb.user.User("shared@foo.bar"))
        study.delete(study.id)
        self.assertFalse(study.exists(title))

        with self.assertRaises(qdb.exceptions.QiitaDBError):
            qdb.study.Study.delete(1)

        with self.assertRaises(qdb.exceptions.QiitaDBUnknownIDError):
            qdb.study.Study.delete(41)

    def test_retrieve_title(self):
        self.assertEqual(self.study.title, 'Identification of the Microbiomes'
                         ' for Cannabis Soils')

    def test_set_title(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 1',
            self.info)
        new.title = "Cannabis soils"
        self.assertEqual(new.title, "Cannabis soils")
        qdb.study.Study.delete(new.id)

    def test_portals(self):
        self.assertEqual(self.study._portals, ['QIITA'])

    def test_ebi_study_accession(self):
        self.assertEqual(self.study.ebi_study_accession, 'EBI123456-BB')
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 4',
            self.info)
        self.assertEqual(new.ebi_study_accession, None)
        qdb.study.Study.delete(new.id)

    def test_ebi_study_accession_setter(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), 'Test', self.info)
        self.assertEqual(new.ebi_study_accession, None)
        new.ebi_study_accession = 'EBI654321-BB'
        self.assertEqual(new.ebi_study_accession, 'EBI654321-BB')

        # Raises an error if the study already has an EBI study accession
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            self.study.ebi_study_accession = 'EBI654321-BB'

        qdb.study.Study.delete(new.id)

    def test_ebi_submission_status(self):
        self.assertEqual(self.study.ebi_submission_status, 'submitted')

        # let's test that even with a failed job nothing changes
        # add a failed job for an artifact (2) that can be submitted
        user = qdb.user.User('test@foo.bar')
        qp = qdb.software.Software.from_name_and_version('Qiita', 'alpha')
        cmd = qp.get_command('submit_to_EBI')
        params = qdb.software.Parameters.load(cmd, values_dict={
            'artifact': 2, 'submission_type': 'ADD'})
        job = qdb.processing_job.ProcessingJob.create(user, params, True)
        job._set_error('Killed by Admin')
        # and just to be careful add a failed job for an artifact (1) that
        # cannot be submitted
        qp = qdb.software.Software.from_name_and_version('Qiita', 'alpha')
        cmd = qp.get_command('submit_to_EBI')
        params = qdb.software.Parameters.load(cmd, values_dict={
            'artifact': 1, 'submission_type': 'ADD'})
        job = qdb.processing_job.ProcessingJob.create(user, params, True)
        job._set_error('Killed by Admin')
        # should still return submited
        self.assertEqual(self.study.ebi_submission_status, 'submitted')

        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 5',
            self.info)
        self.assertEqual(new.ebi_submission_status, 'not submitted')
        qdb.study.Study.delete(new.id)

    def test_set_info(self):
        """Set info in a study"""
        newinfo = {
            "timeseries_type_id": 2,
            "metadata_complete": False,
            "lab_person_id": qdb.study.StudyPerson(2),
            "vamps_id": 'MBE_111222',
            'notes': 'These are my notes!!! \n ... and more notes ...'
        }
        self.info['first_contact'] = "6/11/2014"
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 6',
            self.info)
        self.infoexp.update(newinfo)
        new.info = newinfo
        # add missing table cols
        self.infoexp["funding"] = None
        self.infoexp["spatial_series"] = None
        self.infoexp["most_recent_contact"] = None
        self.infoexp["reprocess"] = False
        self.infoexp["first_contact"] = datetime(2014, 6, 11)
        self.infoexp["lab_person"] = qdb.study.StudyPerson(2)
        del self.infoexp["lab_person_id"]

        self.assertEqual(new.info, self.infoexp)
        qdb.study.Study.delete(new.id)

    def test_set_info_public(self):
        """Tests for fail if editing info of a public study"""
        self.study.info = {"vamps_id": "12321312"}

    def test_set_info_public_error(self):
        """Tests for fail if trying to modify timeseries of a public study"""
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.study.info = {"timeseries_type_id": 2}

    def test_set_info_disallowed_keys(self):
        """Tests for fail if sending non-info keys in info dict"""
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 7',
            self.info)
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            new.info = {"email": "fail@fail.com"}
        qdb.study.Study.delete(new.id)

    def test_info_empty(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 8',
            self.info)
        with self.assertRaises(IncompetentQiitaDeveloperError):
            new.info = {}
        qdb.study.Study.delete(new.id)

    def test_retrieve_status(self):
        self.assertEqual(self.study.status, "private")

    def test_retrieve_shared_with(self):
        self.assertEqual(self.study.shared_with,
                         [qdb.user.User('shared@foo.bar')])

    def test_retrieve_publications_empty(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 9',
            self.info)
        self.assertEqual(new.publications, [])

    def test_publication_setter(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), 'New study', self.info)
        self.assertEqual(new.publications, [])

        new_values = [['10.100/654321', True],
                      ['10.100/1101987', True],
                      ['1101987', False]]
        new.publications = new_values
        self.assertEqual(new.publications, new_values)
        qdb.study.Study.delete(new.id)

    def test_publications_setter_typeerror(self):
        with self.assertRaises(TypeError):
            self.study.publications = '123456'

    def test_retrieve_investigation(self):
        self.assertEqual(self.study.investigation,
                         qdb.investigation.Investigation(1))

    def test_retrieve_investigation_empty(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 10',
            self.info)
        self.assertEqual(new.investigation, None)
        qdb.study.Study.delete(new.id)

    def test_retrieve_sample_template(self):
        self.assertEqual(
            self.study.sample_template,
            qdb.metadata_template.sample_template.SampleTemplate(1))

    def test_retrieve_data_types(self):
        self.assertEqual(self.study.data_types, ['18S'])

    def test_retrieve_data_types_none(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 11',
            self.info)
        self.assertEqual(new.data_types, [])
        qdb.study.Study.delete(new.id)

    def test_retrieve_artifacts(self):
        exp = [qdb.artifact.Artifact(1),
               qdb.artifact.Artifact(2),
               qdb.artifact.Artifact(3),
               qdb.artifact.Artifact(4),
               qdb.artifact.Artifact(5),
               qdb.artifact.Artifact(6),
               qdb.artifact.Artifact(7)]
        self.assertEqual(self.study.artifacts(), exp)
        self.assertEqual(self.study.artifacts(dtype="16S"), exp[-2:])
        self.assertEqual(self.study.artifacts(dtype="18S"), exp[:-2])

        self.assertEqual(self.study.artifacts(artifact_type="BIOM"),
                         [qdb.artifact.Artifact(4),
                          qdb.artifact.Artifact(5),
                          qdb.artifact.Artifact(6),
                          qdb.artifact.Artifact(7)])

        self.assertEqual(self.study.artifacts(dtype="18S",
                                              artifact_type="BIOM"),
                         [qdb.artifact.Artifact(4),
                          qdb.artifact.Artifact(5)])

    def test_retrieve_artifacts_none(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 12',
            self.info)
        self.assertEqual(new.artifacts(), [])
        qdb.study.Study.delete(new.id)

    def test_retrieve_prep_templates(self):
        self.assertEqual(
            self.study.prep_templates(),
            [qdb.metadata_template.prep_template.PrepTemplate(1),
             qdb.metadata_template.prep_template.PrepTemplate(2)])

    def test_retrieve_prep_templates_none(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 13',
            self.info)
        self.assertEqual(new.prep_templates(), [])
        qdb.study.Study.delete(new.id)

    def test_analyses(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 13',
            self.info)

        self.assertEqual(qdb.study.Study(1).analyses(), [
            qdb.analysis.Analysis(1), qdb.analysis.Analysis(2),
            qdb.analysis.Analysis(3)])

        self.assertEqual(qdb.study.Study(2).analyses(), [])

        qdb.study.Study.delete(new.id)

    def test_environmental_packages(self):
        obs = self.study.environmental_packages
        exp = ['soil', 'plant-associated']
        self.assertEqual(sorted(obs), sorted(exp))

    def test_environmental_packages_setter(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 14',
            self.info)
        obs = new.environmental_packages
        exp = []
        self.assertEqual(obs, exp)

        new_values = ['air', 'human-oral']
        new.environmental_packages = new_values
        obs = new.environmental_packages
        self.assertEqual(sorted(obs), sorted(new_values))
        qdb.study.Study.delete(new.id)

    def test_environmental_packages_setter_typeerror(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 15',
            self.info)
        with self.assertRaises(TypeError):
            new.environmental_packages = 'air'
        qdb.study.Study.delete(new.id)

    def test_environmental_packages_setter_valueerror(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 16',
            self.info)
        with self.assertRaises(ValueError):
            new.environmental_packages = ['air', 'not a package']
        qdb.study.Study.delete(new.id)

    def test_environmental_packages_sandboxed(self):
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.study.environmental_packages = ['air']

    def test_study_tags(self):
        # testing empty tags
        obs = qdb.study.Study.get_tags()
        self.assertEqual(obs, {'admin': [], 'user': []})

        # inserting new tags
        user = qdb.user.User('test@foo.bar')
        tags = ['this is my tag', 'I want GOLD!!', 'this is my tag']
        qdb.study.Study.insert_tags(user, tags)
        # now as admin
        admin = qdb.user.User('admin@foo.bar')
        admin_tags = ['actual GOLD!', 'this is my tag']
        qdb.study.Study.insert_tags(admin, admin_tags)

        # testing that insertion went fine
        obs = qdb.study.Study.get_tags()
        exp = {'user': ['I want GOLD!!', 'this is my tag'],
               'admin': ['actual GOLD!']}
        self.assertEqual(obs, exp)

        # assigning the tags to study as user
        study = qdb.study.Study(1)
        tags = ['this is my tag', 'actual GOLD!']
        message = study.update_tags(user, tags)
        self.assertCountEqual(study.tags, tags[:1])
        self.assertEqual(message, 'Only admins can assign: actual GOLD!')
        # now like admin
        message = study.update_tags(admin, tags)
        self.assertCountEqual(study.tags, tags)
        self.assertEqual(message, '')

        # cleaning tags
        message = study.update_tags(user, [])
        self.assertEqual(study.tags, ['actual GOLD!'])
        self.assertEqual(message, 'You cannot remove: actual GOLD!')
        message = study.update_tags(admin, [])
        self.assertEqual(study.tags, [])
        self.assertEqual(message, '')

    def test_specimen_id_column_get_set(self):
        self.assertEqual(self.study.specimen_id_column, None)
        self.study.specimen_id_column = 'anonymized_name'
        self.assertEqual(self.study.specimen_id_column, 'anonymized_name')
        self.study.specimen_id_column = None
        self.assertEqual(self.study.specimen_id_column, None)

    def test_specimen_id_column_not_unique(self):
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            self.study.specimen_id_column = 'dna_extracted'

    def test_specimen_id_column_doesnt_exist(self):
        with self.assertRaises(qdb.exceptions.QiitaDBLookupError):
            self.study.specimen_id_column = 'foo'

    def test_specimen_id_column_no_sample_information(self):
        empty = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "Fried duck microbiome",
            self.info)
        with self.assertRaises(qdb.exceptions.QiitaDBLookupError):
            empty.specimen_id_column = 'foo'

        # cleaning up the created study
        qdb.study.Study.delete(empty._id)


if __name__ == "__main__":
    main()
