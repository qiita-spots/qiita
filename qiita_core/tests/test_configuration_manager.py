# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from os import environ, close, remove
from tempfile import mkstemp
from future import standard_library
from functools import partial
import warnings

from qiita_core.exceptions import MissingConfigSection
from qiita_core.configuration_manager import ConfigurationManager

with standard_library.hooks():
    from configparser import ConfigParser


class ConfigurationManagerTests(TestCase):
    def setUp(self):
        self.old_conf_fp = environ.get('QIITA_CONFIG_FP')
        fd, self.conf_fp = mkstemp(suffix='.txt')
        close(fd)
        with open(self.conf_fp, 'w') as f:
            f.write(CONF)
        environ['QIITA_CONFIG_FP'] = self.conf_fp

        self.conf = ConfigParser()
        with open(self.conf_fp, 'U') as f:
            self.conf.readfp(f)

    def tearDown(self):
        if self.old_conf_fp is not None:
            environ['QIITA_CONFIG_FP'] = self.old_conf_fp
        else:
            del environ['QIITA_CONFIG_FP']
        remove(self.conf_fp)

    def test_init(self):
        obs = ConfigurationManager()
        # Main section
        self.assertEqual(obs.conf_fp, self.conf_fp)
        self.assertTrue(obs.test_environment)
        self.assertEqual(obs.base_data_dir, "/tmp/")
        self.assertEqual(obs.log_dir, "/tmp/")
        self.assertEqual(obs.base_url, "https://localhost")
        self.assertEqual(obs.max_upload_size, 100)
        self.assertTrue(obs.require_approval)
        self.assertEqual(obs.qiita_env, "source activate qiita")
        self.assertEqual(obs.private_launcher, 'qiita-private-launcher')
        self.assertEqual(obs.plugin_launcher, "qiita-plugin-launcher")
        self.assertEqual(obs.plugin_dir, "/tmp/")
        self.assertEqual(
            obs.valid_upload_extension,
            ["fastq", "fastq.gz", "txt", "tsv", "sff", "fna", "qual"])
        self.assertEqual(obs.certificate_file, "/tmp/server.cert")
        self.assertEqual(obs.cookie_secret, "SECRET")
        self.assertEqual(obs.key_file, "/tmp/server.key")

        # Postgres section
        self.assertEqual(obs.user, "postgres")
        self.assertEqual(obs.admin_user, "postgres")
        self.assertEqual(obs.password, "andanotherpwd")
        self.assertEqual(obs.admin_password, "thishastobesecure")
        self.assertEqual(obs.database, "qiita_test")
        self.assertEqual(obs.host, "localhost")
        self.assertEqual(obs.port, 5432)

        # Redis section
        self.assertEqual(obs.redis_host, "localhost")
        self.assertEqual(obs.redis_password, "anotherpassword")
        self.assertEqual(obs.redis_db, 13)
        self.assertEqual(obs.redis_port, 6379)

        # SMTP section
        self.assertEqual(obs.smtp_host, "localhost")
        self.assertEqual(obs.smtp_port, 25)
        self.assertEqual(obs.smtp_user, "qiita")
        self.assertEqual(obs.smtp_password, "supersecurepassword")
        self.assertFalse(obs.smtp_ssl)
        self.assertEqual(obs.smtp_email, "example@domain.com")

        # EBI section
        self.assertEqual(obs.ebi_seq_xfer_user, "Webin-41528")
        self.assertEqual(obs.ebi_seq_xfer_pass, "passwordforebi")
        self.assertEqual(obs.ebi_seq_xfer_url, "webin.ebi.ac.uk")
        self.assertEqual(
            obs.ebi_dropbox_url,
            "https://www-test.ebi.ac.uk/ena/submit/drop-box/submit/")
        self.assertEqual(obs.ebi_center_name, "qiita-test")
        self.assertEqual(obs.ebi_organization_prefix, "example_organization")

        # VAMPS section
        self.assertEqual(obs.vamps_user, "user")
        self.assertEqual(obs.vamps_pass, "password")
        self.assertEqual(obs.vamps_url,
                         "https://vamps.mbl.edu/mobe_workshop/getfile.php")

        # Portal section
        self.assertEqual(obs.portal_fp, "/tmp/portal.cfg")
        self.assertEqual(obs.portal, "QIITA")
        self.assertEqual(obs.portal_dir, "/portal")

        # iframe section
        self.assertEqual(obs.iframe_qiimp, "https://localhost:8898/")

    def test_init_error(self):
        with open(self.conf_fp, 'w') as f:
            f.write("\n")

        with self.assertRaises(MissingConfigSection):
            ConfigurationManager()

    def test_get_main(self):
        obs = ConfigurationManager()

        conf_setter = partial(self.conf.set, 'main')
        conf_setter('COOKIE_SECRET', '')
        conf_setter('BASE_DATA_DIR', '')
        conf_setter('PLUGIN_DIR', '')
        conf_setter('CERTIFICATE_FILE', '')
        conf_setter('KEY_FILE', '')
        conf_setter('QIITA_ENV', '')

        # Warning raised if No files will be allowed to be uploaded
        # Warning raised if no cookie_secret
        with warnings.catch_warnings(record=True) as warns:
            obs._get_main(self.conf)

            obs_warns = [str(w.message) for w in warns]
            exp_warns = ['Random cookie secret generated.']
            self.assertItemsEqual(obs_warns, exp_warns)

        self.assertNotEqual(obs.cookie_secret, "SECRET")
        # Test default base_data_dir
        self.assertTrue(
            obs.base_data_dir.endswith("/qiita_db/support_files/test_data"))
        # Test default plugin dir
        self.assertTrue(obs.plugin_dir.endswith("/.qiita_plugins"))
        # Default certificate_file
        self.assertTrue(
            obs.certificate_file.endswith(
                "/qiita_core/support_files/server.crt"))
        # Default key_file
        self.assertTrue(
            obs.key_file.endswith("/qiita_core/support_files/server.key"))

        # BASE_DATA_DIR does not exist
        conf_setter('BASE_DATA_DIR', '/surprised/if/this/dir/exists')
        with self.assertRaises(ValueError):
            obs._get_main(self.conf)

        # WORKING_DIR does not exist
        conf_setter('BASE_DATA_DIR', '/tmp')
        conf_setter('WORKING_DIR', '/surprised/if/this/dir/exists')
        with self.assertRaises(ValueError):
            obs._get_main(self.conf)

        # PLUGIN_DIR does not exist
        conf_setter('WORKING_DIR', '/tmp')
        conf_setter('PLUGIN_DIR', '/surprised/if/this/dir/exists')
        with self.assertRaises(ValueError):
            obs._get_main(self.conf)

        # No files can be uploaded
        conf_setter('PLUGIN_DIR', '/tmp')
        conf_setter('VALID_UPLOAD_EXTENSION', '')
        with self.assertRaises(ValueError):
            obs._get_main(self.conf)

        self.assertEqual(obs.qiita_env, "")

    def test_get_postgres(self):
        obs = ConfigurationManager()

        conf_setter = partial(self.conf.set, 'postgres')
        conf_setter('PASSWORD', '')
        conf_setter('ADMIN_PASSWORD', '')
        obs._get_postgres(self.conf)
        self.assertIsNone(obs.password)
        self.assertIsNone(obs.admin_password)

    def test_get_portal(self):
        obs = ConfigurationManager()
        conf_setter = partial(self.conf.set, 'portal')
        # Default portal_dir
        conf_setter('PORTAL_DIR', '')
        obs._get_portal(self.conf)
        self.assertEqual(obs.portal_dir, "")
        # Portal dir does not start with /
        conf_setter('PORTAL_DIR', 'gold_portal')
        obs._get_portal(self.conf)
        self.assertEqual(obs.portal_dir, "/gold_portal")
        # Portal dir endswith /
        conf_setter('PORTAL_DIR', '/gold_portal/')
        obs._get_portal(self.conf)
        self.assertEqual(obs.portal_dir, "/gold_portal")


