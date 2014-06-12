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
from re import match

from .base import QiitaObject
from .exceptions import QiitaDBNotImplementedError
from .sql_connection import SQLConnectionHandler

from qiita_core.exceptions import IncorrectEmailError, IncorrectPasswordError
from .exceptions import QiitaDBDuplicateError, QiitaDBColumnError
from .util import hash_password
from .sql_connection import SQLConnectionHandler
from .util import create_rand_string, check_table_cols
from .study import Study
from .analysis import Analysis


class User(QiitaObject):
    """
    User object to access to the Qiita user information

    Attributes
    ----------
    email
    level
    info
    private_studies
    shared_studies
    private_analyses
    shared_analyses

    Methods
    -------
    add_shared_study
    remove_shared_study
    add_private_analysis
    remove_private_analysis
    add_shared_analysis
    remove_shared_analysis
    """

    _table = "qiita_user"
    # The following columns are considered not part of the user info
    _non_info = {"email", "user_level_id", "password", "user_verify_code",
                 "pass_reset_code", "pass_reset_timestamp"}

    def _check_id(self, id_, conn_handler=None):
        r"""Check that the provided ID actually exists in the database

        Parameters
        ----------
        id_ : object
            The ID to test
        conn_handler : SQLConnectionHandler
            The connection handler object connected to the DB

        Notes
        -----
        This function overwrites the base function, as sql layout doesn't
        follow the same conventions done in the other classes.
        """
        self._check_subclass()

        conn_handler = (conn_handler if conn_handler is not None
                        else SQLConnectionHandler())
        return conn_handler.execute_fetchone(
            "SELECT EXISTS(SELECT * FROM qiita.qiita_user WHERE "
            "email = %s)", (id_, ))[0]

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
        # see if user exists
        if not cls.exists(email):
            raise IncorrectEmailError("Email not valid: %s" % email)

        if not validate_password(password):
            raise IncorrectPasswordError("Password not valid!")

        # pull password out of database
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT password FROM qiita.{0} WHERE "
               "email = %s".format(cls._table))
        dbpass = conn_handler.execute_fetchone(sql, (email, ))[0]

        # verify password
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
        if not validate_email(email):
            raise IncorrectEmailError("Email string not valid: %s" % email)
        conn_handler = SQLConnectionHandler()

        return conn_handler.execute_fetchone(
            "SELECT EXISTS(SELECT * FROM qiita.{0} WHERE "
            "email = %s)".format(cls._table), (email, ))[0]

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
        # validate email and password for new user
        if not validate_email(email):
            raise IncorrectEmailError("Bad email given: %s" % email)
        if not validate_password(password):
            raise IncorrectPasswordError("Bad password given!")

        # make sure user does not already exist
        if cls.exists(email):
            raise QiitaDBDuplicateError("User %s already exists" % email)

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
        conn_handler = SQLConnectionHandler()
        check_table_cols(conn_handler, info, cls._table)

        # build info to insert making sure columns and data are in same order
        # for sql insertion
        columns = info.keys()
        values = [info[col] for col in columns]

        sql = ("INSERT INTO qiita.%s (%s) VALUES (%s)" %
               (cls._table, ','.join(columns), ','.join(['%s'] * len(values))))
        conn_handler.execute(sql, values)
        return cls(email)

    # ---properties---

    @property
    def email(self):
        """The email of the user"""
        return self._id

    @property
    def level(self):
        """The level of privileges of the user"""
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT name from qiita.user_level WHERE user_level_id = "
               "(SELECT user_level_id from qiita.{0} WHERE "
               "email = %s)".format(self._table))
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @property
    def info(self):
        """Dict with any other information attached to the user"""
        conn_handler = SQLConnectionHandler()
        sql = "SELECT * from qiita.{0} WHERE email = %s".format(self._table)
        # Need direct typecast from psycopg2 dict to standard dict
        info = dict(conn_handler.execute_fetchone(sql, (self._id, )))
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
        # make sure non-info columns aren't passed in info dict
        if self._non_info.intersection(info):
            raise QiitaDBColumnError("non info keys passed!")

        # make sure keys in info correspond to columns in table
        conn_handler = SQLConnectionHandler()
        check_table_cols(conn_handler, info, self._table)

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
        conn_handler.execute(sql, data)

    @property
    def private_studies(self):
        """Returns a list of private study ids owned by the user"""
        sql = ("SELECT study_id FROM qiita.study WHERE "
               "email = %s".format(self._table))
        conn_handler = SQLConnectionHandler()
        study_ids = conn_handler.execute_fetchall(sql, (self._id, ))
        return [s[0] for s in study_ids]

    @property
    def shared_studies(self):
        """Returns a list of study ids shared with the user"""
        sql = ("SELECT study_id FROM qiita.study_users WHERE "
               "email = %s".format(self._table))
        conn_handler = SQLConnectionHandler()
        study_ids = conn_handler.execute_fetchall(sql, (self._id, ))
        return [s[0] for s in study_ids]

    @property
    def private_analyses(self):
        """Returns a list of private analysis ids owned by the user"""
        sql = ("Select analysis_id from qiita.analysis WHERE email = %s AND "
               "analysis_status_id <> 6")
        conn_handler = SQLConnectionHandler()
        analysis_ids = conn_handler.execute_fetchall(sql, (self._id, ))
        return [a[0] for a in analysis_ids]

    @property
    def shared_analyses(self):
        """Returns a list of analysis ids shared with the user"""
        sql = ("SELECT analysis_id FROM qiita.analysis_users WHERE "
               "email = %s".format(self._table))
        conn_handler = SQLConnectionHandler()
        analysis_ids = conn_handler.execute_fetchall(sql, (self._id, ))
        return [a[0] for a in analysis_ids]


def validate_email(email):
    """Makes sure email string has one @ and a period after the @

    Parameters
    ----------
    email: str
        email to validate

    Returns
    -------
    bool
        Whether or not the email is valid
    """
    return True if match(r"[^@]+@[^@]+\.[^@]+", email) else False


def validate_password(password):
    """Validates a password is only ascii letters, numbers, or characters and
    at least 8 characters

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
    http://stackoverflow.com/questions/2990654/how-to-test-a-regex-password-in-python
    """
    return True if match(r'[A-Za-z0-9@#$%^&+=]{8,}', password) else False
