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
    """Execute a function direct through IPython on a remote ipengine"""
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


def _test_result(test_type, name, state, result):
    """Write out the results of the test"""
    stderr.write("*** %s - %s - %s\n" % (state, test_type, name))

    if state == 'FAIL':
        stderr.write('###\n')
        stderr.write(''.join(result))
        stderr.write('###\n')


def _test_runner(test_type, name, func):
    """Dispatch to the corresponding runner"""
    if test_type == 'local':
        state, result = _test_wrapper_local(func)
    elif test_type == 'moi':
        state, result = _test_wrapper_moi(func)
    elif test_type == 'remote':
        state, result = _test_wrapper_remote(func)
    else:
        raise ValueError("Unknown test type: %s" % test_type)

    _test_result(test_type, name, state, result)


def test(runner):
    """Test the environment

    * Verify redis connectivity indepedent of moi
    * Verify database connectivity
    * Verify submission via moi

    Tests are performed both on the server and ipengines.
    """
    def redis_test(**kwargs):
        from redis import Redis
        from qiita_core.configuration_manager import ConfigurationManager
        config = ConfigurationManager()

        r_client = Redis(host=config.redis_host,
                         port=config.redis_port,
                         password=config.redis_password,
                         db=config.redis_db)
        r_client.set('---qiita-test---', 42, ex=1)
        return r_client.get('---qiita-test---') == 42

    def postgres_test(**kwargs):
        from qiita_db.sql_connection import SQLConnectionHandler
        c = SQLConnectionHandler()
        return c.execute("SELECT 42") == 42

    def moi_test(**kwargs):
        from moi.job import submit_nouser
        def inner(a, b, **kwargs):
            return a + b
        _, _, ar = submit_nouser(inner, 7, 35)

    if runner == 'all':
        runner = ('local', 'remote', 'moi')
    else:
        runner = [runner]

    for name in runner:
        _test_runner(name, "redis", redis_test)
        _test_runner(name, "postgres", postgres_test)
        _test_runner(name, "submit via moi", moi_test)