CONF = """
# ------------------------------ Main settings --------------------------------
[main]
# Change to FALSE in a production system
TEST_ENVIRONMENT = TRUE

# Absolute path to write log file to. If not given, no log file will be created
LOG_DIR = /tmp/

# Whether studies require admin approval to be made available
REQUIRE_APPROVAL = True

# Base URL: DO NOT ADD TRAILING SLASH
BASE_URL = https://localhost

# Download path files
UPLOAD_DATA_DIR = /tmp/

# Working directory path
WORKING_DIR = /tmp/

# Maximum upload size (in Gb)
MAX_UPLOAD_SIZE = 100

# Path to the base directory where the data files are going to be stored
BASE_DATA_DIR = /tmp/

# Valid upload extension, comma separated. Empty for no uploads
VALID_UPLOAD_EXTENSION = fastq,fastq.gz,txt,tsv,sff,fna,qual

# The script used to start the qiita environment, if any
# used to spawn private CLI to a cluster
QIITA_ENV = source activate qiita

# Script used for launching private Qiita tasks
PRIVATE_LAUNCHER = qiita-private-launcher

# Script used for launching plugins
PLUGIN_LAUNCHER = qiita-plugin-launcher

# Plugins configuration directory
PLUGIN_DIR = /tmp/

# Webserver certificate file paths
CERTIFICATE_FILE = /tmp/server.cert
KEY_FILE = /tmp/server.key

# The value used to secure cookies used for user sessions. A suitable value can
# be generated with:
#
# python -c "from base64 import b64encode;\
#   from uuid import uuid4;\
#   print b64encode(uuid4().bytes + uuid4().bytes)"
COOKIE_SECRET = SECRET

# ----------------------------- SMTP settings -----------------------------
[smtp]
# The hostname to connect to
# Google: smtp.google.com
HOST = localhost

# The port to connect to the database
# Google: 587
PORT = 25

# SSL needed (True or False)
# Google: True
SSL = False

# The user name to connect with
USER = qiita

# The user password to connect with
PASSWORD = supersecurepassword

# The email to have messages sent from
EMAIL = example@domain.com

# ----------------------------- Redis settings --------------------------------
[redis]
HOST = localhost
PORT = 6379
PASSWORD = anotherpassword
# The redis database you will use, redis has a max of 16.
# Qiita should have its own database
DB = 13

# ----------------------------- Postgres settings -----------------------------
[postgres]
# The user name to connect to the database
USER = postgres

# The administrator user, which can be used to create/drop environments
ADMIN_USER = postgres

# The database to connect to
DATABASE = qiita_test

# The host where the database lives on
HOST = localhost

# The port to connect to the database
PORT = 5432

# The password to use to connect to the database
PASSWORD = andanotherpwd

# The postgres password for the admin_user
ADMIN_PASSWORD = thishastobesecure

# ----------------------------- EBI settings -----------------------------
[ebi]
# The user to use when submitting to EBI
EBI_SEQ_XFER_USER = Webin-41528

# Password for the above user
EBI_SEQ_XFER_PASS = passwordforebi

# URL of EBI's FASP site
EBI_SEQ_XFER_URL = webin.ebi.ac.uk

# URL of EBI's HTTPS dropbox
EBI_DROPBOX_URL = https://www-test.ebi.ac.uk/ena/submit/drop-box/submit/

# The name of the sequencing center to use when doing EBI submissions
EBI_CENTER_NAME = qiita-test

# This string (with an underscore) will be prefixed to your EBI submission and
# study aliases
EBI_ORGANIZATION_PREFIX = example_organization

# ----------------------------- VAMPS settings -----------------------------
[vamps]
# general info to submit to vamps
USER = user
PASSWORD = password
URL = https://vamps.mbl.edu/mobe_workshop/getfile.php

# ----------------------------- Portal settings -----------------------------
[portal]

# Portal the site is working under
PORTAL = QIITA

# Portal subdirectory
PORTAL_DIR = /portal

# Full path to portal styling config file
PORTAL_FP = /tmp/portal.cfg

# ----------------------------- iframes settings ---------------------------
[iframe]
QIIMP = https://localhost:8898/
"""

if __name__ == '__main__':
    main()
