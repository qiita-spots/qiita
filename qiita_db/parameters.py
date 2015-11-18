# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

import qiita_db as qdb


class BaseParameters(qdb.base.QiitaObject):
    r"""Base object to access to the parameters table"""

    @classmethod
    def _check_columns(cls, **kwargs):
        db_cols = set(qdb.util.get_table_cols(cls._table))
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
        with qdb.sql_connection.TRN:
            cls._check_columns(**kwargs)

            cols = ["{} = %s".format(col) for col in kwargs]
            sql = "SELECT EXISTS(SELECT * FROM qiita.{0} WHERE {1})".format(
                cls._table, ' AND '.join(cols))

            qdb.sql_connection.TRN.add(sql, kwargs.values())
            return qdb.sql_connection.TRN.execute_fetchlast()

    @classmethod
    def create(cls, param_set_name, **kwargs):
        r"""Adds a new parameter set to the DB"""
        with qdb.sql_connection.TRN:
            cls._check_columns(**kwargs)

            vals = kwargs.values()
            vals.insert(0, param_set_name)

            if cls.exists(**kwargs):
                raise qdb.exceptions.QiitaDBDuplicateError(
                    cls.__name__, "Values: %s" % kwargs)

            sql = """INSERT INTO qiita.{0} (param_set_name, {1})
                     VALUES (%s, {2})
                     RETURNING {3}""".format(
                cls._table,
                ', '.join(kwargs),
                ', '.join(['%s'] * len(kwargs)),
                cls._column_id)

            qdb.sql_connection.TRN.add(sql, vals)

            return cls(qdb.sql_connection.TRN.execute_fetchlast())

    @classmethod
    def iter(cls):
        """Iterates over all parameters

        Returns
        -------
        generator
            Yields a parameter instance
        """
        with qdb.sql_connection.TRN:
            sql = "SELECT {0} FROM qiita.{1}".format(cls._column_id,
                                                     cls._table)
            qdb.sql_connection.TRN.add(sql)
            for result in qdb.sql_connection.TRN.execute_fetchflatten():
                yield cls(result)

    @property
    def name(self):
        """The name of the parameter set

        Returns
        -------
        str
            The name of the parameter set
        """
        with qdb.sql_connection.TRN:
            sql = "SELECT param_set_name FROM qiita.{0} WHERE {1} = %s".format(
                self._table, self._column_id)
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def values(self):
        """The values of the parameter set

        Returns
        -------
        dict
            Dictionary with the parameter values keyed by parameter name
        """
        with qdb.sql_connection.TRN:
            sql = "SELECT * FROM qiita.{0} WHERE {1} = %s".format(
                self._table, self._column_id)
            qdb.sql_connection.TRN.add(sql, [self.id])
            # There should be only one row
            result = dict(qdb.sql_connection.TRN.execute_fetchindex()[0])
            # Remove the parameter id and the parameter name as those are used
            # internally, and they are not passed to the processing step
            del result[self._column_id]
            del result['param_set_name']
            return result

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
        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(
                        SELECT * FROM qiita.{0}
                        WHERE {1} = %s)""".format(self._table, self._column_id)
            qdb.sql_connection.TRN.add(sql, [id_])
            return qdb.sql_connection.TRN.execute_fetchlast()

    def _get_values_as_dict(self):
        r""""""
        with qdb.sql_connection.TRN:
            sql = "SELECT * FROM qiita.{0} WHERE {1}=%s".format(
                self._table, self._column_id)
            qdb.sql_connection.TRN.add(sql, [self.id])
            return dict(qdb.sql_connection.TRN.execute_fetchindex()[0])

    def to_str(self):
        r"""Generates a string with the parameter values

        Returns
        -------
        str
            The string with all the parameters
        """
        with qdb.sql_connection.TRN:
            table_cols = qdb.util.qdb.util.get_table_cols_w_type(self._table)
            table_cols.remove([self._column_id, 'bigint'])

            values = self._get_values_as_dict()

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

    _column_id = "parameters_id"
    _table = "preprocessed_sequence_illumina_params"
    _ignore_cols = {"param_set_name"}


class Preprocessed454Params(BaseParameters):
    r"""Gives access to the preprocessed parameters of illumina data"""

    _column_id = "parameters_id"
    _table = "preprocessed_sequence_454_params"
    _ignore_cols = {"param_set_name"}


class ProcessedSortmernaParams(BaseParameters):
    r"""Gives access to the processed parameters using SortMeRNA"""

    _column_id = "parameters_id"
    _table = "processed_params_sortmerna"
    _ignore_cols = {'reference_id', 'param_set_name'}

    @property
    def reference(self):
        """"Returns the reference id used on this parameter set"""
        with qdb.sql_connection.TRN:
            sql = "SELECT reference_id FROM qiita.{0} WHERE {1}=%s".format(
                self._table, self._column_id)
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    def to_file(self, f):
        r"""Writes the parameters to a file in QIIME parameters file format

        Parameters
        ----------
        f : file-like object
            File-like object to write the parameters. Should support the write
            operation
        """
        values = self._get_values_as_dict()

        # Remove the id column
        del values[self._column_id]

        # We know that the execution method is SortMeRNA,
        # add it to the parameter file
        f.write("pick_otus:otu_picking_method\tsortmerna\n")

        for key, value in sorted(values.items()):
            if key in self._ignore_cols:
                continue
            f.write("pick_otus:%s\t%s\n" % (key, value))
