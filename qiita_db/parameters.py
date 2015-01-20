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
from .exceptions import QiitaDBDuplicateError


class BaseParameters(QiitaObject):
    r"""Base object to access to the parameters table"""

    @classmethod
    def _check_columns(cls, **kwargs):
        db_cols = set(get_table_cols(cls._table))
        db_cols.remove("param_set_name")
        db_cols.remove(cls._column_id)
        missing = db_cols.difference(kwargs)

        if missing:
            raise ValueError("Missing columns: %s" % ', '.join(missing))

        extra = set(kwargs).difference(db_cols)
        if extra:
            raise ValueError("Extra columns: %s" % ', '.join(extra))

    @classmethod
    def exists(cls, **kwargs):
        r"""Check if the parameter set already exists on the DB"""
        cls._check_columns(**kwargs)

        conn_handler = SQLConnectionHandler()

        cols = ["{} = %s".format(col) for col in kwargs]

        return conn_handler.execute_fetchone(
            "SELECT EXISTS(SELECT * FROM qiita.{0} WHERE {1})".format(
                cls._table, ' AND '.join(cols)),
            kwargs.values())[0]

    @classmethod
    def create(cls, param_set_name, **kwargs):
        r"""Adds a new parameter set to the DB"""
        cls._check_columns(**kwargs)

        conn_handler = SQLConnectionHandler()

        vals = kwargs.values()
        vals.insert(0, param_set_name)

        if cls.exists(**kwargs):
            raise QiitaDBDuplicateError(cls.__name__, "Values: %s" % kwargs)

        id_ = conn_handler.execute_fetchone(
            "INSERT INTO qiita.{0} (param_set_name, {1}) VALUES (%s, {2}) "
            "RETURNING {3}".format(
                cls._table, ', '.join(kwargs),
                ', '.join(['%s'] * len(kwargs)), cls._column_id),
            vals)[0]

        return cls(id_)

    @classmethod
    def iter(cls):
        """Iterates over all parameters

        Returns
        -------
        generator
            Yields a parameter instance
        """
        conn_handler = SQLConnectionHandler()
        sql = "SELECT {0} FROM qiita.{1}".format(cls._column_id, cls._table)

        for result in conn_handler.execute_fetchall(sql):
            yield cls(result[0])

    @property
    def name(self):
        """The name of the parameter set

        Returns
        -------
        str
            The name of the parameter set
        """
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(
            "SELECT param_set_name FROM qiita.{0} WHERE {1} = %s".format(
                self._table, self._column_id),
            (self.id,))[0]

    @property
    def values(self):
        """The values of the parameter set

        Returns
        -------
        dict
            Dictionary with the parameter values keyed by parameter name
        """
        conn_handler = SQLConnectionHandler()
        result = dict(conn_handler.execute_fetchone(
            "SELECT * FROM qiita.{0} WHERE {1} = %s".format(
                self._table, self._column_id),
            (self.id,)))
        # Remove the parameter id and the parameter name as those are used
        # internally, and they are not passed to the processing step
        del result[self._column_id]
        del result['param_set_name']
        return result

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
            "SELECT EXISTS(SELECT * FROM qiita.{0} WHERE {1} = %s)".format(
                self._table, self._column_id),
            (id_, ))[0]

    def _get_values_as_dict(self, conn_handler):
        r""""""
        return dict(conn_handler.execute_fetchone(
                    "SELECT * FROM qiita.{0} WHERE {1}=%s".format(
                        self._table, self._column_id), (self.id,)))

    def to_str(self):
        r"""Generates a string with the parameter values

        Returns
        -------
        str
            The string with all the parameters
        """
        conn_handler = SQLConnectionHandler()
        table_cols = get_table_cols_w_type(self._table)
        table_cols.remove([self._column_id, 'bigint'])

        values = self._get_values_as_dict(conn_handler=conn_handler)

        result = []
        for p_name, p_type in sorted(table_cols):
            if p_name in self._ignore_cols:
                continue
            if p_type == 'boolean':
                if values[p_name]:
                    result.append("--%s" % p_name)
            else:
                result.append("--%s %s" % (p_name, values[p_name]))

        return " ".join(result)


class PreprocessedIlluminaParams(BaseParameters):
    r"""Gives access to the preprocessed parameters of illumina data"""

    _column_id = "preprocessed_params_id"
    _table = "preprocessed_sequence_illumina_params"
    _ignore_cols = {"param_set_name"}


class Preprocessed454Params(BaseParameters):
    r"""Gives access to the preprocessed parameters of illumina data"""

    _column_id = "preprocessed_params_id"
    _table = "preprocessed_sequence_454_params"
    _ignore_cols = {"param_set_name"}


class ProcessedSortmernaParams(BaseParameters):
    r"""Gives access to the processed parameters using SortMeRNA"""

    _column_id = "processed_params_id"
    _table = "processed_params_sortmerna"
    _ignore_cols = {'reference_id', 'param_set_name'}

    @property
    def reference(self):
        """"Returns the reference id used on this parameter set"""
        conn_handler = SQLConnectionHandler()

        return conn_handler.execute_fetchone(
            "SELECT reference_id FROM qiita.{0} WHERE {1}=%s".format(
                self._table, self._column_id), (self.id,))[0]

    def to_file(self, f):
        r"""Writes the parameters to a file in QIIME parameters file format

        Parameters
        ----------
        f : file-like object
            File-like object to write the parameters. Should support the write
            operation
        """
        conn_handler = SQLConnectionHandler()
        values = self._get_values_as_dict(conn_handler)

        # Remove the id column
        del values[self._column_id]

        # We know that the execution method is SortMeRNA,
        # add it to the parameter file
        f.write("pick_otus:otu_picking_method\tsortmerna\n")

        for key, value in sorted(values.items()):
            if key in self._ignore_cols:
                continue
            f.write("pick_otus:%s\t%s\n" % (key, value))
