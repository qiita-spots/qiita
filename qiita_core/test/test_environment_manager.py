# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main

from qiita_core.util import qiita_test_checker
from qiita_core.environment_manager import (
    _test_wrapper_local, _test_wrapper_remote, _test_result)


@qiita_test_checker()
class EnvironmentManager(TestCase):
    """Tests the environment manager"""
    # Missing funcs to test:
    #   start_cluster('test')
    #   stop_cluster('test')
    #   _test_wrapper_moi(func)
    #   _ipy_wait
    #   _test_runner

    def test__test_wrapper_local(self):
        def func_success():
            return 2+2

        def func_fail():
            raise ValueError('An error')

        msg, func = _test_wrapper_local(func_success)
        self.assertEqual('SUCCESS', msg)

        msg, func = _test_wrapper_local(func_fail)
        self.assertEqual('FAIL', msg)

    def test__test_wrapper_remote(self):
        def func():
            return 4

        msg, result = _test_wrapper_remote(func)
        self.assertEqual(('SUCCESS', 4), (msg, result))

    def test__ipy_wait(self):
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

    def test__test_runner(self):
        def func():
            return 4


#
# def test(runner):
#     """Test the environment
#
#     * Verify redis connectivity indepedent of moi
#     * Verify database connectivity
#     * Verify submission via moi
#
#     Tests are performed both on the server and ipengines.
#     """
#     def redis_test(**kwargs):
#         """Put and get a key from redis"""
#         from uuid import uuid4
#         from redis import Redis
#         from qiita_core.configuration_manager import ConfigurationManager
#         config = ConfigurationManager()
#
#         r_client = Redis(host=config.redis_host,
#                          port=config.redis_port,
#                          password=config.redis_password,
#                          db=config.redis_db)
#         key = str(uuid4())
#         r_client.set(key, 42, ex=1)
#         return int(r_client.get(key))
#
#     def postgres_test(**kwargs):
#         """Open a connection and query postgres"""
#         from qiita_db.sql_connection import SQLConnectionHandler
#         c = SQLConnectionHandler()
#         return c.execute_fetchone("SELECT 42")[0]
#
#     def moi_test(**kwargs):
#         """Submit a function via moi"""
#         from moi.job import submit_nouser
#
#         def inner(a, b, **kwargs):
#             return a + b
#
#         _, _, ar = submit_nouser(inner, 7, 35)
#         state, result = _ipy_wait(ar)
#         return result
#
#     if runner == 'all':
#         runner = ('local', 'remote', 'moi')
#     else:
#         runner = [runner]
#
#     for name in runner:
#         _test_runner(name, "redis", redis_test, 42)
#         _test_runner(name, "postgres", postgres_test, 42)
#         _test_runner(name, "submit via moi", moi_test, 42)

if __name__ == '__main__':
    main()
