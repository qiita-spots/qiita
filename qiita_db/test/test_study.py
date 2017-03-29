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
        self.assertEqual(new.id, 4)
        obs = self.conn_handler.execute_fetchall(
            "SELECT * FROM qiita.study_person WHERE study_person_id = 4")
        self.assertEqual(obs, [[4, 'SomeDude', 'somedude@foo.bar', 'affil',
                         '111 fake street', '111-121-1313']])

        qdb.study.StudyPerson.delete(new.id)

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
        with self.assertRaises(qdb.esceptions.QiitaDBLookupError):
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
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "study_alias": "FCM",
            "study_description": "Microbiome of people who eat nothing but "
                                 "fried chicken",
            "study_abstract": "Exploring how a high fat diet changes the "
                              "gut microbiome",
            "emp_person_id": qdb.study.StudyPerson(2),
            "principal_investigator_id": qdb.study.StudyPerson(3),
            "lab_person_id": qdb.study.StudyPerson(1)
        }

        self.infoexp = {
            "timeseries_type_id": 1,
            "metadata_complete": True,
            "mixs_compliant": True,
            "number_samples_collected": 25,
            "number_samples_promised": 28,
            "study_alias": "FCM",
            "study_description": "Microbiome of people who eat nothing but "
                                 "fried chicken",
            "study_abstract": "Exploring how a high fat diet changes the "
                              "gut microbiome",
            "emp_person_id": 2,
            "principal_investigator": qdb.study.StudyPerson(3),
            "lab_person": qdb.study.StudyPerson(1)
        }

        self.existingexp = {
            'mixs_compliant': True,
            'metadata_complete': True,
            'reprocess': False,
            'number_samples_promised': 27,
            'emp_person_id': 2,
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
            'number_samples_collected': 27}

    def tearDown(self):
        qiita_config.portal = self.portal
        self._change_processed_data_status('private')

    def _change_processed_data_status(self, new_status):
        # Change the status of the studies by changing the status of their
        # artifacts
        id_status = qdb.util.convert_to_id(new_status, 'visibility')
        self.conn_handler.execute(
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
            'number_samples_promised': 27, 'emp_person_id': 2,
            'funding': None, 'vamps_id': None,
            'first_contact': datetime(2014, 5, 19, 16, 10),
            'principal_investigator_id': 3, 'timeseries_type_id': 1,
            'publications': [{'f1': '10.100/123456', 'f2': True},
                             {'f1': '123456', 'f2': False},
                             {'f1': '10.100/7891011', 'f2': True},
                             {'f1': '7891011', 'f2': False}],
            'study_alias': 'Cannabis Soils',
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
            'intervention_type': 'None', 'email': 'test@foo.bar',
            'study_id': 1,
            'most_recent_contact': datetime(2014, 5, 19, 16, 11),
            'lab_person_id': 1,
            'study_title': 'Identification of the Microbiomes for Cannabis '
            'Soils', 'number_samples_collected': 27,
            'ebi_submission_status': 'submitted',
            'ebi_study_accession': 'EBI123456-BB'}
        self.assertEqual(obs, exp)

        # Test get specific keys for single study
        exp_keys = ['metadata_complete', 'reprocess', 'timeseries_type',
                    'publications', 'study_title']
        obs = qdb.study.Study.get_info([1], exp_keys)
        self.assertEqual(len(obs), 1)
        obs = dict(obs[0])
        exp = {
            'metadata_complete': True, 'reprocess': False,
            'timeseries_type': 'None',
            'publications': [{'f1': '10.100/123456', 'f2': True},
                             {'f1': '123456', 'f2': False},
                             {'f1': '10.100/7891011', 'f2': True},
                             {'f1': '7891011', 'f2': False}],
            'study_title': 'Identification of the Microbiomes for Cannabis '
            'Soils'}
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

        s = qdb.study.Study.create(user, 'test_study_1', efo=[1], info=info)
        obs = qdb.study.Study.get_info(info_cols=exp_keys)
        exp = [[True, [{'f1': '7891011', 'f2': False},
                       {'f1': '10.100/7891011', 'f2': True},
                       {'f1': '123456', 'f2': False},
                       {'f1': '10.100/123456', 'f2': True}], False,
                'Identification of the Microbiomes for Cannabis Soils',
                'None'],
               [False, None, False, 'test_study_1', 'None']]
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

    def test_share(self):
        # Clear all sharing associations
        self._change_processed_data_status('sandbox')
        self.conn_handler.execute("delete from qiita.study_users")
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
            'NOT Identification of the Microbiomes for Cannabis Soils', [1],
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
        with self.assertRaises(qdb.exceptions.QiitaDBDuplicateError):
            qdb.study.Study.create(
                qdb.user.User('test@foo.bar'),
                'Identification of the Microbiomes for Cannabis Soils',
                [1], self.info)

    def test_create_study_min_data(self):
        """Insert a study into the database"""
        before = datetime.now()
        obs = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "Fried chicken microbiome 1", [1],
            self.info)
        after = datetime.now()
        self.assertEqual(obs.status, 'sandbox')
        self.assertEqual(obs.title, "Fried chicken microbiome 1")
        obs_info = obs.info
        insertion_timestamp = obs_info.pop('first_contact')
        exp = {'mixs_compliant': True, 'metadata_complete': True,
               'reprocess': False,
               'number_samples_promised': 28, 'emp_person_id': 2,
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
               'number_samples_collected': 25}
        self.assertEqual(obs_info, exp)
        # Check the timestamp separately, since it is set by the database
        # to the microsecond, and we can't predict it a priori
        self.assertTrue(before < insertion_timestamp < after)
        self.assertEqual(obs.efo, [1])
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
            qdb.user.User('test@foo.bar'), "NEW!", [1], self.info,
            qdb.investigation.Investigation(1))

        # make sure portal is associated
        obs = self.conn_handler.execute_fetchall(
            "SELECT * from qiita.study_portal WHERE study_id = %s", [s.id])
        self.assertEqual(obs, [[s.id, 2], [s.id, 1]])
        qdb.study.Study.delete(s.id)

    def test_create_study_with_investigation(self):
        """Insert a study into the database with an investigation"""
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "Fried chicken microbiome 2", [1],
            self.info, qdb.investigation.Investigation(1))
        # check the investigation was assigned
        obs = self.conn_handler.execute_fetchall(
            "SELECT * from qiita.investigation_study WHERE study_id = %s",
            [new.id])
        self.assertEqual(obs, [[1, new.id]])
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
            'study_id': 3827
            })
        obs = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), "Fried chicken microbiome 3", [1],
            self.info)
        self.assertEqual(obs.id, 3827)
        self.assertEqual(obs.status, 'sandbox')
        self.assertEqual(obs.title, "Fried chicken microbiome 3")
        exp = {'mixs_compliant': True, 'metadata_complete': False,
               'reprocess': True,
               'number_samples_promised': 28, 'emp_person_id': 2,
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
               'number_samples_collected': 25}
        self.assertEqual(obs.info, exp)
        self.assertEqual(obs.efo, [1])
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

    def test_create_missing_required(self):
        """ Insert a study that is missing a required info key"""
        self.info.pop("study_alias")
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            qdb.study.Study.create(
                qdb.user.User('test@foo.bar'), "Fried Chicken Microbiome 4",
                [1], self.info)

    def test_create_empty_efo(self):
        """ Insert a study that is missing a required info key"""
        with self.assertRaises(IncompetentQiitaDeveloperError):
            qdb.study.Study.create(
                qdb.user.User('test@foo.bar'), "Fried Chicken Microbiome 5",
                [], self.info)

    def test_create_study_with_not_allowed_key(self):
        """Insert a study with key from _non_info present"""
        self.info.update({"email": "wooo@sup.net"})
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            qdb.study.Study.create(
                qdb.user.User('test@foo.bar'), "Fried Chicken Microbiome 6",
                [1], self.info)

    def test_create_unknown_db_col(self):
        """ Insert a study with an info key not in the database"""
        self.info["SHOULDNOTBEHERE"] = "BWAHAHAHAHAHA"
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            qdb.study.Study.create(
                qdb.user.User('test@foo.bar'), "Fried Chicken Microbiome 7",
                [1], self.info)

    def test_delete(self):
        title = "Fried chicken microbiome 8"
        # the study is assigned to investigation 1
        study = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), title, [1], self.info,
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
            'NOT Identification of the Microbiomes for Cannabis Soils 1', [1],
            self.info)
        new.title = "Cannabis soils"
        self.assertEqual(new.title, "Cannabis soils")
        qdb.study.Study.delete(new.id)

    def test_get_efo(self):
        self.assertEqual(self.study.efo, [1])

    def test_set_efo(self):
        """Set efo with list efo_id"""
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 2', [1],
            self.info)
        new.efo = [3, 4]
        self.assertEqual(new.efo, [3, 4])
        qdb.study.Study.delete(new.id)

    def test_set_efo_empty(self):
        """Set efo with list efo_id"""
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 3', [1],
            self.info)
        with self.assertRaises(IncompetentQiitaDeveloperError):
            new.efo = []
        qdb.study.Study.delete(new.id)

    def test_set_efo_public(self):
        """Set efo on a public study"""
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.study.efo = [6]

    def test_portals(self):
        self.assertEqual(self.study._portals, ['QIITA'])

    def test_ebi_study_accession(self):
        self.assertEqual(self.study.ebi_study_accession, 'EBI123456-BB')
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 4', [1],
            self.info)
        self.assertEqual(new.ebi_study_accession, None)
        qdb.study.Study.delete(new.id)

    def test_ebi_study_accession_setter(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), 'Test', [1], self.info)
        self.assertEqual(new.ebi_study_accession, None)
        new.ebi_study_accession = 'EBI654321-BB'
        self.assertEqual(new.ebi_study_accession, 'EBI654321-BB')

        # Raises an error if the study already has an EBI study accession
        with self.assertRaises(qdb.exceptions.QiitaDBError):
            self.study.ebi_study_accession = 'EBI654321-BB'

        qdb.study.Study.delete(new.id)

    def test_ebi_submission_status(self):
        self.assertEqual(self.study.ebi_submission_status, 'submitted')
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 5', [1],
            self.info)
        self.assertEqual(new.ebi_submission_status, 'not submitted')
        qdb.study.Study.delete(new.id)

    def test_ebi_submission_status_setter(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), 'Test 1', [1], self.info)
        self.assertEqual(new.ebi_submission_status, "not submitted")
        new.ebi_submission_status = 'submitting'
        self.assertEqual(new.ebi_submission_status, 'submitting')
        new.ebi_submission_status = 'failed: something horrible happened'
        self.assertEqual(new.ebi_submission_status,
                         'failed: something horrible happened')
        new.ebi_submission_status = 'submitted'
        self.assertEqual(new.ebi_submission_status, 'submitted')

        with self.assertRaises(ValueError):
            new.ebi_submission_status = "unknown"

        qdb.study.Study.delete(new.id)

    def test_set_info(self):
        """Set info in a study"""
        newinfo = {
            "timeseries_type_id": 2,
            "metadata_complete": False,
            "number_samples_collected": 28,
            "lab_person_id": qdb.study.StudyPerson(2),
            "vamps_id": 'MBE_111222',
        }
        self.info['first_contact'] = "6/11/2014"
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 6', [1],
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
            'NOT Identification of the Microbiomes for Cannabis Soils 7', [1],
            self.info)
        with self.assertRaises(qdb.exceptions.QiitaDBColumnError):
            new.info = {"email": "fail@fail.com"}
        qdb.study.Study.delete(new.id)

    def test_info_empty(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 8', [1],
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
            'NOT Identification of the Microbiomes for Cannabis Soils 9', [1],
            self.info)
        self.assertEqual(new.publications, [])

    def test_publication_setter(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'), 'New study', [1], self.info)
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
            'NOT Identification of the Microbiomes for Cannabis Soils 10', [1],
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
            'NOT Identification of the Microbiomes for Cannabis Soils 11', [1],
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
            'NOT Identification of the Microbiomes for Cannabis Soils 12', [1],
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
            'NOT Identification of the Microbiomes for Cannabis Soils 13', [1],
            self.info)
        self.assertEqual(new.prep_templates(), [])
        qdb.study.Study.delete(new.id)

    def test_environmental_packages(self):
        obs = self.study.environmental_packages
        exp = ['soil', 'plant-associated']
        self.assertEqual(sorted(obs), sorted(exp))

    def test_environmental_packages_setter(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 14', [1],
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
            'NOT Identification of the Microbiomes for Cannabis Soils 15', [1],
            self.info)
        with self.assertRaises(TypeError):
            new.environmental_packages = 'air'
        qdb.study.Study.delete(new.id)

    def test_environmental_packages_setter_valueerror(self):
        new = qdb.study.Study.create(
            qdb.user.User('test@foo.bar'),
            'NOT Identification of the Microbiomes for Cannabis Soils 16', [1],
            self.info)
        with self.assertRaises(ValueError):
            new.environmental_packages = ['air', 'not a package']
        qdb.study.Study.delete(new.id)

    def test_environmental_packages_sandboxed(self):
        with self.assertRaises(qdb.exceptions.QiitaDBStatusError):
            self.study.environmental_packages = ['air']

    def test_study_tags(self):
        # inserting new tags
        user = qdb.user.User('test@foo.bar')
        tags = ['this is my tag', 'I want GOLD!!']
        qdb.study.Study.insert_tags(user, tags)

        # testing that insertion went fine
        obs = qdb.study.Study.get_tags()
        exp = [[i + 1, tag] for i, tag in enumerate(tags)]
        self.assertEqual(obs, exp)

        # assigning the tags to study
        study = qdb.study.Study(1)
        self.assertEqual(study.tags, [])
        study.tags = [tig for tig, tag in obs]
        # and checking that everything went fine
        self.assertEqual(obs, study.tags)

        # making sure that everything is overwritten
        obs.pop()
        study.tags = [tig for tig, tag in obs]
        self.assertEqual(obs, study.tags)

        # cleaning tags
        study.tags = []
        self.assertEqual(study.tags, [])


if __name__ == "__main__":
    main()
