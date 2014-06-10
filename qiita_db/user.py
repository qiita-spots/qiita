#!/usr/bin/env python
from __future__ import division

"""
Objects for dealing with Qiita users

This modules provides the implementation of the User class.

Classes
-------
- `User` -- A Qiita user class
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from .base import QiitaObject

from ..qiita_core.util import hash_pw
from .exceptions import (QiitaDBNotImplementedError,
                         IncompetentQiitaDeveloperError,
                         QiitaDBDuplicateError, QiitaDBColumnError)
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
    add_shared_study(study)
        Adds a new shared study to the user

    remove_shared_study(study)
        Removes a shared study from the user

    add_private_analysis(analysis)
        Adds a new private analysis to the user

    remove_private_analysis(analysis)
        Removes a private analysis from the user

    add_shared_analysis(analysis)
        Adds a new shared analysis to the user

    remove_shared_analysis(analysis)
        Removes a shared analysis from the user
    """

    _table = "qiita_user"
    _non_info = {"email", "user_level_id", "password", "user_verify_code",
                 "pass_reset_code", "pass_reset_timestamp"}

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
        User object or None
            Returns the User object corresponding to the login information
            or None if incorrect login information
        """
        # see if user exists
        if not cls.exists(email):
            return None

        # pull password out of database
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT password FROM qiita.{0} WHERE "
               "email = %s".format(cls._table))
        dbpass = conn_handler.execute_fetchone(sql, (email, ))[0]

        # verify password
        hashed = hash_pw(password, dbpass)
        return cls(email) if hashed == dbpass else None

    @classmethod
    def exists(cls, email):
        """Checks if a user exists on the database

        Parameters
        ----------
        email : str
            the email of the user
        """
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
            other information for the user keyed to table column name
        """
        if email == "":
            raise IncompetentQiitaDeveloperError("Blank username given!")
        if password == "":
            raise IncompetentQiitaDeveloperError("Blank password given!")

        # make sure user does not already exist
        if cls.exists(email):
            raise QiitaDBDuplicateError("User %s already exists" % email)

        # make sure non-info columns arent passed in info dict
        for key in info:
            if key in cls._non_info:
                raise QiitaDBColumnError("%s should not be passed in info!" %
                                         key)

        # create email verification code and hashed password to insert
        # add values to info
        info["email"] = email
        info["password"] = hash_pw(password)
        info["verify_code"] = create_rand_string(20, punct=False)

        # make sure keys in info correspond to columns in table
        conn_handler = SQLConnectionHandler()
        check_table_cols(conn_handler, info, cls._table)

        # build info to insert making sure columns and data are in same order
        # for sql insertion
        columns = info.keys()
        values = (info[col] for col in columns)

        sql = ("INSERT INTO qiita.%s (%s) VALUES (%s)" %
               (cls._table, ','.join(columns), ','.join(['%s'] * len(values))))
        conn_handler.execute(sql, values)

    @classmethod
    def delete(cls, id_):
        """Deletes the user `id` from the database

        Parameters
        ----------
        id_ :
            The object identifier
        """
        raise QiitaDBNotImplementedError()

    def _check_id(self, id_, conn_handler=None):
        r"""Check that the provided ID actually exists on the database

        Parameters
        ----------
        id_ : object
            The ID to test
            The connection handler object connected to the DB

        Notes
        -----
        This function overwrites the base function, as sql layout doesn't
        follow the same conventions done in the other tables.
        """
        self._check_subclass()

        conn_handler = (conn_handler if conn_handler is not None
                        else SQLConnectionHandler())
        print ("SELECT EXISTS(SELECT * FROM qiita.qiita_user WHERE "
               "email = %s)" % id_)
        return conn_handler.execute_fetchone(
            "SELECT EXISTS(SELECT * FROM qiita.qiita_user WHERE "
            "email = %s)", (id_, ))[0]

    # ---properties---

    @property
    def email(self):
        """The email of the user"""
        return self._id

    @property
    def level(self):
        """The level of privileges of the user"""
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT user_level_id from qiita.{0} WHERE "
               "email = %s".format(self._table))
        return conn_handler.execute_fetchone(sql, (self._id, ))[0]

    @level.setter
    def level(self, level):
        """ Sets the level of privileges of the user

        Parameters
        ----------
        level : int
            The new level of the user

        Notes
        -----
        the ints correspond to {1: 'admin', 2: 'dev', 3: 'superuser',
        4: 'user', 5: 'unverified', 6: 'guest'}
        """
        conn_handler = SQLConnectionHandler()
        sql = ("UPDATE qiita.qiita_user SET user_level_id = %s WHERE "
               "email = %s".format(self._table))
        conn_handler.execute(sql, (level, self._id))

    @property
    def info(self):
        """Dict with any other information attached to the user"""
        conn_handler = SQLConnectionHandler()
        sql = "SELECT * from qiita.{0} WHERE email = %s".format(self._table)
        # Need direct typecast from psycopg2 dict to standard dict
        info = dict(conn_handler.execute_fetchall(sql, (self._id, )))
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
        for key in info:
            if key in self._non_info:
                raise QiitaDBColumnError("%s should not be passed in info!" %
                                         key)

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
        """Returns a list of private studies owned by the user"""
        sql = ("SELECT study_id FROM qiita.study WHERE study_status_id = 3 AND"
               " email = %s".format(self._table))
        conn_handler = SQLConnectionHandler()
        studies = conn_handler.execute_fetchall(sql, (self._id, ))
        return [Study(s[0]) for s in studies]

    @property
    def shared_studies(self):
        """Returns a list of studies shared with the user"""
        sql = ("SELECT study_id FROM qiita.study_users WHERE "
               "email = %s".format(self._table))
        conn_handler = SQLConnectionHandler()
        studies = conn_handler.execute_fetchall(sql, (self._id, ))
        return [Study(s[0]) for s in studies]

    @property
    def private_analyses(self):
        """Returns a list of private analyses owned by the user"""
        sql = ("Select analysis_id from qiita.analysis WHERE email = %s AND "
               "analysis_status_id <> 6")
        conn_handler = SQLConnectionHandler()
        analyses = conn_handler.execute_fetchall(sql, (self._id, ))
        return [Analysis(a[0]) for a in analyses]

    @property
    def shared_analyses(self):
        """Returns a list of analyses shared with the user"""
        sql = ("SELECT analysis_id FROM qiita.analysis_users WHERE "
               "email = %s".format(self._table))
        conn_handler = SQLConnectionHandler()
        analyses = conn_handler.execute_fetchall(sql, (self._id, ))
        return [Analysis(a[0]) for a in analyses]

    # ---Functions---
    def add_shared_study(self, study):
        """Adds a new shared study to the user

        Parameters
        ----------
        study : Study object
            The study to be added to the shared list
        """
        sql = "INSERT INTO qiita.study_users (email, study_id) VALUES (%s, %s)"
        conn_handler = SQLConnectionHandler()
        conn_handler.execute(sql, (self._id, study.id))

    def remove_shared_study(self, study):
        """Removes a shared study from the user

        Parameters
        ----------
        study :
            The study to be removed from the shared list
        """
        sql = ("DELETE FROM qiita.study_users WHERE  email = %s")
        conn_handler = SQLConnectionHandler()
        conn_handler.execute(sql, (self._id, ))

    def add_shared_analysis(self, analysis):
        """Adds a new shared analysis to the user

        Parameters
        ----------
        analysis : Analysis object
            The analysis to be added to the shared list
        """
        sql = ("INSERT INTO qiita.analysis_users (email, study_id) VALUES "
               "(%s, %s)")
        conn_handler = SQLConnectionHandler()
        conn_handler.execute(sql, (self._id, analysis.id))

    def remove_shared_analysis(self, analysis):
        """Removes a shared analysis from the user

        Parameters
        ----------
        analysis :
            The analysis to be removed from the shared list
        """
        sql = ("DELETE FROM qiita.analysis_users WHERE  email = %s")
        conn_handler = SQLConnectionHandler()
        conn_handler.execute(sql, (self._id, ))
