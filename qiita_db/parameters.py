# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from .base import QiitaObject
from .sql_connection import SQLConnectionHandler
from .util import get_table_cols_w_type, get_table_cols


class BaseParameters(QiitaObject):
    r"""Base object to access to the parameters table"""

    @classmethod
    def create(cls, param_set_name, **kwargs):
        r"""Adds a new parameter set to the DB"""
        db_cols = set(get_table_cols(cls._table))
        db_cols.remove("param_set_name")
        db_cols.remove("preprocessed_params_id")
        missing = db_cols.difference(kwargs)

        if missing:
            raise ValueError("Missing columns: %s" % ', '.join(missing))

        conn_handler = SQLConnectionHandler()

        vals = kwargs.values()
        vals.insert(0, param_set_name)

        id_ = conn_handler.execute_fetchone(
            "INSERT INTO qiita.{0} (param_set_name, {1}) VALUES (%s, {2}) "
            "RETURNING preprocessed_params_id".format(
                cls._table, ', '.join(kwargs),
                ', '.join(['%s'] * len(kwargs))),
            vals)[0]

        return cls(id_)

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
            "SELECT EXISTS(SELECT * FROM qiita.{0} WHERE "
            "preprocessed_params_id = %s)".format(self._table), (id_, ))[0]

    def to_str(self):
        r"""Generates a string with the parameter values

        Returns
        -------
        str
            The string with all the parameters
        """
        conn_handler = SQLConnectionHandler()
        table_cols = get_table_cols_w_type(self._table)
        table_cols.remove(["preprocessed_params_id", 'bigint'])
        table_cols.remove(["param_set_name", 'character varying'])

        values = dict(conn_handler.execute_fetchone(
            "SELECT * FROM qiita.{0} WHERE "
            "preprocessed_params_id=%s".format(self._table), (self.id,)))

        result = []
        for p_name, p_type in sorted(table_cols):
            if p_type == 'boolean':
                if values[p_name]:
                    result.append("--%s" % p_name)
            else:
                result.append("--%s %s" % (p_name, values[p_name]))

        return " ".join(result)


class PreprocessedIlluminaParams(BaseParameters):
    r"""Gives access to the preprocessed parameters of illumina data"""

    _table = "preprocessed_sequence_illumina_params"


class Preprocessed454Params(BaseParameters):
    r"""Gives access to the preprocessed parameters of illumina data"""

    _table = "preprocessed_sequence_454_params"
