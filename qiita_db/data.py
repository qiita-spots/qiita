r"""
Data objects (:mod: `qiita_db.data`)
====================================

..currentmodule:: qiita_db.data


This module provides functionality for inserting, querying and deleting
data stored in the database. There are three data classes available: `RawData`,
`PreprocessedData` and `ProcessedData`.

Objects for dealing with Qiita raw and (pre)processed data files

Classes
-------

..autosummary::
    :toctree: generated/

    BaseData
    RawData
    PreprocessedData
    ProcessedData

Examples
--------
Assume we have a raw data instance composed by two fastq files (the sequence
file 'seqs.fastq' and the barcodes file 'barcodes.fastq') that belongs to
study 1.

Inserting the raw data into the database:

>>> from qiita_db.data import RawData
>>> from qiita_db.study import Study
>>> study = Study(1)
>>> filepaths = [('seqs.fastq', 1), ('barcodes.fastq', 2)]
>>> rd = RawData.create(2, filepaths, study) # doctest: +SKIP
>>> print rd.id # doctest: +SKIP
2

Retrieve if the raw data files have been submitted to insdc

>>> rd.is_submitted_to_insdc() # doctest: +SKIP
False

Retrieve the filepaths associated with the raw data

>>> rd.get_filepaths() # doctest: +SKIP
[('seqs.fastq', 1), ('barcodes.fastq', 2)]

Assume we have preprocessed the previous raw data files using the parameters
under the first row in the 'preprocessed_sequence_illumina_params', and we
obtained to files: a fasta file 'seqs.fna' and a qual file 'seqs.qual'.

Inserting the preprocessed data into the database

>>> from qiita_db.data import PreprocessedData
>>> filepaths = [('seqs.fna', 4), ('seqs.qual', 5)]
>>> ppd = PreprocessedData.create(rd, "preprocessed_sequence_illumina_params",
...                               1, filepaths) # doctest: +SKIP
>>> print ppd.id # doctest: +SKIP
2

Assume we have processed the previous preprocessed data on June 2nd 2014 at 5pm
using uclust and the first set of parameters, and we obtained a BIOM table.

Inserting the processed data into the database:

>>> from qiita_db.data import ProcessedData
>>> from datetime import datetime
>>> filepaths = [('foo/table.biom', 6)]
>>> date = datetime(2014, 6, 2, 5, 0, 0)
>>> pd = ProcessedData(ppd, "processed_params_uclust", 1,
...                    filepaths, date) # doctest: +SKIP
>>> print pd.id # doctest: +SKIP
2
"""
from __future__ import division
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from datetime import datetime

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from .base import QiitaObject
from .sql_connection import SQLConnectionHandler
from .util import exists_dynamic_table


class BaseData(QiitaObject):
    """Base class for the raw and (pre)processed data objects"""
    _filepath_table = "filepath"

    # These variables should be defined in the subclasses. They are useful in
    # order to avoid code replication and be able to generalize the functions
    # included in this BaseClass
    _data_filepath_table = None
    _data_filepath_column = None

    @classmethod
    def _check_data_filepath_attributes(cls):
        """Checks if _data_filepath_table and _data_filepath_column have been
        defined, so this function is actually called from a subclass"""
        if (cls._data_filepath_table is None) or \
                (cls._data_filepath_column is None):
            raise IncompetentQiitaDeveloperError(
                "_data_filepath_table and _data_filepath_column should be "
                "defined in the classes that implement BaseData!")

    @classmethod
    def _insert_filepaths(cls, filepaths, conn_handler):
        """Inserts `filepaths` in the DB connected with `conn_handler`

        Parameters
        ----------
        filepaths : iterable of tuples (str, int)
            The list of paths to the raw files and its filepath type identifier
        conn_handler : SQLConnectionHandler
            The connection handler object connected to the DB

        Returns
        -------
        list
            The filepath_id in the database for each added filepath
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
    def _link_data_filepaths(cls, data_id, fp_ids, conn_handler):
        """Links the data `data_id` with its filepaths `fp_ids` in the DB
        connected with `conn_handler`

        Parameters
        ----------
        data_id : int
            The data identifier
        fp_ids : list of ints
            The filepaths ids to connect the data
        conn_handler : SQLConnectionHandler
            The connection handler object connected to the DB

        Raises
        ------
        IncompetentQiitaDeveloperError
            If called directly from the BaseClass or one of the subclasses does
            not define the class attributes _data_filepath_table and
            _data_filepath_column
        """
        # First check that the internal attributes have been defined, so this
        # function have been actually called from a subclass
        cls._check_data_filepath_attributes()

        # Create the list of SQL values to add
        values = [(data_id, fp_id) for fp_id in fp_ids]
        # Add all rows at once
        conn_handler.executemany(
            "INSERT INTO qiita.{0} ({1}, filepath_id) "
            "VALUES (%s, %s)".format(cls._data_filepath_table,
                                     cls._data_filepath_column), values)

    def get_filepaths(self):
        """
        Returns
        -------
        list of tuples
            A list of (path, filetype id) with all the paths associated with
            the current data
        """
        # First check that the internal attributes have been defined, so this
        # function have been actually called from a subclass
        self._check_data_filepath_attributes()
        # We need a connection handler to the database
        conn_handler = SQLConnectionHandler()
        # Retrieve all the (path, id) tuples related with the current data
        # object and return them. We need to first check the
        # _data_filepath_table to get the filepath ids of the filepath
        # associated with the current data object. We then can query the
        # filepath table to get those paths/
        return conn_handler.execute_fetchall(
            "SELECT filepath, filepath_type_id FROM qiita.{0} WHERE "
            "filepath_id IN (SELECT filepath_id FROM qiita.{1} WHERE "
            "{2}=%(id)s)".format(self._filepath_table,
                                 self._data_filepath_table,
                                 self._data_filepath_column), {'id': self.id})


class RawData(BaseData):
    """"""
    _table = "raw_data"
    _data_filepath_table = "raw_filepath"
    _data_filepath_column = "raw_data_id"

    _study_raw_table = "study_raw_data"

    @classmethod
    def create(cls, filetype, filepaths, study, submitted_to_insdc=False):
        """Creates a new object with a new id on the storage system

        Parameters
        ----------
        filetype : int
            The filetype identifier
        filepaths : iterable of tuples (str, int)
            The list of paths to the raw files and its filepath type identifier
        study : Study
            The Study object to which the raw data belongs to
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
            "INSERT INTO qiita.{0} (study_id, raw_data_id) VALUES "
            "(%(study_id)s, %(raw_id)s)".format(cls._study_raw_table),
            {'study_id': study.id, 'raw_id': rd_id})

        # Add the filepaths to the database
        fp_ids = cls._insert_filepaths(filepaths, conn_handler)

        # Connect the raw data with its filepaths
        cls._link_data_filepaths(rd_id, fp_ids, conn_handler)

        return cls(rd_id)

    def is_submitted_to_insdc(self):
        """Tells if the raw data has been submitted to insdc"""
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(
            "SELECT submitted_to_insdc FROM qiita.{0} "
            "WHERE raw_data_id=%s".format(self._table), [self.id])[0]


