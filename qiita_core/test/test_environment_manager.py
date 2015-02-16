# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from time import sleep

from IPython.parallel import Client

from qiita_core.environment_manager import (
    start_cluster, stop_cluster, _test_wrapper_local, _test_wrapper_remote,
    _test_result, _test_wrapper_moi, _ipy_wait, _test_runner, environment_test)
from qiita_core.configuration_manager import ConfigurationManager


# general funcs for testing
def func_success():
    return 4


def func_raise_value_error():
    raise ValueError('error')


def func_success_moi(moi_update_status, moi_context, moi_parent_id):
    return 4


class EnvironmentManager(TestCase):
    """Tests the environment manager"""

    def setUp(self):
        self.wait_time = 5
        self.config = ConfigurationManager()

    def test_start_and_stop_cluster(self):
        profile_name = 'qiita_test_cluster_name'

        # start cluster
        start_cluster(profile_name)

        # wait for cluster to be created
        sleep(self.wait_time)

        # test that it exists, if it doesn't exist the command will fail
        Client(profile=profile_name)

        # stop cluster
        stop_cluster(profile_name)

        # wait for cluster to be terminated
        sleep(self.wait_time)

        # test that cluster is not running
        with self.assertRaises(IOError):
                Client(profile=profile_name)

    def test__test_wrapper_moi(self):
        obs = _test_wrapper_moi(func_success_moi)
        exp = ('SUCCESS', 4)
        self.assertEqual(exp, obs)

        obs, traceback = _test_wrapper_moi(func_raise_value_error)
        self.assertEqual('FAIL', obs)

    def test__ipy_wait(self):
        rc = Client(profile=self.config.ipython_default)
        bv = rc.load_balanced_view()

        obs = _ipy_wait(bv.apply_async(func_success))
        exp = ('SUCCESS', 4)
        self.assertEqual(exp, obs)

        msg, traceback = _ipy_wait(bv.apply_async(func_raise_value_error))
        self.assertEqual('FAIL', msg)

    def test__test_wrapper_local(self):
        msg, func = _test_wrapper_local(func_success)
        self.assertEqual('SUCCESS', msg)

        msg, func = _test_wrapper_local(func_raise_value_error)
        self.assertEqual('FAIL', msg)

    def test__test_wrapper_remote(self):
        msg, result = _test_wrapper_remote(func_success)
        self.assertEqual(('SUCCESS', 4), (msg, result))

    def test__test_result(self):
        obs = _test_result(
            'test_type', 'name', 'FAIL', 'result', 'result', False)
        exp = ['**** Name: name', '**** Runner: test_type',
               '**** Execution: FAIL', '**** Correct result: True', '',
               '#' * 80, '', 'result', '', '#' * 80, '', '']
        self.assertEqual(exp, obs)

        obs = _test_result(
            'test_type', 'name', 'SUCCESS', 'result', 'result', False)
        exp = ['**** Name: name', '**** Runner: test_type',
               '**** Execution: SUCCESS', '**** Correct result: True', '', '']
        self.assertEqual(exp, obs)

        obs = _test_result(
            'test_type', 'name', 'FAIL', 'result', 'expected', False)
        exp = ['**** Name: name', '**** Runner: test_type',
               '**** Execution: FAIL', '#### EXPECTED RESULT: expected',
               '#### OBSERVED RESULT: result', '', '#' * 80,  '', 'result',
               '', '#' * 80, '', '']
        self.assertEqual(exp, obs)

        obs = _test_result(
            'test_type', 'name', 'SUCCESS', 'result', 'expected', False)
        exp = ['**** Name: name', '**** Runner: test_type',
               '**** Execution: SUCCESS', '#### EXPECTED RESULT: expected',
               '#### OBSERVED RESULT: result', '', '']
        self.assertEqual(exp, obs)

    def test_testers(self):
        # running the tests should be enough to test
        _test_runner('local', 'name', func_success, 4)
        # _test_runner('moi', 'name', func_success_moi, 4)
        _test_runner('remote', 'name', func_success, 4)

        with self.assertRaises(ValueError):
            _test_runner('erorr', 'name', func_success, 4)

        # environment_test('all')

if __name__ == '__main__':
    main()
