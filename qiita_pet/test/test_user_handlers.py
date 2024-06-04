# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from wtforms.validators import ValidationError
from wtforms import StringField

from qiita_pet.test.tornado_test_base import TestHandlerBase
from qiita_pet.handlers.user_handlers import UserProfile


class TestUserProfile(TestHandlerBase):
    # TODO: add proper test for this once figure out how. Issue 567
    pass


class TestUserProfileHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/profile/')
        self.assertEqual(response.code, 200)

    def test_post_password(self):
        post_args = {
            'action': 'password',
            'oldpass': 'password',
            'newpass': 'newpass'
        }
        response = self.post('/profile/', post_args)
        self.assertEqual(response.code, 200)

    def test_post_profile(self):
        post_args = {
            'action': ['profile'],
            'affiliation': ['NEWNAME'],
            'address': ['ADDRESS'],
            'name': ['TESTDUDE'],
            'phone': ['111-222-3333'],
            'social_orcid': [''],
            'social_googlescholar': [''],
            'social_researchgate': ['']}
        response = self.post('/profile/', post_args)
        self.assertEqual(response.code, 200)

    def test_validators_social(self):
        # None or empty should be valid
        obs = UserProfile.validate_general(None, "", "")
        self.assertEqual(obs, None)
        obs = UserProfile.validate_general("", "", "")
        self.assertEqual(obs, None)

        # having white spaces should raise errors
        with self.assertRaises(ValidationError):
            obs = UserProfile.validate_general(" infix", "", "")
        with self.assertRaises(ValidationError):
            obs = UserProfile.validate_general("infix ", "", "")
        with self.assertRaises(ValidationError):
            obs = UserProfile.validate_general(" infix ", "", "")
        obs = UserProfile.validate_general("infix", "", "")
        self.assertEqual(obs, 'infix')

        with self.assertRaises(ValidationError):
            obs = UserProfile.validate_general(
                "http://kurt.com/id1234", "msg", r"http://kurt.\w{1,3}/")

    def test_validator_orcid_id(self):
        field = StringField("testfield")

        field.data = "0000-0002-0975-9019"
        obs = UserProfile.validator_orcid_id(None, field)
        self.assertEqual(obs, None)

        field.data = "https://orcid.org/0000-0002-0975-9019"
        with self.assertRaises(ValidationError):
            obs = UserProfile.validator_orcid_id(None, field)

        field.data = "wrong"
        with self.assertRaises(ValidationError):
            obs = UserProfile.validator_orcid_id(None, field)

    def test_validator_gscholar_id(self):
        field = StringField("testfield")

        field.data = "_e3QL94AAAAJ"
        obs = UserProfile.validator_gscholar_id(None, field)
        self.assertEqual(obs, None)

        field.data = ('https://scholar.google.com/citations?user=_e3QL94AAAAJ&'
                      'hl=en')
        with self.assertRaises(ValidationError):
            obs = UserProfile.validator_gscholar_id(None, field)

        field.data = 'user=_e3QL94AAAAJ&hl=en'
        with self.assertRaises(ValidationError):
            obs = UserProfile.validator_gscholar_id(None, field)

        field.data = 'user=_e3QL94AAAAJ'
        with self.assertRaises(ValidationError):
            obs = UserProfile.validator_gscholar_id(None, field)

        field.data = '=_e3QL94AAAAJ'
        with self.assertRaises(ValidationError):
            obs = UserProfile.validator_gscholar_id(None, field)

    def test_validator_rgate_id(self):
        field = StringField("testfield")

        field.data = "Rob-Knight"
        obs = UserProfile.validator_rgate_id(None, field)
        self.assertEqual(obs, None)

        field.data = 'https://www.researchgate.net/profile/Rob-Knight'
        with self.assertRaises(ValidationError):
            obs = UserProfile.validator_rgate_id(None, field)


class TestUserJobsHandler(TestHandlerBase):
    def test_get(self):
        response = self.get('/user/jobs/')
        self.assertEqual(response.code, 200)


if __name__ == "__main__":
    main()
