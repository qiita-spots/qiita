#
# Copyright (c) 2014, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3clause License.
#
# The full license is in the file LICENSE, distributed with this software.
#

from sys import exc_info, stderr
import traceback


MAX_TEST_WAIT = 5
TEST_RUNNERS = ('local', 'remote', 'all')


def _test_wrapper_local(func):
    """Execute a function locally"""
    try:
        return ('SUCCESS', func())
    except:
        return ('FAIL', traceback.format_exception(*exc_info()))


def _test_result(test_type, name, state, result, expected):
    """Write out the results of the test"""
    correct_result = result == expected

    to_write = ["**** Name: %s" % name,
                "**** Runner: %s" % test_type,
                "**** Execution: %s" % state]

    if correct_result:
        to_write.append('**** Correct result: %s' % str(correct_result))
    else:
        to_write.append('#### EXPECTED RESULT: %s' % str(expected))
        to_write.append('#### OBSERVED RESULT: %s' % str(result))

    stderr.write('\n'.join(to_write))
    stderr.write('\n')

    if state == 'FAIL':
        stderr.write('#' * 80)
        stderr.write('\n')
        stderr.write(''.join(result))
        stderr.write('#' * 80)
        stderr.write('\n')

    stderr.write('\n')


def test(runner):
    """Test the environment

    * Verify redis connectivity
    * Verify database connectivity

    Tests are performed both on the server and ipengines.
    """
    def redis_test(**kwargs):
        """Put and get a key from redis"""
        from uuid import uuid4
        from redis import Redis
        from qiita_core.configuration_manager import ConfigurationManager
        config = ConfigurationManager()

        r_client = Redis(host=config.redis_host,
                         port=config.redis_port,
                         password=config.redis_password,
                         db=config.redis_db)
        key = str(uuid4())
        r_client.set(key, 42, ex=1)
        return int(r_client.get(key))

    def postgres_test(**kwargs):
        """Open a connection and query postgres"""
        from qiita_db.sql_connection import SQLConnectionHandler
        c = SQLConnectionHandler()
        return c.execute_fetchone("SELECT 42")[0]

    if runner == 'all':
        runner = ('local', )
    else:
        runner = [runner]

    for name in runner:
        _test_runner(name, "redis", redis_test, 42)
        _test_runner(name, "postgres", postgres_test, 42)


def _test_runner(test_type, name, func, expected):
    """Dispatch to the corresponding runner"""
    if test_type == 'local':
        state, result = _test_wrapper_local(func)
    else:
        raise ValueError("Unknown test type: %s" % test_type)

    _test_result(test_type, name, state, result, expected)
