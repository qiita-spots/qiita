# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.exceptions import (IncorrectEmailError, IncorrectPasswordError,
                                   IncompetentQiitaDeveloperError)
from qiita_core.util import qiita_test_checker
from qiita_db.user import User
from qiita_db.exceptions import (QiitaDBDuplicateError, QiitaDBColumnError,
                                 QiitaDBUnknownIDError)


@qiita_test_checker()
class UserTest(TestCase):
    """Tests the User object and all properties/methods"""

    def setUp(self):
        self.user = User('admin@foo.bar')

        self.userinfo = {
            'name': 'Dude',
            'affiliation': 'Nowhere University',
            'address': '123 fake st, Apt 0, Faketown, CO 80302',
            'phone': '111-222-3344'
        }

    def test_instantiate_user(self):
        User('admin@foo.bar')

    def test_instantiate_unknown_user(self):
        with self.assertRaises(QiitaDBUnknownIDError):
            User('FAIL@OMG.bar')

    def _check_correct_info(self, obs, exp):
        self.assertEqual(set(exp.keys()), set(obs.keys()))
        for key in exp:
            # user_verify_code and password seed randomly generated so just
            # making sure they exist and is correct length
            if key == 'user_verify_code':
                self.assertEqual(len(obs[key]), 20)
            elif key == "password":
                self.assertEqual(len(obs[key]), 60)
            else:
                self.assertEqual(obs[key], exp[key])

    def test_create_user(self):
        user = User.create('new@test.bar', 'password')
        self.assertEqual(user.id, 'new@test.bar')
        sql = "SELECT * from qiita.qiita_user WHERE email = 'new@test.bar'"
        obs = self.conn_handler.execute_fetchall(sql)
        self.assertEqual(len(obs), 1)
        obs = dict(obs[0])
        exp = {
            'password': '',
            'name': None,
            'pass_reset_timestamp': None,
            'affiliation': None,
            'pass_reset_code': None,
            'phone': None,
            'user_verify_code': '',
            'address': None,
            'user_level_id': 5,
            'email': 'new@test.bar'}
        self._check_correct_info(obs, exp)

    def test_create_user_info(self):
        user = User.create('new@test.bar', 'password', self.userinfo)
        self.assertEqual(user.id, 'new@test.bar')
        sql = "SELECT * from qiita.qiita_user WHERE email = 'new@test.bar'"
        obs = self.conn_handler.execute_fetchall(sql)
        self.assertEqual(len(obs), 1)
        obs = dict(obs[0])
        exp = {
            'password': '',
            'name': 'Dude',
            'affiliation': 'Nowhere University',
            'address': '123 fake st, Apt 0, Faketown, CO 80302',
            'phone': '111-222-3344',
            'pass_reset_timestamp': None,
            'pass_reset_code': None,
            'user_verify_code': '',
            'user_level_id': 5,
            'email': 'new@test.bar'}
        self._check_correct_info(obs, exp)

    def test_create_user_column_not_allowed(self):
        self.userinfo["pass_reset_code"] = "FAIL"
        with self.assertRaises(QiitaDBColumnError):
            User.create('new@test.bar', 'password', self.userinfo)

    def test_create_user_non_existent_column(self):
        self.userinfo["BADTHING"] = "FAIL"
        with self.assertRaises(QiitaDBColumnError):
            User.create('new@test.bar', 'password', self.userinfo)

    def test_create_user_duplicate(self):
        with self.assertRaises(QiitaDBDuplicateError):
            User.create('test@foo.bar', 'password')

    def test_create_user_bad_email(self):
        with self.assertRaises(IncorrectEmailError):
            User.create('notanemail', 'password')

    def test_create_user_bad_password(self):
        with self.assertRaises(IncorrectPasswordError):
            User.create('new@test.com', '')

    def test_login(self):
        self.assertEqual(User.login("test@foo.bar", "password"),
                         User("test@foo.bar"))

    def test_login_incorrect_user(self):
        with self.assertRaises(IncorrectEmailError):
            User.login("notexist@foo.bar", "password")

    def test_login_incorrect_password(self):
        with self.assertRaises(IncorrectPasswordError):
            User.login("test@foo.bar", "WRONGPASSWORD")

    def test_login_invalid_password(self):
        with self.assertRaises(IncorrectPasswordError):
            User.login("test@foo.bar", "SHORT")

    def test_exists(self):
        self.assertTrue(User.exists("test@foo.bar"))

    def test_exists_notindb(self):
        self.assertFalse(User.exists("notexist@foo.bar"))

    def test_exists_invaid_email(self):
        with self.assertRaises(IncorrectEmailError):
            User.exists("notanemail@badformat")

    def test_get_email(self):
        self.assertEqual(self.user.email, 'admin@foo.bar')

    def test_get_level(self):
        self.assertEqual(self.user.level, "user")

    def test_get_info(self):
        expinfo = {
            'name': 'Admin',
            'affiliation': 'Owner University',
            'address': '312 noname st, Apt K, Nonexistantown, CO 80302',
            'phone': '222-444-6789'
        }
        self.assertEqual(self.user.info, expinfo)

    def test_set_info(self):
        self.user.info = self.userinfo
        self.assertEqual(self.user.info, self.userinfo)

    def test_set_info_not_info(self):
        """Tests setting info with a non-allowed column"""
        self.userinfo["email"] = "FAIL"
        with self.assertRaises(QiitaDBColumnError):
            self.user.info = self.userinfo

    def test_set_info_bad_info(self):
        """Test setting info with a key not in the table"""
        self.userinfo["BADTHING"] = "FAIL"
        with self.assertRaises(QiitaDBColumnError):
            self.user.info = self.userinfo

    def test_get_private_studies(self):
        user = User('test@foo.bar')
        self.assertEqual(user.private_studies, [1])

    def test_get_shared_studies(self):
        user = User('shared@foo.bar')
        self.assertEqual(user.shared_studies, [1])

    def test_get_private_analyses(self):
        self.assertEqual(self.user.private_analyses, [])

    def test_get_shared_analyses(self):
        self.assertEqual(self.user.shared_analyses, [])

    def test_verify_code(self):
        sql = ("insert into qiita.qiita_user values ('test@user.com', '1', "
               "'testtest', 'testuser', '', '', '', 'verifycode', 'resetcode'"
               ",null)")
        self.conn_handler.execute(sql)
        self.assertTrue(User.verify_code('test@user.com', 'verifycode',
                                         'create'))
        self.assertTrue(User.verify_code('test@user.com', 'resetcode',
                                         'reset'))
        self.assertFalse(User.verify_code('test@user.com', 'wrongcode',
                                          'create'))
        self.assertFalse(User.verify_code('test@user.com', 'wrongcode',
                                          'reset'))
        with self.assertRaises(IncompetentQiitaDeveloperError):
            User.verify_code('test@user.com', 'fakecode', 'badtype')


if __name__ == "__main__":
    main()
