# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from functools import wraps
from os.path import dirname
from git import Repo
from git.exc import InvalidGitRepositoryError

from qiita_core.qiita_settings import qiita_config, r_client
from qiita_pet import __version__ as qiita_pet_lib_version
from qiita_db.sql_connection import TRN
from qiita_db.environment_manager import reset_test_database


def is_test_environment():
    """Checks if Qiita is running in a test environment

    Returns
    -------
    bool
        Whether Qiita is running in a test environment or not

    Notes
    -----
    Qiita is running in a test environment if:
        - It is connected to a test database, AND
        - The config file indicates that this is a test environment
    """
    # Check that we are not in a production environment
    with TRN:
        TRN.add("SELECT test FROM settings")
        test_db = TRN.execute_fetchflatten()[0]
    return qiita_config.test_environment and test_db


def qiita_test_checker(test=False):
    """Decorator that allows the execution of all methods in a test class only
    and only if Qiita is set up to work in a test environment.

    Parameters
    ----------
    test : bool, optional
        If True it will raise a RuntimeError error

    Raises
    ------
    RuntimeError
        If Qiita is set up to work in a production environment
    """
    def class_modifier(cls):
        if not is_test_environment() or test:
            raise RuntimeError("Working in a production environment. Not "
                               "executing the tests to keep the production "
                               "database safe.")

        # Now, we decorate the setup and teardown functions
        class DecoratedClass(cls):
            def setUp(self):
                super(DecoratedClass, self).setUp()

            @classmethod
            @reset_test_database
            def tearDownClass(cls):
                pass

        return DecoratedClass
    return class_modifier


def execute_as_transaction(func):
    """Decorator to make a method execute inside a transaction"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        from qiita_db.sql_connection import TRN
        with TRN:
            return func(*args, **kwargs)
    return wrapper


def get_qiita_version():
    """Returns the Qiita version and Git sha if present

    Returns
    ------
    tuple (version, sha)
        The Qiita version and SHA. SHA can be an empty string.
    """
    # the actual repo is the abspath of the current file without
    # qiita_core
    git_repo_path = dirname(dirname(__file__))

    try:
        repo = Repo(git_repo_path)
        sha = repo.active_branch.commit.hexsha
    except (InvalidGitRepositoryError, TypeError):
        sha = ''

    return (qiita_pet_lib_version, sha)


def get_release_info(study_status='public'):
    """Returns the studies and the archive release details

    Parameters
    ----------
    study_status : str, optional
        The study status to search for. Note that this should always be set
        to 'public' but having this exposed helps with testing. The other
        options are 'private' and 'sandbox'

    Returns
    ------
    ((str, str, str), (str, str, str))
        The release MD5, filepath and timestamp
    """
    portal = qiita_config.portal
    md5sum = r_client.get('%s:release:%s:md5sum' % (portal, study_status))
    filepath = r_client.get('%s:release:%s:filepath' % (portal, study_status))
    timestamp = r_client.get('%s:release:%s:time' % (portal, study_status))
    # replacing None values for empty strings as the text is displayed nicely
    # in the GUI
    if md5sum is None:
        md5sum = b''
    if filepath is None:
        filepath = b''
    if timestamp is None:
        timestamp = b''
    biom_metadata_release = ((md5sum, filepath, timestamp))

    md5sum = r_client.get('release-archive:md5sum')
    filepath = r_client.get('release-archive:filepath')
    timestamp = r_client.get('release-archive:time')
    # replacing None values for empty strings as the text is displayed nicely
    # in the GUI
    if md5sum is None:
        md5sum = b''
    if filepath is None:
        filepath = b''
    if timestamp is None:
        timestamp = b''
    archive_release = ((md5sum, filepath, timestamp))

    return (biom_metadata_release, archive_release)
