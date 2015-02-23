r"""
Logging objects (:mod: `qiita_db.logger`)
====================================

..currentmodule:: qiita_db.logger

This module provides objects for recording log information

Classes
-------

..autosummary::
    :toctree: generated/

    LogEntry
"""

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division

from json import loads, dumps

from qiita_db.util import convert_to_id
from .sql_connection import SQLConnectionHandler
from .base import QiitaObject


class LogEntry(QiitaObject):
    """
    Attributes
    ----------
    severity
    time
    info
    message

    Methods
    -------
    clear_info
    add_info
    """

    _table = 'logging'

    @classmethod
    def newest_records(cls, numrecords=100):
        """Return a list of the newest records in the logging table

        Parameters
        ----------
        numrecords : int, optional
            The number of records to return. Default 100

        Returns
        -------
        list of LogEntry objects
            list of the log entries
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT logging_id FROM qiita.{0} ORDER BY logging_id DESC "
               "LIMIT %s".format(cls._table))
        ids = [x[0]
               for x in conn_handler.execute_fetchall(sql, (numrecords, ))]

        return [cls(i) for i in ids]

    @classmethod
    def create(cls, severity, msg, info=None):
        """Creates a new LogEntry object

        Parameters
        ----------
        severity : str  {Warning, Runtime, Fatal}
            The level of severity to use for the LogEntry. Refers to an entry
            in the SEVERITY table.
        msg : str
            The message text
        info : dict, optional
            Defaults to ``None``. If supplied, the information will be added
            as the first entry in a list of information dicts. If ``None``,
            an empty dict will be added.

        Notes
        -----
        - When `info` is added, keys can be of any type, but upon retrieval,
          they will be of type str
        """
        if info is None:
            info = {}

        info = dumps([info])

        conn_handler = SQLConnectionHandler()
        sql = ("INSERT INTO qiita.{} (time, severity_id, msg, information) "
               "VALUES (NOW(), %s, %s, %s) "
               "RETURNING logging_id".format(cls._table))
        severity_id = convert_to_id(severity, "severity")
        id_ = conn_handler.execute_fetchone(sql, (severity_id, msg, info))[0]

        return cls(id_)

    @property
    def severity(self):
        """Returns the severity_id associated with this LogEntry

        Returns
        -------
        int
            This is a key to the SEVERITY table
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT severity_id FROM qiita.{} WHERE "
               "logging_id = %s".format(self._table))

        return conn_handler.execute_fetchone(sql, (self.id,))[0]

    @property
    def time(self):
        """Returns the time that this LogEntry was created

        Returns
        -------
        datetime
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT time FROM qiita.{} "
               "WHERE logging_id = %s".format(self._table))
        timestamp = conn_handler.execute_fetchone(sql, (self.id,))[0]

        return timestamp

    @property
    def info(self):
        """Returns the info associated with this LogEntry

        Returns
        -------
        list of dict
            Each entry in the list is information that was added (the info
            added upon creation will be index 0, and if additional info
            was supplied subsequently, those entries will occupy subsequent
            indices)

        Notes
        -----
        - When `info` is added, keys can be of any type, but upon retrieval,
          they will be of type str
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT information FROM qiita.{} "
               "WHERE logging_id = %s".format(self._table))
        info = conn_handler.execute_fetchone(sql, (self.id,))[0]

        return loads(info)

    @property
    def msg(self):
        """Gets the message text for this LogEntry

        Returns
        -------
        str
        """
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT msg FROM qiita.{0} "
               "WHERE logging_id = %s".format(self._table))

        return conn_handler.execute_fetchone(sql, (self.id,))[0]

    def clear_info(self):
        """Resets the list of info dicts to be an empty list
        """
        conn_handler = SQLConnectionHandler()
        sql = ("UPDATE qiita.{} set information = %s "
               "WHERE logging_id = %s".format(self._table))
        new_info = dumps([])

        conn_handler.execute(sql, (new_info, self.id))

    def add_info(self, info):
        """Adds new information to the info associated with this LogEntry

        Parameters
        ----------
        info : dict
            The information to add.

        Notes
        -----
        - When `info` is added, keys can be of any type, but upon retrieval,
          they will be of type str
        """
        conn_handler = SQLConnectionHandler()
        current_info = self.info
        current_info.append(info)
        new_info = dumps(current_info)

        sql = ("UPDATE qiita.{} SET information = %s "
               "WHERE logging_id = %s".format(self._table))
        conn_handler.execute(sql, (new_info, self.id))
