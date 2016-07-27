# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from functools import partial
from os.path import join, dirname, abspath, isdir, expanduser
from os import environ
from future import standard_library
from base64 import b64encode
from uuid import uuid4
import warnings

from .exceptions import MissingConfigSection

with standard_library.hooks():
    from configparser import ConfigParser


class ConfigurationManager(object):
    """Holds the QIITA configuration

    Parameters
    ----------
    conf_fp: str, optional
        Filepath to the configuration file. Default: config_test.cfg

    Attributes
    ----------
    test_environment : bool
        If true, we are in a test environment.
    base_url: str
        base URL for the website, in the form http://SOMETHING.com
    base_data_dir : str
        Path to the base directorys where all data file are stored
    working_dir : str
        Path to the working directory
    max_upload_size : int
        Max upload size
    valid_upload_extension : str
        The extensions that are valid to upload, comma separated
    user : str
        The postgres user
    password : str
        The postgres password for the previous user
    admin_user : str
        The administrator user, which can be used to create/drop environments
    admin_password : str
        The postgres password for the admin_user
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
    smtp_host : str
        The SMTP host from which mail will be sent
    smtp_port : int
        The port on the SMTP host to use
    smtp_user : str
        The user on the SMTP server that will send mail
    smtp_password : str
        The password for the user on the SMTP server that will send mail
    smtp_ssl : bool
        Whether or not SSL is used when connecting to the SMTP server
    smtp_email : str
        The email address that mail will be sent from when sending mail from
        the SMTP server
    ebi_seq_xfer_user : str
        The user to use when submitting to EBI
    ebi_seq_xfer_pass : str
        The password for the ebi_seq_xfer_user
    ebi_seq_xfer_url : str
        The URL of EBI's sequence portal site
    ebi_center_name : str
        The name of the sequencing center to use when doing EBI submissions
    ebi_organization_prefix : str
        This string (with an underscore) will be prefixed to your EBI
        submission and study aliases
    redis_host : str
        The host/ip for redis
    redis_port : int
        The port for redis
    redis_password : str
        The password for redis
    redis_db : int
        The db for redis
    vamps_user : str
        The VAMPS user
    vamps_pass : str
        The VAMPS password
    vamps_url : str
        The VAMPS URL
    conf_fp : str
        The filepath for the configuration file that is loaded
    portal : str
        The portal under the Qiita instance is running under
    portal_dir : str
        The portal subdirectory used in the URL
    portal_fp : str
        The filepath to the portal styling config file
    plugin_launcher : str
        The script used to start the plugins
    portal_dir : str
        The path to the directory containing the plugin configuration files
    """
    def __init__(self):
        # If conf_fp is None, we default to the test configuration file
        try:
            conf_fp = environ['QIITA_CONFIG_FP']
        except KeyError:
            conf_fp = join(dirname(abspath(__file__)),
                           'support_files/config_test.cfg')
        self.conf_fp = conf_fp

        # Parse the configuration file
        config = ConfigParser()
        with open(conf_fp, 'U') as conf_file:
            config.readfp(conf_file)

        _required_sections = {'main', 'redis', 'postgres', 'smtp', 'ebi',
                              'ipython', 'portal'}
        if not _required_sections.issubset(set(config.sections())):
            missing = _required_sections - set(config.sections())
            raise MissingConfigSection(', '.join(missing))

        self._get_main(config)
        self._get_smtp(config)
        self._get_postgres(config)
        self._get_redis(config)
        self._get_ebi(config)
        self._get_ipython(config)
        self._get_vamps(config)
        self._get_portal(config)

    def _get_main(self, config):
        """Get the configuration of the main section"""
        self.test_environment = config.getboolean('main', 'TEST_ENVIRONMENT')
        install_dir = dirname(dirname(abspath(__file__)))
        default_base_data_dir = join(install_dir, 'qiita_db', 'support_files',
                                     'test_data')
        self.base_data_dir = config.get('main', 'BASE_DATA_DIR') or \
            default_base_data_dir

        self.log_path = config.get('main', 'LOG_PATH')
        self.base_url = config.get('main', 'BASE_URL')

        if not isdir(self.base_data_dir):
            raise ValueError("The BASE_DATA_DIR (%s) folder doesn't exist" %
                             self.base_data_dir)

        self.working_dir = config.get('main', 'WORKING_DIR')
        if not isdir(self.working_dir):
            raise ValueError("The WORKING_DIR (%s) folder doesn't exist" %
                             self.working_dir)
        self.max_upload_size = config.getint('main', 'MAX_UPLOAD_SIZE')
        self.require_approval = config.getboolean('main', 'REQUIRE_APPROVAL')

        self.plugin_launcher = config.get('main', 'PLUGIN_LAUNCHER')
        self.plugin_dir = config.get('main', 'PLUGIN_DIR')
        if not self.plugin_dir:
            self.plugin_dir = join(expanduser('~'), '.qiita_plugins')

        self.valid_upload_extension = [ve.strip() for ve in config.get(
            'main', 'VALID_UPLOAD_EXTENSION').split(',')]
        if (not self.valid_upload_extension or
           self.valid_upload_extension == ['']):
            self.valid_upload_extension = []
            raise ValueError('No files will be allowed to be uploaded.')

        self.certificate_file = config.get('main', 'CERTIFICATE_FILE')
        if not self.certificate_file:
            self.certificate_file = join(install_dir, 'qiita_core',
                                         'support_files', 'server.crt')

        self.cookie_secret = config.get('main', 'COOKIE_SECRET')
        if not self.cookie_secret:
            self.cookie_secret = b64encode(uuid4().bytes + uuid4().bytes)
            warnings.warn("Random cookie secret generated.")

        self.key_file = config.get('main', 'KEY_FILE')
        if not self.key_file:
            self.key_file = join(install_dir, 'qiita_core', 'support_files',
                                 'server.key')

    def _get_postgres(self, config):
        """Get the configuration of the postgres section"""
        self.user = config.get('postgres', 'USER')
        self.admin_user = config.get('postgres', 'ADMIN_USER') or None

        self.password = config.get('postgres', 'PASSWORD')
        if not self.password:
            self.password = None

        self.admin_password = config.get('postgres', 'ADMIN_PASSWORD')
        if not self.admin_password:
            self.admin_password = None

        self.database = config.get('postgres', 'DATABASE')
        self.host = config.get('postgres', 'HOST')
        self.port = config.getint('postgres', 'PORT')

    def _get_redis(self, config):
        """Get the configuration of the redis section"""
        sec_get = partial(config.get, 'redis')
        sec_getint = partial(config.getint, 'redis')

        self.redis_host = sec_get('HOST')
        self.redis_password = sec_get('PASSWORD')
        self.redis_db = sec_getint('DB')
        self.redis_port = sec_getint('PORT')

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

    def _get_ebi(self, config):
        sec_get = partial(config.get, 'ebi')

        self.ebi_seq_xfer_user = sec_get('EBI_SEQ_XFER_USER')
        self.ebi_seq_xfer_pass = sec_get('EBI_SEQ_XFER_PASS')
        self.ebi_seq_xfer_url = sec_get('EBI_SEQ_XFER_URL')
        self.ebi_dropbox_url = sec_get('EBI_DROPBOX_URL')
        self.ebi_center_name = sec_get('EBI_CENTER_NAME')
        self.ebi_organization_prefix = sec_get('EBI_ORGANIZATION_PREFIX')

    def _get_ipython(self, config):
        self.ipython_contexts = config.get('ipython', 'context').split(',')
        self.ipython_default = config.get('ipython', 'default')

    def _get_vamps(self, config):
        self.vamps_user = config.get('vamps', 'USER')
        self.vamps_pass = config.get('vamps', 'PASSWORD')
        self.vamps_url = config.get('vamps', 'URL')

    def _get_portal(self, config):
        self.portal_fp = config.get('portal', 'PORTAL_FP')
        self.portal = config.get('portal', 'PORTAL')
        self.portal_dir = config.get('portal', 'PORTAL_DIR')
        if self.portal_dir:
            if not self.portal_dir.startswith('/'):
                self.portal_dir = "/%s" % self.portal_dir
            if self.portal_dir.endswith('/'):
                self.portal_dir = self.portal_dir[:-1]
        else:
            self.portal_dir = ""
