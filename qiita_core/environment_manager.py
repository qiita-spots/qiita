# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os import fork
from sys import exit, exc_info, stderr
import traceback

from IPython.parallel.apps.ipclusterapp import IPClusterStart, IPClusterStop


MAX_TEST_WAIT = 5
TEST_RUNNERS = ('local', 'remote', 'moi', 'all')


def start_cluster(profile):
    """Start a cluster"""
    me = fork()
    if me == 0:
        c = IPClusterStart(profile=profile, log_level=0, daemonize=True)
        c.initialize(argv=[])
        c.start()


def stop_cluster(profile):
    """Stop a cluster"""
    me = fork()
    if me == 0:
        c = IPClusterStop(profile=profile, log_level=0)
        c.initialize(argv=[])
        c.start()
        exit(0)


def _test_wrapper_local(func):
    """Execute a function locally"""
    try:
        return ('SUCCESS', func())
    except:
        return ('FAIL', traceback.format_exception(*exc_info()))


def _test_wrapper_moi(func):
    """Submit a function through moi"""
    try:
        from moi.job import submit_nouser
        _, _, ar = submit_nouser(func)
    except:
        return ('FAIL', traceback.format_exception(*exc_info()))

    return _ipy_wait(ar)


def _test_wrapper_remote(func):
    """Execute a function on a remote ipengine"""
    from IPython.parallel import Client
    from qiita_core.configuration_manager import ConfigurationManager
    config = ConfigurationManager()
    c = Client(profile=config.ipython_default)
    bv = c.load_balanced_view()
    return _ipy_wait(bv.apply_async(func))


def _ipy_wait(ar):
    """Wait on a IPython AsyncResult"""
    ar.wait(timeout=MAX_TEST_WAIT)

    if ar.ready():
        result = _test_wrapper_local(ar.get)
    else:
        result = ('FAIL', 'No result after %d seconds' % MAX_TEST_WAIT)

    return result


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


def _test_runner(test_type, name, func, expected):
    """Dispatch to the corresponding runner"""
    if test_type == 'local':
        state, result = _test_wrapper_local(func)
    elif test_type == 'moi':
        state, result = _test_wrapper_moi(func)
    elif test_type == 'remote':
        state, result = _test_wrapper_remote(func)
    else:
        raise ValueError("Unknown test type: %s" % test_type)

    _test_result(test_type, name, state, result, expected)


def test(runner):
    """Test the environment

    * Verify redis connectivity indepedent of moi
    * Verify database connectivity
    * Verify submission via moi

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

    def moi_test(**kwargs):
        """Submit a function via moi"""
        from moi.job import submit_nouser

        def inner(a, b, **kwargs):
            return a + b

        _, _, ar = submit_nouser(inner, 7, 35)
        state, result = _ipy_wait(ar)
        return result

    if runner == 'all':
        runner = ('local', 'remote', 'moi')
    else:
        runner = [runner]

    for name in runner:
        _test_runner(name, "redis", redis_test, 42)
        _test_runner(name, "postgres", postgres_test, 42)
        _test_runner(name, "submit via moi", moi_test, 42)
