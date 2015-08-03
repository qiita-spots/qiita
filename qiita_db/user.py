r"""
User object (:mod:`qiita_db.user`)
==================================

.. currentmodule:: qiita_db.user

This modules provides the implementation of the User class. This is used for
handling creation, deletion, and login of users, as well as retrieval of all
studies and analyses that are owned by or shared with the user.

Classes
-------

.. autosummary::
   :toctree: generated/

   User

Examples
--------
TODO
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from re import sub

from qiita_core.exceptions import (IncorrectEmailError, IncorrectPasswordError,
                                   IncompetentQiitaDeveloperError)
from qiita_core.qiita_settings import qiita_config
from .base import QiitaObject
from .sql_connection import TRN
from .util import (create_rand_string, check_table_cols, hash_password,
                   convert_to_id)
from .exceptions import (QiitaDBColumnError, QiitaDBDuplicateError,
                         QiitaDBError)


class User(QiitaObject):
    """
    User object to access to the Qiita user information

    Attributes
    ----------
    email
    level
    info
    user_studies
    shared_studies
    default_analysis
    private_analyses
    shared_analyses
    unread_messages

    Methods
    -------
    change_password
    generate_reset_code
    change_forgot_password
    iter
    messages
    mark_messages
    delete_messages
    """

    _table = "qiita_user"
    # The following columns are considered not part of the user info
    _non_info = {"email", "user_level_id", "password"}

    def _check_id(self, id_):
        r"""Check that the provided ID actually exists in the database

        Parameters
        ----------
        id_ : object
            The ID to test

        Notes
        -----
        This function overwrites the base function, as sql layout doesn't
        follow the same conventions done in the other classes.
        """
        with TRN:
            sql = """SELECT EXISTS(
                        SELECT * FROM qiita.qiita_user WHERE email = %s)"""
            TRN.add(sql, [id_])
            return TRN.execute_fetchlast()

    @classmethod
    def iter(cls):
        """Iterates over all users, sorted by their email addresses

        Returns
        -------
        generator
            Yields a user ID (email) for each user in the database,
            in order of ascending ID
        """
        with TRN:
            sql = """select email from qiita.{}""".format(cls._table)
            TRN.add(sql)
            # Using [-1] to get the results of the last SQL query
            for result in TRN.execute_fetchindex():
                yield result[0]

    @classmethod
    def login(cls, email, password):
        """Logs a user into the system

        Parameters
        ----------
        email : str
            The email of the user
        password: str
            The plaintext password of the user

        Returns
        -------
        User object
            Returns the User object corresponding to the login information
            if correct login information

        Raises
        ------
        IncorrectEmailError
            Email passed is not a valid email
        IncorrectPasswordError
            Password passed is not correct for user
        """
        with TRN:
            # see if user exists
            if not cls.exists(email):
                raise IncorrectEmailError("Email not valid: %s" % email)

            if not validate_password(password):
                raise IncorrectPasswordError("Password not valid!")

            # pull password out of database
            sql = ("SELECT password, user_level_id FROM qiita.{0} WHERE "
                   "email = %s".format(cls._table))
            TRN.add(sql, [email])
            # Using [0] because there is only one row
            info = TRN.execute_fetchindex()[0]

            # verify user email verification
            # MAGIC NUMBER 5 = unverified email
            if int(info[1]) == 5:
                return False

            # verify password
            dbpass = info[0]
            hashed = hash_password(password, dbpass)
            if hashed == dbpass:
                return cls(email)
            else:
                raise IncorrectPasswordError("Password not valid!")

    @classmethod
    def exists(cls, email):
        """Checks if a user exists on the database

        Parameters
        ----------
        email : str
            the email of the user
        """
        with TRN:
            if not validate_email(email):
                raise IncorrectEmailError("Email string not valid: %s" % email)

            sql = """SELECT EXISTS(
                        SELECT * FROM qiita.{0}
                        WHERE email = %s)""".format(cls._table)
            TRN.add(sql, [email])
            return TRN.execute_fetchlast()

    @classmethod
    def create(cls, email, password, info=None):
        """Creates a new user on the database

        Parameters
        ----------
        email : str
            The email of the user - used for log in
        password :
            The plaintext password of the user
        info: dict
            Other information for the user keyed to table column name

        Raises
        ------
        IncorrectPasswordError
            Password string given is not proper format
        IncorrectEmailError
            Email string given is not a valid email
        QiitaDBDuplicateError
            User already exists
        """
        with TRN:
            # validate email and password for new user
            if not validate_email(email):
                raise IncorrectEmailError("Bad email given: %s" % email)
            if not validate_password(password):
                raise IncorrectPasswordError("Bad password given!")

            # make sure user does not already exist
            if cls.exists(email):
                raise QiitaDBDuplicateError("User", "email: %s" % email)

            # make sure non-info columns aren't passed in info dict
            if info:
                if cls._non_info.intersection(info):
                    raise QiitaDBColumnError("non info keys passed: %s" %
                                             cls._non_info.intersection(info))
            else:
                info = {}

            # create email verification code and hashed password to insert
            # add values to info
            info["email"] = email
            info["password"] = hash_password(password)
            info["user_verify_code"] = create_rand_string(20, punct=False)

            # make sure keys in info correspond to columns in table
            check_table_cols(info, cls._table)

            # build info to insert making sure columns and data are in
            # same order for sql insertion
            columns = info.keys()
            values = [info[col] for col in columns]
            # crete user
            sql = "INSERT INTO qiita.{0} ({1}) VALUES ({2})".format(
                cls._table, ','.join(columns), ','.join(['%s'] * len(values)))
            TRN.add(sql, values)

            return cls(email)

    @classmethod
    def verify_code(cls, email, code, code_type):
        """Verify that a code and email match

        Parameters
        ----------
        email : str
            email address of the user
        code : str
            code to verify
        code_type : {'create', 'reset'}
            type of code being verified, whether creating user or reset pass.

        Returns
        -------
        bool

        Raises
        ------
        IncompentQiitaDeveloper
            code_type is not create or reset
        QiitaDBError
            User has no code of the given type
        """
        with TRN:
            if code_type == 'create':
                column = 'user_verify_code'
            elif code_type == 'reset':
                column = 'pass_reset_code'
            else:
                raise IncompetentQiitaDeveloperError(
                    "code_type must be 'create' or 'reset' Uknown type %s"
                    % code_type)
            sql = "SELECT {0} FROM qiita.{1} WHERE email = %s".format(
                column, cls._table)
            TRN.add(sql, [email])
            db_code = TRN.execute_fetchindex()

            if not db_code:
                return False

            db_code = db_code[0][0]
            if db_code is None:
                raise QiitaDBError("No %s code for user %s" %
                                   (column, email))

            correct_code = db_code == code

            if correct_code:
                sql = """UPDATE qiita.{0} SET {1} = NULL
                         WHERE email = %s""".format(cls._table, column)
                TRN.add(sql, [email])

                if code_type == "create":
                    # verify the user
                    level = convert_to_id('user', 'user_level', 'name')
                    sql = """UPDATE qiita.{} SET user_level_id = %s
                             WHERE email = %s""".format(cls._table)
                    TRN.add(sql, [level, email])

                    # create user default sample holders once verified
                    # create one per portal
                    sql = "SELECT portal_type_id FROM qiita.portal_type"
                    TRN.add(sql)

                    an_sql = """INSERT INTO qiita.analysis
                                    (email, name, description, dflt,
                                     analysis_status_id)
                                VALUES (%s, %s, %s, %s, 1)
                                RETURNING analysis_id"""
                    ap_sql = """INSERT INTO qiita.analysis_portal
                                    (analysis_id, portal_type_id)
                                VALUES (%s, %s)"""

                    for portal_id in TRN.execute_fetchflatten():
                        placeholder = "{%s:0:0}" % TRN.index
                        args = [email, '%s-dflt-%d' % (email, portal_id),
                                'dflt', True]
                        TRN.add(an_sql, args)
                        TRN.add(ap_sql, [placeholder, portal_id])

                    TRN.execute()

            return correct_code

    # ---properties---
    @property
    def email(self):
        """The email of the user"""
        return self._id

    @property
    def level(self):
        """The level of privileges of the user"""
        with TRN:
            sql = """SELECT ul.name
                     FROM qiita.user_level ul
                        JOIN qiita.{0} u
                            ON ul.user_level_id = u.user_level_id
                     WHERE u.email = %s""".format(self._table)
            TRN.add(sql, [self._id])
            return TRN.execute_fetchlast()

    @property
    def info(self):
        """Dict with any other information attached to the user"""
        with TRN:
            sql = "SELECT * from qiita.{0} WHERE email = %s".format(
                self._table)
            # Need direct typecast from psycopg2 dict to standard dict
            TRN.add(sql, [self._id])
            # [0] retrieves the first row (the only one present)
            info = dict(TRN.execute_fetchindex()[0])
            # Remove non-info columns
            for col in self._non_info:
                info.pop(col)
            return info

    @info.setter
    def info(self, info):
        """Updates the information attached to the user

        Parameters
        ----------
        info : dict
        """
        with TRN:
            # make sure non-info columns aren't passed in info dict
            if self._non_info.intersection(info):
                raise QiitaDBColumnError("non info keys passed!")

            # make sure keys in info correspond to columns in table
            check_table_cols(info, self._table)

            # build sql command and data to update
            sql_insert = []
            data = []
            # items used for py3 compatability
            for key, val in info.items():
                sql_insert.append("{0} = %s".format(key))
                data.append(val)
            data.append(self._id)

            sql = ("UPDATE qiita.{0} SET {1} WHERE "
                   "email = %s".format(self._table, ','.join(sql_insert)))
            TRN.add(sql, data)
            TRN.execute()

    @property
    def default_analysis(self):
        with TRN:
            sql = """SELECT analysis_id
                     FROM qiita.analysis
                        JOIN qiita.analysis_portal USING (analysis_id)
                        JOIN qiita.portal_type USING (portal_type_id)
                     WHERE email = %s AND dflt = true AND portal = %s"""
            TRN.add(sql, [self._id, qiita_config.portal])
            return TRN.execute_fetchlast()

    @property
    def user_studies(self):
        """Returns a list of study ids owned by the user"""
        with TRN:
            sql = """SELECT study_id
                     FROM qiita.study
                        JOIN qiita.study_portal USING (study_id)
                        JOIN qiita.portal_type USING (portal_type_id)
                     WHERE email = %s AND portal = %s"""
            TRN.add(sql, [self._id, qiita_config.portal])
            return set(TRN.execute_fetchflatten())

    @property
    def shared_studies(self):
        """Returns a list of study ids shared with the user"""
        with TRN:
            sql = """SELECT study_id
                     FROM qiita.study_users
                        JOIN qiita.study_portal USING (study_id)
                        JOIN qiita.portal_type USING (portal_type_id)
                     WHERE email = %s and portal = %s"""
            TRN.add(sql, [self._id, qiita_config.portal])
            return set(TRN.execute_fetchflatten())

    @property
    def private_analyses(self):
        """Returns a list of private analysis ids owned by the user"""
        with TRN:
            sql = """SELECT analysis_id FROM qiita.analysis
                        JOIN qiita.analysis_portal USING (analysis_id)
                        JOIN qiita.portal_type USING (portal_type_id)
                     WHERE email = %s AND dflt = false AND portal = %s"""
            TRN.add(sql, [self._id, qiita_config.portal])
            return set(TRN.execute_fetchflatten())

    @property
    def shared_analyses(self):
        """Returns a list of analysis ids shared with the user"""
        with TRN:
            sql = """SELECT analysis_id FROM qiita.analysis_users
                        JOIN qiita.analysis_portal USING (analysis_id)
                        JOIN qiita.portal_type USING (portal_type_id)
                     WHERE email = %s AND portal = %s"""
            TRN.add(sql, [self._id, qiita_config.portal])
            return set(TRN.execute_fetchflatten())

    @property
    def unread_messages(self):
        """Returns all unread messages for a user"""
        with TRN:
            sql = """SELECT message_id, message, message_time, read
                     FROM qiita.message_user
                     JOIN qiita.message USING (message_id)
                     WHERE email = %s AND read = FALSE
                     ORDER BY message_time DESC"""
            TRN.add(sql, [self._id])
            return TRN.execute_fetchindex()

    # ------- methods ---------
    def change_password(self, oldpass, newpass):
        """Changes the password from oldpass to newpass

        Parameters
        ----------
        oldpass : str
            User's old password
        newpass : str
            User's new password

        Returns
        -------
        bool
            password changed or not
        """
        with TRN:
            sql = "SELECT password FROM qiita.{0} WHERE email = %s".format(
                self._table)
            TRN.add(sql, [self._id])
            dbpass = TRN.execute_fetchlast()
            if dbpass == hash_password(oldpass, dbpass):
                self._change_pass(newpass)
                return True
            return False

    def generate_reset_code(self):
        """Generates a password reset code for user"""
        with TRN:
            reset_code = create_rand_string(20, punct=False)
            sql = """UPDATE qiita.{0}
                     SET pass_reset_code = %s, pass_reset_timestamp = NOW()
                     WHERE email = %s""".format(self._table)
            TRN.add(sql, [reset_code, self._id])
            TRN.execute()

    def change_forgot_password(self, code, newpass):
        """Changes the password if the code is valid

        Parameters
        ----------
        code : str
            User's forgotten password ID code
        newpass : str
            User's new password

        Returns
        -------
        bool
            password changed or not
        """
        with TRN:
            if self.verify_code(self._id, code, "reset"):
                self._change_pass(newpass)
                return True
            return False

    def _change_pass(self, newpass):
        with TRN:
            if not validate_password(newpass):
                raise IncorrectPasswordError("Bad password given!")

            sql = """UPDATE qiita.{0}
                     SET password=%s, pass_reset_code = NULL
                     WHERE email = %s""".format(self._table)
            TRN.add(sql, [hash_password(newpass), self._id])
            TRN.execute()

    def messages(self, count=None):
        """Return messages in user's queue

        Parameters
        ----------
        count : int, optional
            Number of messages to return, starting with newest. Default all

        Returns
        -------
        list of tuples
            Messages in the queue, in the form
            [(msg_id, msg, timestamp, read), ...]
        """
        with TRN:
            sql_info = [self._id]
            sql = """SELECT message_id, message, message_time, read
                     FROM qiita.message_user
                     JOIN qiita.message USING (message_id)
                     WHERE email = %s ORDER BY message_time DESC"""
            if count is not None:
                sql += " LIMIT %s"
                sql_info.append(count)
            TRN.add(sql, sql_info)
            return TRN.execute_fetchindex()

    def mark_messages(self, messages, read=True):
        """Mark given messages as read/unread

        Parameters
        ----------
        messages : list of ints
            Message IDs to mark as read/unread
        read : bool, optional
            Marks as read if True, unread if False. Default True
        """
        with TRN:
            sql = """UPDATE qiita.message_user
                     SET read = %s
                     WHERE message_id IN %s AND email = %s"""
            TRN.add(sql, [read, tuple(messages), self._id])
            return TRN.execute_fetchindex()

    def delete_messages(self, messages):
        """Delete given messages for the user

        Parameters
        ----------
        messages : list of ints
            Message IDs to delete
        """
        with TRN:
            # remove message from user
            sql = """DELETE FROM qiita.message_user
                     WHERE message_id IN %s AND email = %s"""
            TRN.add(sql, [tuple(messages), self._id])
            # Remove any messages that no longer are attached to a user
            sql = """DELETE FROM qiita.message WHERE message_id NOT IN
                     (SELECT DISTINCT message_id FROM qiita.message_user)"""
            TRN.add(sql)
            TRN.execute()


def validate_email(email):
    """Validates an email

    Notes
    -----
    An email address is of the form local-part@domain_part
    For our purposes:

    - No quoted strings are allowed
    - No unicode strings are allowed
    - There must be exactly one @ symbol
    - Neither local-part nor domain-part can be blank
    - The local-part cannot start or end with a dot
    - The local-part must be composed of the following characters:
      a-zA-Z0-9#_~!$&'()*+,;=:.-
    - The domain-part must be a valid hostname, composed of:
      a-zA-Z0-9.

    Parameters
    ----------
    email: str
        email to validate

    Returns
    -------
    bool
        Whether or not the email is valid
    """
    # Do not accept email addresses that have unicode characters
    try:
        email.encode('ascii')
    except UnicodeError:
        return False

    # we are not allowing quoted strings in the email address
    if '"' in email:
        return False

    # Must have exactly 1 @ symbol
    if email.count('@') != 1:
        return False

    local_part, domain_part = email.split('@')

    # Neither part can be blank
    if not (local_part and domain_part):
        return False

    # The local part cannot begin or end with a dot
    if local_part.startswith('.') or local_part.endswith('.'):
        return False

    # The domain part cannot begin or end with a hyphen
    if domain_part.startswith('-') or domain_part.endswith('-'):
        return False

    # This is the full set of allowable characters for the local part.
    local_valid_chars = "[a-zA-Z0-9#_~!$&'()*+,;=:.-]"
    if len(sub(local_valid_chars, '', local_part)):
        return False

    domain_valid_chars = "[a-zA-Z0-9.-]"
    if len(sub(domain_valid_chars, '', domain_part)):
        return False

    return True


def validate_password(password):
    """Validates a password

    Notes
    -----
    The valid characters for a password are:

        * lowercase letters
        * uppercase letters
        * numbers
        * special characters (e.g., !@#$%^&*()-_=+`~[]{}|;:'",<.>/?) with the
            exception of a backslash
        * must be ASCII
        * no spaces
        * must be at least 8 characters

    Parameters
    ----------
    password: str
        Password to validate

    Returns
    -------
    bool
        Whether or not the password is valid

    References
    -----
    http://stackoverflow.com/q/196345
    """
    if len(password) < 8:
        return False

    if "\\" in password or " " in password:
        return False

    try:
        password.encode('ascii')
    except UnicodeError:
        return False

    return True