class PreprocessedData(BaseData):
    """"""
    _table = "preprocessed_data"
    _data_filepath_table = "preprocessed_filepath"
    _data_filepath_column = "preprocessed_data_id"

    @classmethod
    def create(cls, raw_data, preprocessed_params_table,
               preprocessed_params_id, filepaths):
        """Creates a new object with a new id on the storage system

        Parameters
        ----------
        raw_data : RawData
            The RawData object used as base to this preprocessed data
        preprocessed_params_table : str
            Name of the table that holds the preprocessing parameters used
        preprocessed_params_id : int
            Identifier of the parameters from the `preprocessed_params_table`
            table used
        filepaths : iterable of tuples (str, int)
            The list of paths to the preprocessed files and its filepath type
            identifier

        Raises
        ------
        IncompetentQiitaDeveloperError
            If the table `preprocessed_params_table` does not exists
        """
        conn_handler = SQLConnectionHandler()
        # We first check that the preprocessed_params_table exists
        if not exists_dynamic_table(preprocessed_params_table, "preprocessed_",
                                    "_params", conn_handler):
            raise IncompetentQiitaDeveloperError(
                "Preprocessed params table '%s' does not exists!"
                % preprocessed_params_table)
        # Add the preprocessed data to the database,
        # and get the preprocessed data id back
        ppd_id = conn_handler.execute_fetchone(
            "INSERT INTO qiita.{0} (raw_data_id, preprocessed_params_table, "
            "preprocessed_params_id) VALUES (%(raw_id)s, %(param_table)s, "
            "%(param_id)s) RETURNING preprocessed_data_id".format(cls._table),
            {'raw_id': raw_data.id, 'param_table': preprocessed_params_table,
             'param_id': preprocessed_params_id})[0]

        # Add the filepaths to the database
        fp_ids = cls._insert_filepaths(filepaths, conn_handler)

        # Connect the preprocessed data with its filepaths
        cls._link_data_filepaths(ppd_id, fp_ids, conn_handler)

        return cls(ppd_id)


class ProcessedData(BaseData):
    """"""
    _table = "processed_data"
    _data_filepath_table = "processed_filepath"
    _data_filepath_column = "processed_data_id"

    @classmethod
    def create(cls, preprocessed_data, processed_params_table,
               processed_params_id, filepaths, processed_date=None):
        """
        Parameters
        ----------
        preprocessed_data : PreprocessedData
            The PreprocessedData object used as base to this processed data
        processed_params_table : str
            Name of the table that holds the preprocessing parameters used
        processed_params_id : int
            Identifier of the parameters from the `processed_params_table`
            table used
        filepaths : iterable of tuples (str, int)
            The list of paths to the processed files and its filepath type
            identifier
        processed_date : datetime, optional
            Date in which the data have been processed. Default: now

        Raises
        ------
        IncompetentQiitaDeveloperError
            If the table `processed_params_table` does not exists
        """
        conn_handler = SQLConnectionHandler()
        # We first check that the processed_params_table exists
        if not exists_dynamic_table(processed_params_table,
                                    "processed_params_", "", conn_handler):
            raise IncompetentQiitaDeveloperError(
                "Processed params table %s does not exists!"
                % processed_params_table)

        # Check if we have received a date:
        if processed_date is None:
            processed_date = datetime.now()

        # Add the processed data to the database,
        # and get the processed data id back
        pd_id = conn_handler.execute_fetchone(
            "INSERT INTO qiita.{0} (preprocessed_data_id, "
            "processed_params_table, processed_params_id, processed_date) "
            "VALUES (%(prep_data_id)s, %(param_table)s, %(param_id)s, "
            "%(date)s) RETURNING processed_data_id".format(cls._table),
            {'prep_data_id': preprocessed_data.id,
             'param_table': processed_params_table,
             'param_id': processed_params_id,
             'date': processed_date})[0]

        # Add the filepaths to the database
        fp_ids = cls._insert_filepaths(filepaths, conn_handler)

        # Connect the processed data with its filepaths
        cls._link_data_filepaths(pd_id, fp_ids, conn_handler)

        return cls(pd_id)
