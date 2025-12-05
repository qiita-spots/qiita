# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from datetime import datetime, timezone

from jose import jwt as jose_jwt

import qiita_db as qdb
from qiita_core.qiita_settings import qiita_config


class DownloadLink(qdb.base.QiitaObject):
    r"""
    A shortened url for downloading artifacts
    alongside a signed jwt and expiration

    Methods
    -------
    delete_expired

    See Also
    --------
    qiita_db.QiitaObject
    """

    _table = "download_link"

    @classmethod
    def create(cls, jwt):
        r"""Creates a new object with a new id on the storage system

        Parameters
        ----------
        jwt : Json Web Token signing the access link.
        This jwt will have, at a minimum, jti and exp fields

        Raises
        ------
        IncompetentQiitaDeveloperError
            If the jwt is improperly signed or doesn't contain a jti or exp
        QiitaDBDuplicateError
            If the jti already exists in the database
        """

        jwt_data = jose_jwt.decode(jwt, qiita_config.jwt_secret, algorithms="HS256")
        jti = jwt_data["jti"]
        exp = datetime.utcfromtimestamp(jwt_data["exp"] / 1000)

        with qdb.sql_connection.TRN:
            if cls.exists(jti):
                raise qdb.exceptions.QiitaDBDuplicateError("JTI Already Exists")

            # insert token into database
            sql = """INSERT INTO qiita.{0} (jti, jwt, exp)
            VALUES (%s, %s, %s) RETURNING jti""".format(cls._table)
            qdb.sql_connection.TRN.add(sql, [jti, jwt, exp])
            qdb.sql_connection.TRN.execute()

    @classmethod
    def delete(cls, jti):
        r"""Deletes the link with specified jti from the storage system

        Parameters
        ----------
        jti : object
            The jwt token identifier
        """
        sql = """DELETE FROM qiita.{0} WHERE jti=%s""".format(cls._table)
        qdb.sql_connection.perform_as_transaction(sql, [jti])

    @classmethod
    def exists(cls, jti):
        r"""Checks if a link with specified jti exists

        Returns
        -------
        bool
            True if link exists else false
        """

        with qdb.sql_connection.TRN:
            sql = """SELECT COUNT(jti) FROM qiita.{0}
                     WHERE jti=%s""".format(cls._table)
            qdb.sql_connection.TRN.add(sql, [jti])
            return qdb.sql_connection.TRN.execute_fetchlast() == 1

    @classmethod
    def delete_expired(cls):
        r"""Deletes all expired download links"""
        now = datetime.now(timezone.utc)

        sql = """DELETE FROM qiita.{0} WHERE exp<%s""".format(cls._table)
        qdb.sql_connection.perform_as_transaction(sql, [now])

    @classmethod
    def get(cls, jti):
        r"""Retrieves a jwt by its jti

        Returns
        -------
        str
            A JSON web token

        """

        with qdb.sql_connection.TRN:
            sql = """SELECT jwt FROM qiita.{0}
                     WHERE jti=%s""".format(cls._table)
            qdb.sql_connection.TRN.add(sql, [jti])
            return qdb.sql_connection.TRN.execute_fetchlast()
