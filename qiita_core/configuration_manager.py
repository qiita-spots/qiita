# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from functools import partial
from os.path import join, dirname, abspath, isdir
from os import environ
from future import standard_library
with standard_library.hooks():
    from configparser import (ConfigParser, NoOptionError,
                              MissingSectionHeaderError)


class ConfigurationManager(object):
    """Holds the QIITA configuration

    Parameters
    ----------
    conf_fp: str, optional
        Filepath to the configuration file. Default: config_test.txt

    Attributes
    ----------
    test_environment : bool
        If true, we are in a test environment.
    base_data_dir : str
        Path to the base directorys where all data file are stored
    upload_data_dir : str
        Path to the base directorys where all data file are stored
    user : str
        The postgres user
    password : str
        The postgres password for the previous user
    database : str
        The postgres database to connect to
    host : str
        The host where the database lives
    port : int
        The port used to connect to the postgres database in the previous host
    ipyc_demo : str
        The IPython demo cluster profile
    ipyc_demo_n : int
        The size of the demo cluster
    ipyc_reserved : str
        The IPython reserved cluster profile
    ipyc_reserved_n : int
        The size of the reserved cluster
    ipyc_general : str
        The IPython general cluster profile
    ipyc_general_n : int
        The size of the general cluster
    """
    def __init__(self):
        # If conf_fp is None, we default to the test configuration file
        try:
            conf_fp = environ['QIITA_CONFIG_FP']
        except KeyError:
            conf_fp = join(dirname(abspath(__file__)),
                           'support_files/config_test.txt')

        # Parse the configuration file
        config = ConfigParser()
        with open(conf_fp, 'U') as conf_file:
            config.readfp(conf_file)

        _expected_sections = {'main', 'ipython', 'redis', 'postgres',
                              'smtp'}
        if set(config.sections()) != _expected_sections:
            missing = _expected_sections - set(config.sections())
            raise MissingSectionHeaderError("Missing: %r" % missing)

        self._get_main(config)
        self._get_smtp(config)
        self._get_postgres(config)
        self._get_redis(config)
        self._get_ipython(config)

    def _get_main(self, config):
        """Get the configuration of the main section"""
        self.test_environment = config.getboolean('main', 'TEST_ENVIRONMENT')
        try:
            self.base_data_dir = config.get('main', 'BASE_DATA_DIR')
        except NoOptionError as e:
            if self.test_environment:
                self.base_data_dir = join(dirname(abspath(__file__)),
                                          '../test_data')
            else:
                raise e

        self.upload_data_dir = config.get('main', 'UPLOAD_DATA_DIR')
        if not isdir(self.upload_data_dir):
            raise ValueError("The UPLOAD_DATA_DIR (%s) folder doesn't exist" %
                             self.upload_data_dir)

    def _get_postgres(self, config):
        """Get the configuration of the postgres section"""
        self.user = config.get('postgres', 'USER')
        try:
            self.password = config.get('postgres', 'PASSWORD')
        except NoOptionError as e:
            if self.test_environment:
                self.password = None
            else:
                raise e
        self.database = config.get('postgres', 'DATABASE')
        self.host = config.get('postgres', 'HOST')
        self.port = config.getint('postgres', 'PORT')

    def _get_redis(self, config):
        """Get the configuration of the redis section"""
        pass

    def _get_ipython(self, config):
        """Get the configuration of the ipython section"""
        sec_get = partial(config.get, 'ipython')
        sec_getint = partial(config.getint, 'ipython')

        self.ipyc_demo = sec_get('DEMO_CLUSTER')
        self.ipyc_reserved = sec_get('RESERVED_CLUSTER')
        self.ipyc_general = sec_get('GENERAL_CLUSTER')

        self.ipyc_demo_n = sec_getint('DEMO_CLUSTER_SIZE')
        self.ipyc_reserved_n = sec_getint('RESERVED_CLUSTER_SIZE')
        self.ipyc_general_n = sec_getint('GENERAL_CLUSTER_SIZE')

    def _get_smtp(self, config):
        sec_get = partial(config.get, 'smtp')
        sec_getint = partial(config.getint, 'smtp')
        sec_getbool = partial(config.getboolean, 'smtp')

        self.smtp_host = sec_get("HOST")
        self.smtp_port = sec_getint("PORT")
        self.smtp_user = sec_get("USER")
        self.smtp_password = sec_get("PASSWORD")
        self.smtp_ssl = sec_getbool("SSL")
        self.smtp_email = sec_get('EMAIL')
