# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from unittest import TestCase, main
from os.path import join

from qiita_db.util import get_mountpoint
from qiita_pet.handlers.api_proxy.util import check_access, check_fp


class TestUtil(TestCase):
    def test_check_access(self):
        obs = check_access(1, 'test@foo.bar')
        self.assertEqual(obs, {})

    def test_check_access_no_access(self):
        obs = check_access(1, 'demo@microbio.me')
        exp = {'status': 'error',
               'message': 'User does not have access to study'}
        self.assertEqual(obs, exp)

    def test_check_access_bad_id(self):
        obs = check_access(232423423, 'test@foo.bar')
        exp = {'status': 'error',
               'message': 'Study does not exist'}
        self.assertEqual(obs, exp)

    def test_check_fp(self):
        obs = check_fp(1, 'uploaded_file.txt')
        _, base_fp = get_mountpoint("uploads")[0]
        exp = {'status': 'success',
               'message': '',
               'file': join(base_fp, '1', 'uploaded_file.txt')}
        self.assertEqual(obs, exp)

    def test_check_fp_bad_fp(self):
        obs = check_fp(1, 'badfile')
        exp = {'status': 'error',
               'message': 'file does not exist',
               'file': 'badfile'}
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    main()
