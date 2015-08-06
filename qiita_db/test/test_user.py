# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from datetime import datetime

from qiita_core.exceptions import (IncorrectEmailError, IncorrectPasswordError,
                                   IncompetentQiitaDeveloperError)
from qiita_core.util import qiita_test_checker
from qiita_core.qiita_settings import qiita_config
from qiita_db.util import hash_password, add_system_message
from qiita_db.user import User, validate_password, validate_email
from qiita_db.exceptions import (QiitaDBDuplicateError, QiitaDBColumnError,
                                 QiitaDBUnknownIDError, QiitaDBError)


class SupportTests(TestCase):
    def test_validate_password(self):
        valid1 = 'abcdefgh'
        valid2 = 'abcdefgh1234'
        valid3 = 'abcdefgh!@#$'
        valid4 = 'aBC123!@#{}'
        invalid1 = 'abc'
        invalid2 = u'øabcdefghi'
        invalid3 = 'abcd   efgh'

        self.assertTrue(validate_password(valid1))
        self.assertTrue(validate_password(valid2))
        self.assertTrue(validate_password(valid3))
        self.assertTrue(validate_password(valid4))
        self.assertFalse(validate_password(invalid1))
        self.assertFalse(validate_password(invalid2))
        self.assertFalse(validate_password(invalid3))

    def test_validate_email(self):
        valid1 = 'foo@bar.com'
        valid2 = 'asdasd.asdasd.asd123asd@stuff.edu'
        valid3 = 'w00t@123.456.789.com'
        valid4 = 'name@a.b-c.d'
        invalid1 = '@stuff.com'
        invalid2 = 'asdasdásd@things.com'
        invalid3 = '.asdas@com'
        invalid4 = 'name@a.b-c.d-'

        self.assertTrue(validate_email(valid1))
        self.assertTrue(validate_email(valid2))
        self.assertTrue(validate_email(valid3))
        self.assertTrue(validate_email(valid4))
        self.assertFalse(validate_email(invalid1))
        self.assertFalse(validate_email(invalid2))
        self.assertFalse(validate_email(invalid3))
        self.assertFalse(validate_email(invalid4))


