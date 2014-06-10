# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.util import qiita_test_checker
from qiita_db.user import User
from qiita_db.study import Study
from qiita_db.analysis import Analysis
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.exceptions import QiitaDBDuplicateError, QiitaDBColumnError


@qiita_test_checker()
class SetupTest(TestCase):
    """Tests that the test database have been successfully populated"""

    def setUp(self):
        self.conn = SQLConnectionHandler()
        self.user = User('admin@foo.bar')

        self.userinfo = {
            'name': 'Dude',
            'affiliation': 'Nowhere University',
            'address': '123 fake st, Apt 0, Faketown, CO 80302',
            'phone': '111-222-3344'
        }

    def test_create_user(self):
        user = User.create('new@test.bar', 'password')
        self.assertEqual(user.id, 'new@test.bar')
        sql = "SELECT * from qiita.qiita_user WHERE email = 'new@test.bar'"
        obs = self.conn.execute_fetchall(sql)
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
        for key in exp:
            # user_verify_code and password seed randomly generated so just
            # making sure they exist and is correct length
            if key == 'user_verify_code':
                self.assertEqual(len(obs[key]), 20)
            elif key == "password":
                self.assertEqual(len(obs[key]), 60)
            else:
                self.assertEqual(obs[key], exp[key])

    def test_create_user_info(self):
        user = User.create('new@test.bar', 'password', self.userinfo)
        self.assertEqual(user.id, 'new@test.bar')
        sql = "SELECT * from qiita.qiita_user WHERE email = 'new@test.bar'"
        obs = self.conn.execute_fetchall(sql)
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
        for key in exp:
            # user_verify_code and password seed randomly generated so just
            # making sure they exist and is correct length
            if key == 'user_verify_code':
                self.assertEqual(len(obs[key]), 20)
            elif key == "password":
                self.assertEqual(len(obs[key]), 60)
            else:
                self.assertEqual(obs[key], exp[key])

    def test_create_user_bad_info(self):
        self.userinfo["pass_reset_code"] = "FAIL"
        with self.assertRaises(QiitaDBColumnError):
            User.create('new@test.bar', 'password', self.userinfo)

    def test_create_user_not_info(self):
        self.userinfo["BADTHING"] = "FAIL"
        with self.assertRaises(QiitaDBColumnError):
            User.create('new@test.bar', 'password', self.userinfo)

    def test_create_user_duplicate(self):
        with self.assertRaises(QiitaDBDuplicateError):
            User.create('test@foo.bar', 'password')

    def test_create_user_blank_email(self):
        with self.assertRaises(IncompetentQiitaDeveloperError):
            User.create('', 'password')

    def test_create_user_blank_password(self):
        with self.assertRaises(IncompetentQiitaDeveloperError):
            User.create('new@test.com', '')

    def test_login(self):
        self.assertEqual(User.login("test@foo.bar", "password"),
                         User("test@foo.bar"))

    def test_login_incorrect_user(self):
        self.assertEqual(User.login("notexist@foo.bar", "password"),
                         None)

    def test_login_incorrect_password(self):
        self.assertEqual(User.login("test@foo.bar", "WRONG"),
                         None)

    def test_exists(self):
        self.assertEqual(User.exists("test@foo.bar"), True)

    def test_exists_notindb(self):
        self.assertEqual(User.exists("notexist@foo.bar"), False)

    def test_get_email(self):
        self.assertEqual(self.user.email, 'admin@foo.bar')

    def test_get_level(self):
        self.assertEqual(self.user.level, 4)

    def test_set_level(self):
        self.user.level = 2
        self.assertEqual(self.user.level, 2)

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
        self.userinfo["email"] = "FAIL"
        with self.assertRaises(QiitaDBColumnError):
            self.user.info = self.userinfo

    def test_set_info_bad_info(self):
        self.userinfo["BADTHING"] = "FAIL"
        with self.assertRaises(QiitaDBColumnError):
            self.user.info = self.userinfo

    def test_get_private_studies(self):
        user = User('test@foo.bar')
        self.assertEqual(user.private_studies, [Study(1)])

    def test_get_shared_studies(self):
        user = User('shared@foo.bar')
        self.assertEqual(user.shared_studies, [Study(1)])

    def test_get_private_analyses(self):
        self.assertEqual(self.user.private_analyses, [])

    def test_get_shared_analyses(self):
        self.assertEqual(self.user.shared_analyses, [])

    def test_add_shared_study(self):
        self.user.add_shared_study(Study(1))
        self.assertEqual(self.user.shared_studies, [Study(1)])

    def test_remove_shared_study(self):
        user = User('shared@foo.bar')
        user.remove_shared_study(Study(1))
        self.assertEqual(user.shared_studies, [])

    def test_add_shared_analysis(self):
        self.user.add_shared_analysis(Analysis(1))
        self.assertEqual(self.user.shared_analyses, [Analysis(1)])

    def test_remove_shared_analysis(self):
        user = User('shared@foo.bar')
        user.remove_shared_analysis(Analysis(1))
        self.assertEqual(user.shared_analyses, [])


if __name__ == "__main__":
    main()