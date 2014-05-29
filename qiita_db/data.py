from __future__ import division

"""
Objects for dealing with Qiita raw and (pre)processed data files

Classes
-------
- `MetadataTemplate` -- A Qiita Metadata template base class
- `SampleTemplate` -- A Qiita Sample template class
- `PrepTemplate` -- A Qiita Prep template class
"""

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from .base import QiitaObject
from .sql_connection import SQLConnectionHandler
from qiita_core.exceptions import IncompetentQiitaDeveloperError


class BaseData(QiitaObject):
    """Base class for the raw and (pre)processed data objects"""
    _filepath_table = "filepath"

    # These variables should be defined in the subclasses
    _data_filepath_table = None
    _data_filepath_column = None

    @classmethod
    def insert_filepaths(cls, filepaths, conn_handler):
        """Inserts `filepaths` in the DB connected with `conn_handler`

        Parameters
        ----------
        filepaths : iterable of tuples (str, int)
            The list of paths to the raw files and its fileapth type identifier
        conn_handler : qiita_db.SQLConnectionHandler
            The connection handler object connected to the DB

        Returns
        -------
        list
            The filepath_id in the databse for each added filepath
        """
        # Create the list of SQL values to add
        values = ["('%s', %s)" % (path, id) for path, id in filepaths]
        # Insert all the filepaths at once and get the filepath_id back
        ids = conn_handler.execute_fetchall(
            "INSERT INTO qiita.{0} (filepath, filepath_type_id) VALUES {1} "
            "RETURNING filepath_id".format(cls._filepath_table,
                                           ', '.join(values)))
        # we will receive a list of lists with a single element on it (the id),
        # transform it to a list of ids
        return [id[0] for id in ids]

    @classmethod
    def link_data_filepaths(cls, data_id, fp_ids, conn_handler):
        """Links the data `data_id` with its filepaths `fp_ids` in the DB
        connected with `conn_handler`

        Parameters
        ----------
        data_id : int
            The data identifier
        fp_ids : list of ints
            The filepaths ids to connect the data
        conn_handler : qiita_db.SQLConnectionHandler
            The connection handler object connected to the DB

        Raises
        ------
        IncompetentQiitaDeveloperError
            If called directly from the BaseClass or one of the subclasses does
            not define the class attributes _data_filepath_table and
            _data_filepath_column
        """
        if (cls._data_filepath_table is None) or \
                (cls._data_filepath_column is None):
            raise IncompetentQiitaDeveloperError(
                "_data_filepath_table and _data_filepath_column should be "
                "defined in the classes that implement BaseData!")

        values = [(data_id, fp_id) for fp_id in fp_ids]
        conn_handler.executemany(
            "INSERT INTO qiita.{0} ({1}, filepath_id) "
            "VALUES (%s, %s)".format(cls._data_filepath_table,
                                     cls._data_filepath_column),
            values)


class RawData(BaseData):
    """"""
    _table = "raw_data"
    _data_filepath_table = "raw_filepath"
    _data_filepath_column = "raw_data_id"

    _study_raw_table = "study_raw_data"

    @classmethod
    def create(cls, filetype, filepaths, study_id, submitted_to_insdc=False):
        """Creates a new object with a new id on the storage system

        Parameters
        ----------
        filetype : int
            The filetype identifier
        filepath : iterable of tuples (str, int)
            The list of paths to the raw files and its fileapth type identifier
        study_id : int
            The study identifier to which the raw data belongs to
        submitted_to_insdc : bool
            If true, the raw data files have been submitted to insdc

        Returns
        -------
        A new instance of `cls` to access to the RawData stored in the DB
        """
        conn_handler = SQLConnectionHandler()
        # Add the raw data to the database, and get the raw data id back
        rd_id = conn_handler.execute_fetchone(
            "INSERT INTO qiita.{0} (filetype_id, submitted_to_insdc) VALUES "
            "(%(type_id)s, %(insdc)s) RETURNING "
            "raw_data_id".format(cls._table), {'type_id': filetype,
                                               'insdc': submitted_to_insdc})[0]

        # Connect the raw data with its study
        conn_handler.execute(
            "INSERT INTO qiita." + cls._study_raw_table + " (study_id, "
            "raw_data_id) VALUES (%(study_id)s, %(raw_id)s)",
            {'study_id': study_id, 'raw_id': rd_id})

        # Add the filepaths to the database
        fp_ids = cls.insert_filepaths(filepaths, conn_handler)

        # Connect the raw data with its filepaths
        cls.link_data_filepaths(rd_id, fp_ids, conn_handler)

        return cls(rd_id)

    @classmethod
    def delete(cls, id_):
        """Deletes the object `id_` from the storage system

        Parameters
        ----------
        id_ :
            The object identifier
        """
        # Remove
        raise NotImplementedError()

    def is_submitted_to_insdc(self):
        """Tells if the raw data has been submitted to insdc"""
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(
            "SELECT submitted_to_insdc FROM qiita.{0} "
            "WHERE raw_data_id=%s".format(self._table), [self.id])[0]



# class PreprocessedData(BaseData):
#     """"""
#     _table = "preprocessed_data"
#     _data_filepath_table = "preprocessed_filepath"
#     _data_filepath_column = "preprocessed_data_id"

#     @classmethod
#     def create(cls, raw_data_id, preprocessed_params_table,
#                preprocessed_params_id):
#         """Creates a new object with a new id on the storage system

#         Parameters
#         ----------
#         raw_data_id : int
#         preprocessed_params_table : str
#         preprocessed_params_id : int
#         """
#         conn_handler = SQLConnectionHandler()
#         # Add the raw data to the database, and get the raw data id back
#         rd_id = conn_handler.execute_fetchone(
#             "INSERT INTO qiita." + cls._table + " (filetype_id, "
#             "submitted_to_insdc) VALUES (%(type_id)s, %(insdc)s) "
#             "RETURNING raw_data_id", {'type_id': filetype,
#                                       'insdc': submitted_to_insdc})[0]

#         # Connect the raw data with its study
#         conn_handler.execute(
#             "INSERT INTO qiita." + cls._study_raw_table + " (study_id, "
#             "raw_data_id) VALUES (%(study_id)s, %(raw_id)s)",
#             {'study_id': study_id, 'raw_id': rd_id})

#         # Add the filepaths to the database
#         fp_ids = cls.insert_filepaths(filepaths, conn_handler)

#         # Connect the raw data with its filepaths
#         cls.link_data_filepaths(rd_id, fp_ids, conn_handler)

#         return cls(rd_id)

#     @classmethod
#     def delete(id_):
#         """Deletes the object `id_` from the storage system

#         Parameters
#         ----------
#         id_ :
#             The object identifier
#         """
#         raise NotImplementedError()