@qiita_test_checker()
class UserTest(TestCase):
    """Tests the User object and all properties/methods"""

    def setUp(self):
        self.user = User('admin@foo.bar')
        self.portal = qiita_config.portal

        self.userinfo = {
            'name': 'Dude',
            'affiliation': 'Nowhere University',
            'address': '123 fake st, Apt 0, Faketown, CO 80302',
            'phone': '111-222-3344',
            'pass_reset_code': None,
            'pass_reset_timestamp': None,
            'user_verify_code': None
        }

    def tearDown(self):
        qiita_config.portal = self.portal

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
        self.userinfo["email"] = "FAIL"
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

    def test_exists_invalid_email(self):
        with self.assertRaises(IncorrectEmailError):
            User.exists("notanemail.@badformat")

    def test_get_email(self):
        self.assertEqual(self.user.email, 'admin@foo.bar')

    def test_get_level(self):
        self.assertEqual(self.user.level, "admin")

    def test_get_info(self):
        expinfo = {
            'name': 'Admin',
            'affiliation': 'Owner University',
            'address': '312 noname st, Apt K, Nonexistantown, CO 80302',
            'phone': '222-444-6789',
            'pass_reset_code': None,
            'pass_reset_timestamp': None,
            'user_verify_code': None,
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

    def test_default_analysis(self):
        qiita_config.portal = "QIITA"
        obs = self.user.default_analysis
        self.assertEqual(obs, 4)

        qiita_config.portal = "EMP"
        obs = self.user.default_analysis
        self.assertEqual(obs, 8)

    def test_get_user_studies(self):
        user = User('test@foo.bar')
        qiita_config.portal = "QIITA"
        self.assertEqual(user.user_studies, {1})

        qiita_config.portal = "EMP"
        self.assertEqual(user.user_studies, set())

    def test_get_shared_studies(self):
        user = User('shared@foo.bar')
        qiita_config.portal = "QIITA"
        self.assertEqual(user.shared_studies, {1})

        qiita_config.portal = "EMP"
        self.assertEqual(user.shared_studies, set())

    def test_get_private_analyses(self):
        user = User('test@foo.bar')
        qiita_config.portal = "QIITA"
        self.assertEqual(user.private_analyses, set([1, 2]))

        qiita_config.portal = "EMP"
        self.assertEqual(user.private_analyses, set())

    def test_get_shared_analyses(self):
        user = User('shared@foo.bar')
        qiita_config.portal = "QIITA"
        self.assertEqual(user.shared_analyses, set([1]))

        qiita_config.portal = "EMP"
        self.assertEqual(user.shared_analyses, set())

    def test_verify_code(self):
        add_system_message("TESTMESSAGE", datetime.now())
        sql = ("insert into qiita.qiita_user values ('new@test.bar', '1', "
               "'testtest', 'testuser', '', '', '', 'verifycode', 'resetcode'"
               ",null)")
        self.conn_handler.execute(sql)

        self.assertFalse(User.verify_code('new@test.bar', 'wrongcode',
                                          'create'))
        self.assertFalse(User.verify_code('new@test.bar', 'wrongcode',
                                          'reset'))

        self.assertTrue(User.verify_code('new@test.bar', 'verifycode',
                                         'create'))
        self.assertTrue(User.verify_code('new@test.bar', 'resetcode',
                                         'reset'))

        # make sure errors raised if code already used or wrong type
        with self.assertRaises(QiitaDBError):
            User.verify_code('new@test.bar', 'verifycode', 'create')
        with self.assertRaises(QiitaDBError):
            User.verify_code('new@test.bar', 'resetcode', 'reset')

        with self.assertRaises(IncompetentQiitaDeveloperError):
            User.verify_code('new@test.bar', 'fakecode', 'badtype')

        # make sure default analyses created
        sql = ("SELECT email, name, description, dflt FROM qiita.analysis "
               "WHERE email = 'new@test.bar'")
        obs = self.conn_handler.execute_fetchall(sql)
        exp = [['new@test.bar', 'new@test.bar-dflt-2', 'dflt', True],
               ['new@test.bar', 'new@test.bar-dflt-1', 'dflt', True]]
        self.assertEqual(obs, exp)

        # Make sure default analyses are linked with the portal
        sql = """SELECT COUNT(1)
                 FROM qiita.analysis
                    JOIN qiita.analysis_portal USING (analysis_id)
                    JOIN qiita.portal_type USING (portal_type_id)
                 WHERE email = 'new@test.bar' AND dflt = true"""
        self.assertEqual(self.conn_handler.execute_fetchone(sql)[0], 2)

        # Make sure system messages are linked to user
        sql = """SELECT message_id FROM qiita.message_user
                 WHERE email = 'new@test.bar'"""
        self.assertEqual(self.conn_handler.execute_fetchall(sql), [[4]])

    def _check_pass(self, passwd):
        obspass = self.conn_handler.execute_fetchone(
            "SELECT password FROM qiita.qiita_user WHERE email = %s",
            (self.user.id, ))[0]
        self.assertEqual(hash_password(passwd, obspass), obspass)

    def test_change_pass(self):
        self.user._change_pass("newpassword")
        self._check_pass("newpassword")
        self.assertIsNone(self.user.info["pass_reset_code"])

    def test_change_pass_short(self):
        with self.assertRaises(IncorrectPasswordError):
            self.user._change_pass("newpass")
        self._check_pass("password")

    def test_change_password(self):
        self.user.change_password("password", "newpassword")
        self._check_pass("newpassword")

    def test_change_password_wrong_oldpass(self):
        self.user.change_password("WRONG", "newpass")
        self._check_pass("password")

    def test_generate_reset_code(self):
        user = User.create('new@test.bar', 'password')
        sql = "SELECT LOCALTIMESTAMP"
        before = self.conn_handler.execute_fetchone(sql)[0]
        user.generate_reset_code()
        after = self.conn_handler.execute_fetchone(sql)[0]
        sql = ("SELECT pass_reset_code, pass_reset_timestamp FROM "
               "qiita.qiita_user WHERE email = %s")
        obscode, obstime = self.conn_handler.execute_fetchone(
            sql, ('new@test.bar',))
        self.assertEqual(len(obscode), 20)
        self.assertTrue(before < obstime < after)

    def test_change_forgot_password(self):
        self.user.generate_reset_code()
        code = self.user.info["pass_reset_code"]
        obsbool = self.user.change_forgot_password(code, "newpassword")
        self.assertEqual(obsbool, True)
        self._check_pass("newpassword")

    def test_change_forgot_password_bad_code(self):
        self.user.generate_reset_code()
        code = "AAAAAAA"
        obsbool = self.user.change_forgot_password(code, "newpassword")
        self.assertEqual(obsbool, False)
        self._check_pass("password")

    def test_messages(self):
        user = User('test@foo.bar')
        obs = user.messages()
        exp_msg = [
            (1, 'message 1'),
            (2, 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. '
                'Pellentesque sed auctor ex, non placerat sapien. Vestibulum '
                'vestibulum massa ut sapien condimentum, cursus consequat diam'
                ' sodales. Nulla aliquam arcu ut massa auctor, et vehicula '
                'mauris tempor. In lacinia viverra ante quis pellentesque. '
                'Nunc vel mi accumsan, porttitor eros ut, pharetra elit. Nulla'
                ' ac nisi quis dui egestas malesuada vitae ut mauris. Morbi '
                'blandit non nisl a finibus. In erat velit, congue at ipsum '
                'sit amet, venenatis bibendum sem. Curabitur vel odio sed est '
                'rutrum rutrum. Quisque efficitur ut purus in ultrices. '
                'Pellentesque eu auctor justo.'),
            (3, 'message <a href="#">3</a>')]
        self.assertEqual([(x[0], x[1]) for x in obs], exp_msg)
        self.assertTrue(all(x[2] < datetime.now() for x in obs))
        self.assertFalse(all(x[3] for x in obs))

        obs = user.messages(1)
        exp_msg = ['message 1']
        self.assertEqual([x[1] for x in obs], exp_msg)

    def test_mark_messages(self):
        user = User('test@foo.bar')
        user.mark_messages([1, 2])
        obs = user.messages()
        exp = [True, True, False]
        self.assertEqual([x[3] for x in obs], exp)

        user.mark_messages([1], read=False)
        obs = user.messages()
        exp = [False, True, False]
        self.assertEqual([x[3] for x in obs], exp)

    def test_delete_messages(self):
        user = User('test@foo.bar')
        user.delete_messages([1, 2])
        obs = user.messages()
        exp_msg = [(3, 'message <a href="#">3</a>')]
        self.assertEqual([(x[0], x[1]) for x in obs], exp_msg)

        sql = ("SELECT message_id FROM qiita.message")
        obs = self.conn_handler.execute_fetchall(sql)
        self.assertEqual(obs, [[1], [3]])

if __name__ == "__main__":
    main()
