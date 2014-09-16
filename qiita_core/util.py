# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from smtplib import SMTP, SMTP_SSL, SMTPException
from future import standard_library
with standard_library.hooks():
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

from qiita_core.qiita_settings import qiita_config
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.environment_manager import (LAYOUT_FP, INITIALIZE_FP,
                                          POPULATE_FP)


def send_email(to, subject, body):
    # create email
    msg = MIMEMultipart()
    msg['From'] = qiita_config.smtp_email
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # connect to smtp server, using ssl if needed
    if qiita_config.smtp_ssl:
        smtp = SMTP_SSL()
    else:
        smtp = SMTP()
    smtp.set_debuglevel(False)
    smtp.connect(qiita_config.smtp_host, qiita_config.smtp_port)
    # try tls, if not available on server just ignore error
    try:
        smtp.starttls()
    except SMTPException:
        pass
    smtp.ehlo_or_helo_if_needed()

    if qiita_config.smtp_user:
        smtp.login(qiita_config.smtp_user, qiita_config.smtp_password)

    # send email
    try:
        smtp.sendmail(qiita_config.smtp_email, to, msg.as_string())
    except Exception:
        raise RuntimeError("Can't send email!")
    finally:
        smtp.close()


def reset_test_database(wrapped_fn, load_ontos=False):
    """Decorator that drops the qiita schema, rebuilds and repopulates the
    schema with test data, then executes wrapped_fn
    """
    conn_handler = SQLConnectionHandler()

    def decorated_wrapped_fn(*args, **kwargs):
        # Drop the schema
        conn_handler.execute("DROP SCHEMA qiita CASCADE")
        # Create the schema
        with open(LAYOUT_FP, 'U') as f:
            conn_handler.execute(f.read())
        # Initialize the database
        with open(INITIALIZE_FP, 'U') as f:
            conn_handler.execute(f.read())
        # Populate the database
        with open(POPULATE_FP, 'U') as f:
            conn_handler.execute(f.read())

        # Execute the wrapped function
        return wrapped_fn(*args, **kwargs)
    return decorated_wrapped_fn


def qiita_test_checker():
    """Decorator that allows the execution of all methods in a test class only
    and only if Qiita is set up to work in a test environment.

    Raises
    ------
    RuntimeError
        If Qiita is set up to work in a production environment
    """
    def class_modifier(cls):
        # First, we check that we are not in a production environment
        conn_handler = SQLConnectionHandler()
        # It is possible that we are connecting to a production database
        test_db = conn_handler.execute_fetchone("SELECT test FROM settings")[0]
        # Or the loaded configuration file belongs to a production environment
        # or the test database is not qiita_test
        if not qiita_config.test_environment or not test_db \
                or qiita_config.database != 'qiita_test':
            raise RuntimeError("Working in a production environment. Not "
                               "executing the tests to keep the production "
                               "database safe.")

        # Now, we decorate the setup and teardown functions
        class DecoratedClass(cls):
            def setUp(self):
                super(DecoratedClass, self).setUp()
                self.conn_handler = SQLConnectionHandler()

            @reset_test_database
            def tearDown(self):
                super(DecoratedClass, self).tearDown()
                del self.conn_handler

        return DecoratedClass
    return class_modifier
