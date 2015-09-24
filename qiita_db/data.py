r"""
Data objects (:mod: `qiita_db.data`)
====================================

..currentmodule:: qiita_db.data

This module provides functionality for inserting, querying and deleting
data stored in the database. There are three data classes available: `RawData`,
`PreprocessedData` and `ProcessedData`.

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
>>> study = Study(1) # doctest: +SKIP
>>> filepaths = [('seqs.fastq', 1), ('barcodes.fastq', 2)]
>>> rd = RawData.create(2, filepaths, study) # doctest: +SKIP
>>> print rd.id # doctest: +SKIP
2

Retrieve the filepaths associated with the raw data

>>> rd.get_filepaths() # doctest: +SKIP
[(1, 'seqs.fastq', 'raw_sequences'), (2, 'barcodes.fastq', 'raw_barcodes')]

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

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from datetime import datetime
from os.path import join
from functools import partial

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from .base import QiitaObject
from .logger import LogEntry
from .sql_connection import TRN
from .exceptions import QiitaDBError, QiitaDBUnknownIDError, QiitaDBStatusError
from .util import (exists_dynamic_table, insert_filepaths, convert_to_id,
                   convert_from_id, get_filepath_id, get_mountpoint,
                   move_filepaths_to_upload_folder, infer_status)


class BaseData(QiitaObject):
    r"""Base class for the raw, preprocessed and processed data objects.

    Methods
    -------
    get_filepaths

    See Also
    --------
    RawData
    PreprocessedData
    ProcessedData
    """
    _filepath_table = "filepath"

    # These variables should be defined in the subclasses. They are useful in
    # order to avoid code replication and be able to generalize the functions
    # included in this BaseClass
    _data_filepath_table = None
    _data_filepath_column = None

    def _link_data_filepaths(self, fp_ids):
        r"""Links the data `data_id` with its filepaths `fp_ids` in the DB

        Parameters
        ----------
        fp_ids : list of ints
            The filepaths ids to connect the data

        Raises
        ------
        IncompetentQiitaDeveloperError
            If called directly from the BaseClass or one of the subclasses does
            not define the class attributes _data_filepath_table and
            _data_filepath_column
        """
        with TRN:
            # Create the list of SQL values to add
            values = [[self.id, fp_id] for fp_id in fp_ids]
            # Add all rows at once
            sql = """INSERT INTO qiita.{0} ({1}, filepath_id)
                     VALUES (%s, %s)""".format(self._data_filepath_table,
                                               self._data_filepath_column)
            TRN.add(sql, values, many=True)
            TRN.execute()

    def add_filepaths(self, filepaths):
        r"""Populates the DB tables for storing the filepaths and connects the
        `self` objects with these filepaths"""
        with TRN:
            # Update the status of the current object
            self._set_link_filepaths_status("linking")

            try:
                # Add the filepaths to the database
                fp_ids = insert_filepaths(filepaths, self._id, self._table,
                                          self._filepath_table)

                # Connect the raw data with its filepaths
                self._link_data_filepaths(fp_ids)
            except Exception as e:
                # Something went wrong, update the status
                self._set_link_filepaths_status("failed: %s" % e)
                LogEntry.create('Runtime', str(e),
                                info={self.__class__.__name__: self.id})
                raise e

            # Filepaths successfully added, update the status
            self._set_link_filepaths_status("idle")

    def get_filepaths(self):
        r"""Returns the filepaths and filetypes associated with the data object

        Returns
        -------
        list of tuples
            A list of (filepath_id, path, filetype) with all the paths
            associated with the current data
        """
        with TRN:
            # Retrieve all the (path, id) tuples related with the current data
            # object. We need to first check the _data_filepath_table to get
            # the filepath ids of the filepath associated with the current data
            # object. We then can query the filepath table to get those paths.
            sql = """SELECT filepath_id, filepath, filepath_type_id
                     FROM qiita.{0}
                     WHERE filepath_id IN (
                        SELECT filepath_id
                        FROM qiita.{1}
                        WHERE {2}=%s)""".format(self._filepath_table,
                                                self._data_filepath_table,
                                                self._data_filepath_column)
            TRN.add(sql, [self.id])
            db_paths = TRN.execute_fetchindex()

            _, fb = get_mountpoint(self._table)[0]
            base_fp = partial(join, fb)

            return [(fpid, base_fp(fp), convert_from_id(fid, "filepath_type"))
                    for fpid, fp, fid in db_paths]

    def get_filepath_ids(self):
        with TRN:
            sql = "SELECT filepath_id FROM qiita.{0} WHERE {1}=%s".format(
                self._data_filepath_table, self._data_filepath_column)
            TRN.add(sql, [self.id])
            return TRN.execute_fetchflatten()

    @property
    def link_filepaths_status(self):
        with TRN:
            sql = """SELECT link_filepaths_status
                     FROM qiita.{0}
                     WHERE {1}=%s""".format(self._table,
                                            self._data_filepath_column)
            TRN.add(sql, [self.id])
            return TRN.execute_fetchlast()

    def _set_link_filepaths_status(self, status):
        """Updates the link_filepaths_status of the object

        Parameters
        ----------
        status : str
            The new status

        Raises
        ------
        ValueError
            If the status is unknown
        """
        with TRN:
            if (status not in ('idle', 'linking', 'unlinking') and
                    not status.startswith('failed')):
                msg = 'Unknown status: %s' % status
                LogEntry.create('Runtime', msg,
                                info={self.__class__.__name__: self.id})
                raise ValueError(msg)

            sql = """UPDATE qiita.{0} SET link_filepaths_status = %s
                     WHERE {1} = %s""".format(self._table,
                                              self._data_filepath_column)
            TRN.add(sql, [status, self._id])
            TRN.execute()

    @classmethod
    def exists(cls, object_id):
        r"""Checks if the given object_id exists

        Parameters
        ----------
        id : str
            The id of the object we are searching for

        Returns
        -------
        bool
            True if exists, false otherwise.
        """
        with TRN:
            cls._check_subclass()
            sql = "SELECT EXISTS(SELECT * FROM qiita.{0} WHERE {1}=%s)".format(
                cls._table, cls._data_filepath_column)
            TRN.add(sql, [object_id])
            return TRN.execute_fetchlast()


class RawData(BaseData):
    r"""Object for dealing with raw data

    Attributes
    ----------
    studies
    investigation_type

    Methods
    -------
    create
    data_type
    preprocessed_data

    See Also
    --------
    BaseData
    """
    # Override the class variables defined in the base classes
    _table = "raw_data"
    _data_filepath_table = "raw_filepath"
    _data_filepath_column = "raw_data_id"

    @classmethod
    def create(cls, filetype, prep_templates, filepaths):
        r"""Creates a new object with a new id on the storage system

        Parameters
        ----------
        filetype : int
            The filetype identifier
        prep_templates : list of PrepTemplates
            The list of PrepTemplate objects to which the raw data is attached
        filepaths : iterable of tuples (str, int)
            The list of paths to the raw files and its filepath type identifier

        Returns
        -------
        A new instance of `cls` to access to the RawData stored in the DB

        Raises
        ------
        QiitaDBError
            If any of the passed prep templates already have a raw data id
        """
        with TRN:
            # We first need to check if the passed prep templates don't have
            # a raw data already attached to them
            sql = """SELECT EXISTS(
                        SELECT *
                        FROM qiita.prep_template
                        WHERE prep_template_id IN %s
                            AND raw_data_id IS NOT NULL)""".format(
                ', '.join(['%s'] * len(prep_templates)))
            TRN.add(sql, [tuple(pt.id for pt in prep_templates)])
            exists = TRN.execute_fetchlast()
            if exists:
                raise QiitaDBError(
                    "Cannot create raw data because the passed prep templates "
                    "already have a raw data associated with it. "
                    "Prep templates: %s"
                    % ', '.join([str(pt.id) for pt in prep_templates]))

            # Add the raw data to the database, and get the raw data id back
            sql = """INSERT INTO qiita.{0} (filetype_id) VALUES (%s)
                     RETURNING raw_data_id""".format(cls._table)
            TRN.add(sql, [filetype])
            rd_id = TRN.execute_fetchlast()

            # Instantiate the object with the new id
            rd = cls(rd_id)

            # Connect the raw data with its prep templates
            values = [[rd_id, pt.id] for pt in prep_templates]
            sql = """UPDATE qiita.prep_template
                     SET raw_data_id = %s WHERE prep_template_id = %s"""
            TRN.add(sql, values, many=True)
            TRN.execute()

            # Link the files with the raw data object
            rd.add_filepaths(filepaths)

            return rd

    @classmethod
    def delete(cls, raw_data_id, prep_template_id):
        """Removes the raw data with id raw_data_id

        Parameters
        ----------
        raw_data_id : int
            The raw data id
        prep_template_id : int
            The prep_template_id

        Raises
        ------
        QiitaDBUnknownIDError
            If the raw data id doesn't exist
        QiitaDBError
            If the raw data is not linked to that prep_template_id
            If the raw data has files linked
        """
        with TRN:
            # check if the raw data exist
            if not cls.exists(raw_data_id):
                raise QiitaDBUnknownIDError(raw_data_id, "raw data")

            # Check if the raw data is linked to the prep template
            sql = """SELECT EXISTS(
                        SELECT * FROM qiita.prep_template
                        WHERE prep_template_id = %s AND raw_data_id = %s)"""
            TRN.add(sql, [prep_template_id, raw_data_id])
            pt_rd_exists = TRN.execute_fetchlast()
            if not pt_rd_exists:
                raise QiitaDBError(
                    "Raw data %d is not linked to prep template %d or the "
                    "prep template doesn't exist"
                    % (raw_data_id, prep_template_id))

            # Check to how many prep templates the raw data is still linked.
            # If last one, check that are no linked files
            sql = """SELECT COUNT(*) FROM qiita.prep_template
                     WHERE raw_data_id = %s"""
            TRN.add(sql, [raw_data_id])
            raw_data_count = TRN.execute_fetchlast()
            if raw_data_count == 1 and RawData(raw_data_id).get_filepath_ids():
                raise QiitaDBError(
                    "Raw data (%d) can't be removed because it has linked "
                    "files. To remove it, first unlink files." % raw_data_id)

            # delete
            sql = """UPDATE qiita.prep_template
                     SET raw_data_id = %s
                     WHERE prep_template_id = %s"""
            TRN.add(sql, [None, prep_template_id])

            # If there is no other prep template pointing to the raw data, it
            # can be removed
            if raw_data_count == 1:
                sql = "DELETE FROM qiita.raw_data WHERE raw_data_id = %s"
                TRN.add(sql, [raw_data_id])

            TRN.execute()

    @property
    def studies(self):
        r"""The IDs of the studies to which this raw data belongs

        Returns
        -------
        list of int
            The list of study ids to which the raw data belongs to
        """
        with TRN:
            sql = """SELECT study_id
                     FROM qiita.study_prep_template
                        JOIN qiita.prep_template USING (prep_template_id)
                     WHERE raw_data_id = %s"""
            TRN.add(sql, [self.id])
            return TRN.execute_fetchflatten()

    @property
    def filetype(self):
        r"""Returns the raw data filetype

        Returns
        -------
        str
            The raw data's filetype
        """
        with TRN:
            sql = """SELECT f.type
                     FROM qiita.filetype f
                        JOIN qiita.{0} r ON f.filetype_id = r.filetype_id
                     WHERE r.raw_data_id=%s""".format(self._table)
            TRN.add(sql, [self._id])
            return TRN.execute_fetchlast()

    def data_types(self, ret_id=False):
        """Returns the list of data_types or data_type_ids

        Parameters
        ----------
        ret_id : bool, optional
            Return the id instead of the string, default False

        Returns
        -------
        list of str or int
            string values of data_type or ints if data_type_id
        """
        with TRN:
            ret = "_id" if ret_id else ""
            sql = """SELECT d.data_type{0}
                     FROM qiita.data_type d
                        JOIN qiita.prep_template p
                            ON p.data_type_id = d.data_type_id
                     WHERE p.raw_data_id = %s""".format(ret)
            TRN.add(sql, [self._id])
            return TRN.execute_fetchflatten()

    @property
    def prep_templates(self):
        with TRN:
            sql = """SELECT prep_template_id FROM qiita.prep_template
                     WHERE raw_data_id = %s ORDER BY prep_template_id"""
            TRN.add(sql, [self._id])
            return TRN.execute_fetchflatten()

    def _is_preprocessed(self):
        """Returns whether the RawData has been preprocessed or not

        Returns
        -------
        bool
            whether the RawData has been preprocessed or not
        """
        with TRN:
            sql = """SELECT EXISTS(
                        SELECT *
                        FROM qiita.prep_template_preprocessed_data PTPD
                            JOIN qiita.prep_template PT
                                ON PT.prep_template_id = PTPD.prep_template_id
                        WHERE PT.raw_data_id = %s)"""
            TRN.add(sql, [self._id])
            return TRN.execute_fetchlast()

    def _remove_filepath(self, fp):
        """Removes the filepath from the RawData

        Parameters
        ----------
        fp : str
            The filepath to remove

        Raises
        ------
        QiitaDBError
            If the RawData has been already preprocessed
        IncompetentQiitaDeveloperError
            If the queue is provided but not the conn_handler
        ValueError
            If fp does not belong to the raw data
        """
        with TRN:
            # If the RawData has been already preprocessed, we cannot remove
            # any file - raise an error
            if self._is_preprocessed():
                msg = ("Cannot clear all the filepaths from raw data %s, it "
                       "has been already preprocessed" % self._id)
                self._set_link_filepaths_status("failed: %s" % msg)
                raise QiitaDBError(msg)

            # The filepath belongs to one or more prep templates
            prep_templates = self.prep_templates
            if len(prep_templates) > 1:
                msg = ("Can't clear all the filepaths from raw data %s "
                       "because it has been used with other prep templates: "
                       "%s. If you want to remove it, first remove the raw "
                       "data from the other prep templates."
                       % (self._id, ', '.join(map(str, prep_templates))))
                self._set_link_filepaths_status("failed: %s" % msg)
                raise QiitaDBError(msg)

            # Get the filpeath id
            fp_id = get_filepath_id(self._table, fp)
            sql = """SELECT EXISTS(
                        SELECT *
                        FROM qiita.{0}
                        WHERE filepath_id=%s AND {1}=%s
                     )""".format(self._data_filepath_table,
                                 self._data_filepath_column)
            TRN.add(sql, [fp_id, self._id])
            fp_is_mine = TRN.execute_fetchlast()

            if not fp_is_mine:
                msg = ("The filepath %s does not belong to raw data %s"
                       % (fp, self._id))
                self._set_link_filepaths_status("failed: %s" % msg)
                raise ValueError(msg)

            # We can remove the file
            sql = "DELETE FROM qiita.{0} WHERE filepath_id=%s".format(
                self._data_filepath_table)
            TRN.add(sql, [fp_id])

    def clear_filepaths(self):
        """Removes all the filepaths attached to the RawData

        Raises
        ------
        QiitaDBError
            If the RawData has been already preprocessed
        """
        with TRN:
            self._set_link_filepaths_status("unlinking")

            filepaths = self.get_filepaths()
            for _, fp, _ in filepaths:
                self._remove_filepath(fp)

            try:
                TRN.execute()
            except Exception as e:
                self._set_link_filepaths_status("failed: %s" % e)
                LogEntry.create('Runtime', str(e),
                                info={self.__class__.__name__: self.id})
                raise e

            # We can already update the status to done, as the files have been
            # unlinked, the move_filepaths_to_upload_folder call will not
            # change the status of the raw data object
            self._set_link_filepaths_status("idle")

            # Move the files, if they are not used, if you get to this point
            # self.studies should only have one element, thus self.studies[0]
            move_filepaths_to_upload_folder(self.studies[0], filepaths)

    def status(self, study):
        """The status of the raw data within the given study

        Parameters
        ----------
        study : Study
            The study that is looking to the raw data status

        Returns
        -------
        str
            The status of the raw data

        Raises
        ------
        QiitaDBStatusError
            If the raw data does not belong to the passed study

        Notes
        -----
        Given that a raw data can be shared by multiple studies, we need to
        know under which context (study) we want to check the raw data status.
        The rationale is that a raw data object can contain data from multiple
        studies, so the raw data can have multiple status at the same time.
        We then check the processed data generated to infer the status of the
        raw data.
        """
        with TRN:
            if self._id not in study.raw_data():
                raise QiitaDBStatusError(
                    "The study %s does not have access to the raw data %s"
                    % (study.id, self.id))

            sql = """SELECT processed_data_status
                    FROM qiita.processed_data_status pds
                      JOIN qiita.processed_data pd
                        USING (processed_data_status_id)
                      JOIN qiita.preprocessed_processed_data ppd_pd
                        USING (processed_data_id)
                      JOIN qiita.prep_template_preprocessed_data pt_ppd
                        USING (preprocessed_data_id)
                      JOIN qiita.prep_template pt
                        USING (prep_template_id)
                      JOIN qiita.study_processed_data spd
                        USING (processed_data_id)
                    WHERE pt.raw_data_id=%s AND spd.study_id=%s"""
            TRN.add(sql, [self._id, study.id])

            return infer_status(TRN.execute_fetchindex())


class PreprocessedData(BaseData):
    r"""Object for dealing with preprocessed data

    Attributes
    ----------
    raw_data
    study
    prep_template
    ebi_submission_accession
    ebi_study_accession
    files

    Methods
    -------
    create
    is_submitted_to_insdc
    data_type

    See Also
    --------
    BaseData
    """
    # Override the class variables defined in the base classes
    _table = "preprocessed_data"
    _data_filepath_table = "preprocessed_filepath"
    _data_filepath_column = "preprocessed_data_id"
    _study_preprocessed_table = "study_preprocessed_data"
    _template_preprocessed_table = "prep_template_preprocessed_data"

    @classmethod
    def create(cls, study, preprocessed_params_table, preprocessed_params_id,
               filepaths, prep_template=None, data_type=None):
        r"""Creates a new object with a new id on the storage system

        Parameters
        ----------
        study : Study
            The study to which this preprocessed data belongs to
        preprocessed_params_table : str
            Name of the table that holds the preprocessing parameters used
        preprocessed_params_id : int
            Identifier of the parameters from the `preprocessed_params_table`
            table used
        filepaths : iterable of tuples (str, int)
            The list of paths to the preprocessed files and its filepath type
            identifier
            Submission status of the raw data files
        prep_template : PrepTemplate, optional
            The PrepTemplate object used to generate this preprocessed data
        data_type : str, optional
            The data_type of the preprocessed_data

        Raises
        ------
        IncompetentQiitaDeveloperError
            If the table `preprocessed_params_table` does not exists
        IncompetentQiitaDeveloperError
            If data_type does not match that of prep_template passed
        """
        with TRN:
            # Sanity checks for the preprocesses_data data_type
            if ((data_type and prep_template) and
                    data_type != prep_template.data_type):
                raise IncompetentQiitaDeveloperError(
                    "data_type passed does not match prep_template data_type!")
            elif data_type is None and prep_template is None:
                raise IncompetentQiitaDeveloperError(
                    "Neither data_type nor prep_template passed!")
            elif prep_template:
                # prep_template passed but no data_type,
                # so set to prep_template data_type
                data_type = prep_template.data_type(ret_id=True)
            else:
                # only data_type, so need id from the text
                data_type = convert_to_id(data_type, "data_type")

            # Check that the preprocessed_params_table exists
            if not exists_dynamic_table(preprocessed_params_table,
                                        "preprocessed_", "_params"):
                raise IncompetentQiitaDeveloperError(
                    "Preprocessed params table '%s' does not exists!"
                    % preprocessed_params_table)

            # Add the preprocessed data to the database,
            # and get the preprocessed data id back
            sql = """INSERT INTO qiita.{0} (
                        preprocessed_params_table, preprocessed_params_id,
                        data_type_id)
                     VALUES (%s, %s, %s)
                     RETURNING preprocessed_data_id""".format(cls._table)
            TRN.add(sql, [preprocessed_params_table, preprocessed_params_id,
                          data_type])
            ppd_id = TRN.execute_fetchlast()
            ppd = cls(ppd_id)

            # Connect the preprocessed data with its study
            sql = """INSERT INTO qiita.{0} (study_id, preprocessed_data_id)
                     VALUES (%s, %s)""".format(ppd._study_preprocessed_table)
            TRN.add(sql, [study.id, ppd.id])

            # If the prep template was provided, connect the preprocessed data
            # with the prep_template
            if prep_template is not None:
                sql = """INSERT INTO qiita.{0}
                            (prep_template_id, preprocessed_data_id)
                         VALUES (%s, %s)""".format(
                    cls._template_preprocessed_table)
                TRN.add(sql, [prep_template.id, ppd_id])

                sql = """UPDATE qiita.prep_template
                         SET preprocessing_status = 'success'
                         WHERE prep_template_id = %s"""
                TRN.add(sql, [prep_template.id])

            TRN.execute()
            # Add the filepaths to the database and connect them
            ppd.add_filepaths(filepaths)
            return ppd

    @classmethod
    def delete(cls, ppd_id):
        """Removes the preprocessed data with id ppd_id

        Parameters
        ----------
        ppd_id : int
            The preprocessed data id

        Raises
        ------
        QiitaDBStatusError
            If the preprocessed data status is not sandbox or if the
            preprocessed data EBI and VAMPS submission is not in a valid state
            ['not submitted', 'failed']
        QiitaDBError
            If the preprocessed data has been processed
        """
        with TRN:
            valid_submission_states = ['not submitted', 'failed']
            ppd = cls(ppd_id)

            if ppd.status != 'sandbox':
                raise QiitaDBStatusError(
                    "Illegal operation on non sandboxed preprocessed data")
            elif ppd.submitted_to_vamps_status() not in \
                    valid_submission_states:
                raise QiitaDBStatusError(
                    "Illegal operation. This preprocessed data has or is "
                    "being added to VAMPS.")

            sql = """SELECT processed_data_id
                     FROM qiita.preprocessed_processed_data
                     WHERE preprocessed_data_id = %s
                     ORDER BY processed_data_id""".format()
            TRN.add(sql, [ppd_id])
            processed_data = TRN.execute_fetchflatten()

            if processed_data:
                raise QiitaDBError(
                    "Preprocessed data %d cannot be removed because it was "
                    "used to generate the following processed data: %s" % (
                        ppd_id, ', '.join(map(str, processed_data))))

            # delete
            sql = """DELETE FROM qiita.prep_template_preprocessed_data
                     WHERE preprocessed_data_id = %s"""
            args = [ppd_id]
            TRN.add(sql, args)

            sql = """DELETE FROM qiita.preprocessed_filepath
                     WHERE preprocessed_data_id = %s"""
            TRN.add(sql, args)

            sql = """DELETE FROM qiita.study_preprocessed_data
                     WHERE preprocessed_data_id = %s"""
            TRN.add(sql, args)

            sql = """DELETE FROM qiita.preprocessed_data
                     WHERE preprocessed_data_id = %s"""
            TRN.add(sql, args)

            TRN.execute()

    @property
    def processed_data(self):
        r"""The processed data list generated from this preprocessed data"""
        with TRN:
            sql = """SELECT processed_data_id
                     FROM qiita.preprocessed_processed_data
                     WHERE preprocessed_data_id = %s"""
            TRN.add(sql, [self._id])
            return TRN.execute_fetchflatten()

    @property
    def prep_template(self):
        r"""The prep template used to generate the preprocessed data"""
        with TRN:
            sql = """SELECT prep_template_id
                     FROM qiita.{0}
                     WHERE preprocessed_data_id=%s""".format(
                self._template_preprocessed_table)
            TRN.add(sql, [self._id])
            result = TRN.execute_fetchindex()
            # If there is no prep template with the preprocessed data
            # result will be an empty list
            if result:
                result = result[0][0]
            return result

    @property
    def study(self):
        r"""The ID of the study to which this preprocessed data belongs

        Returns
        -------
        int
            The study id to which this preprocessed data belongs to
        """
        with TRN:
            sql = """SELECT study_id FROM qiita.{0}
                     WHERE preprocessed_data_id=%s""".format(
                self._study_preprocessed_table)
            TRN.add(sql, [self._id])
            return TRN.execute_fetchlast()

    def data_type(self, ret_id=False):
        """Returns the data_type or data_type_id

        Parameters
        ----------
        ret_id : bool, optional
            Return the id instead of the string, default False

        Returns
        -------
        str or int
            string value of data_type or data_type_id
        """
        with TRN:
            ret = "_id" if ret_id else ""
            sql = """SELECT d.data_type{0}
                     FROM qiita.data_type d
                        JOIN qiita.{1} p ON p.data_type_id = d.data_type_id
                     WHERE p.preprocessed_data_id = %s""".format(
                ret, self._table)
            TRN.add(sql, [self._id])
            return TRN.execute_fetchlast()

    def submitted_to_vamps_status(self):
        r"""Tells if the raw data has been submitted to VAMPS

        Returns
        -------
        str
            One of {'not submitted', 'submitting', 'success', 'failed'}
        """
        with TRN:
            sql = """SELECT submitted_to_vamps_status
                     FROM qiita.{0}
                     WHERE preprocessed_data_id=%s""".format(self._table)
            TRN.add(sql, [self.id])
            return TRN.execute_fetchlast()

    def update_vamps_status(self, status):
        r"""Update the VAMPS submission status

        Parameters
        ----------
        status : str, {'not submitted', 'submitting', 'success', 'failed'}
            The current status of submission

        Raises
        ------
        ValueError
            If the status is not known.
        """
        if status not in ('not submitted', 'submitting', 'success', 'failed'):
            raise ValueError("Unknown status: %s" % status)

        with TRN:
            sql = """UPDATE qiita.{0}
                     SET submitted_to_vamps_status = %s
                     WHERE preprocessed_data_id=%s""".format(self._table)
            TRN.add(sql, [status, self.id])
            TRN.execute()

    @property
    def processing_status(self):
        r"""Tells if the data has be processed or not

        Returns
        -------
        str
            One of {'not_processed', 'processing', 'processed', 'failed'}
        """
        with TRN:
            sql = """SELECT processing_status
                     FROM qiita.{0}
                     WHERE preprocessed_data_id=%s""".format(self._table)
            TRN.add(sql, [self.id])
            return TRN.execute_fetchlast()

    @processing_status.setter
    def processing_status(self, state):
        r"""Update the processing status

        Parameters
        ----------
        state : str, {'not_processed', 'processing', 'processed', 'failed'}
            The new status of processing

        Raises
        ------
        ValueError
            If the state is not known
        """
        if (state not in ('not_processed', 'processing', 'processed') and
                not state.startswith('failed')):
            raise ValueError('Unknown state: %s' % state)
        with TRN:
            sql = """UPDATE qiita.{0} SET processing_status=%s
                     WHERE preprocessed_data_id=%s""".format(self._table)
            TRN.add(sql, [state, self.id])
            TRN.execute()

    @property
    def status(self):
        """The status of the preprocessed data

        Returns
        -------
        str
            The status of the preprocessed_data

        Notes
        -----
        The status of a preprocessed data is inferred by the status of the
        processed data generated from this preprocessed data. If no processed
        data has been generated with this preprocessed data; then the status
        is 'sandbox'.
        """
        with TRN:
            sql = """SELECT processed_data_status
                    FROM qiita.processed_data_status pds
                      JOIN qiita.processed_data pd
                        USING (processed_data_status_id)
                      JOIN qiita.preprocessed_processed_data ppd_pd
                        USING (processed_data_id)
                    WHERE ppd_pd.preprocessed_data_id=%s"""
            TRN.add(sql, [self._id])

            return infer_status(TRN.execute_fetchindex())

    @property
    def preprocessing_info(self):
        """The preprocessing information

        Returns
        -------
        tuple(str, int)
            The preprocessing parameters table and
            the preprocessing parameters id
        """
        with TRN:
            sql = """SELECT preprocessed_params_table, preprocessed_params_id
                     FROM qiita.{0}
                     WHERE preprocessed_data_id = %s""".format(self._table)
            TRN.add(sql, [self.id])
            result = TRN.execute_fetchflatten()
        return tuple(result)


class ProcessedData(BaseData):
    r"""Object for dealing with processed data

    Attributes
    ----------
    preprocessed_data
    study

    Methods
    -------
    create
    data_type

    See Also
    --------
    BaseData
    """
    # Override the class variables defined in the base classes
    _table = "processed_data"
    _data_filepath_table = "processed_filepath"
    _data_filepath_column = "processed_data_id"
    _study_processed_table = "study_processed_data"
    _preprocessed_processed_table = "preprocessed_processed_data"

    @classmethod
    def get_by_status(cls, status):
        """Returns id for all ProcessedData with given status

        Parameters
        ----------
        status : str
            Status to search for

        Returns
        -------
        list of int
            All the processed data ids that match the given status
        """
        with TRN:
            sql = """SELECT processed_data_id FROM qiita.processed_data pd
                    JOIN qiita.processed_data_status pds
                        USING (processed_data_status_id)
                    WHERE pds.processed_data_status=%s"""
            TRN.add(sql, [status])
            return set(TRN.execute_fetchflatten())

    @classmethod
    def get_by_status_grouped_by_study(cls, status):
        """Returns id for all ProcessedData with given status grouped by study

        Parameters
        ----------
        status : str
            Status to search for

        Returns
        -------
        dict of list of int
            A dictionary keyed by study id in which the values are the
            processed data ids that belong to that study and match the given
            status
        """
        with TRN:
            sql = """SELECT spd.study_id,
                array_agg(pd.processed_data_id ORDER BY pd.processed_data_id)
                FROM qiita.processed_data pd
                    JOIN qiita.processed_data_status pds
                        USING (processed_data_status_id)
                    JOIN qiita.study_processed_data spd
                        USING (processed_data_id)
                WHERE pds.processed_data_status = %s
                GROUP BY spd.study_id;"""
            TRN.add(sql, [status])
            return dict(TRN.execute_fetchindex())

    @classmethod
    def create(cls, processed_params_table, processed_params_id, filepaths,
               preprocessed_data=None, study=None, processed_date=None,
               data_type=None):
        r"""
        Parameters
        ----------
        processed_params_table : str
            Name of the table that holds the preprocessing parameters used
        processed_params_id : int
            Identifier of the parameters from the `processed_params_table`
            table used
        filepaths : iterable of tuples (str, int)
            The list of paths to the processed files and its filepath type
            identifier
        preprocessed_data : PreprocessedData, optional
            The PreprocessedData object used as base to this processed data
        study : Study, optional
            If preprocessed_data is not provided, the study the processed data
            belongs to
        processed_date : datetime, optional
            Date in which the data have been processed. Default: now
        data_type : str, optional
            data_type of the processed_data. Otherwise taken from passed
            preprocessed_data.

        Raises
        ------
        IncompetentQiitaDeveloperError
            If the table `processed_params_table` does not exists
            If `preprocessed_data` and `study` are provided at the same time
            If `preprocessed_data` and `study` are not provided
        """
        with TRN:
            if preprocessed_data is not None:
                if study is not None:
                    raise IncompetentQiitaDeveloperError(
                        "You should provide either preprocessed_data or "
                        "study, but not both")
                elif data_type is not None and \
                        data_type != preprocessed_data.data_type():
                    raise IncompetentQiitaDeveloperError(
                        "data_type passed does not match preprocessed_data "
                        "data_type!")
                else:
                    data_type = preprocessed_data.data_type(ret_id=True)
            else:
                if study is None:
                    raise IncompetentQiitaDeveloperError(
                        "You should provide either a preprocessed_data or "
                        "a study")
                if data_type is None:
                    raise IncompetentQiitaDeveloperError(
                        "You must provide either a preprocessed_data, a "
                        "data_type, or both")
                else:
                    data_type = convert_to_id(data_type, "data_type")

            # We first check that the processed_params_table exists
            if not exists_dynamic_table(processed_params_table,
                                        "processed_params_", ""):
                raise IncompetentQiitaDeveloperError(
                    "Processed params table %s does not exists!"
                    % processed_params_table)

            # Check if we have received a date:
            if processed_date is None:
                processed_date = datetime.now()

            # Add the processed data to the database,
            # and get the processed data id back
            sql = """INSERT INTO qiita.{0}
                        (processed_params_table, processed_params_id,
                         processed_date, data_type_id)
                     VALUES (%s, %s, %s, %s)
                     RETURNING processed_data_id""".format(cls._table)
            TRN.add(sql, [processed_params_table, processed_params_id,
                          processed_date, data_type])
            pd_id = TRN.execute_fetchlast()

            pd = cls(pd_id)

            if preprocessed_data is not None:
                sql = """INSERT INTO qiita.{0}
                            (preprocessed_data_id, processed_data_id)
                         VALUES (%s, %s)""".format(
                    cls._preprocessed_processed_table)
                TRN.add(sql, [preprocessed_data.id, pd_id])
                TRN.execute()
                study_id = preprocessed_data.study
            else:
                study_id = study.id

            # Connect the processed data with the study
            sql = """INSERT INTO qiita.{0} (study_id, processed_data_id)
                     VALUES (%s, %s)""".format(cls._study_processed_table)
            TRN.add(sql, [study_id, pd_id])
            TRN.execute()

            pd.add_filepaths(filepaths)
            return cls(pd_id)

    @classmethod
    def delete(cls, processed_data_id):
        """Removes the processed data with id processed_data_id

        Parameters
        ----------
        processed_data_id : int
            The processed data id

        Raises
        ------
        QiitaDBStatusError
            If the processed data status is not sandbox
        QiitaDBError
            If the processed data has analyses
        """
        with TRN:
            if cls(processed_data_id).status != 'sandbox':
                raise QiitaDBStatusError(
                    "Illegal operation on non sandboxed processed data")

            sql = """SELECT DISTINCT name
                     FROM qiita.analysis
                        JOIN qiita.analysis_sample USING (analysis_id)
                     WHERE processed_data_id = %s ORDER BY name"""
            TRN.add(sql, [processed_data_id])

            analyses = TRN.execute_fetchflatten()

            if analyses:
                raise QiitaDBError(
                    "Processed data %d cannot be removed because it is linked "
                    "to the following analysis: %s"
                    % (processed_data_id, ', '.join(analyses)))

            # delete
            sql = """DELETE FROM qiita.preprocessed_processed_data
                     WHERE processed_data_id = %s"""
            args = [processed_data_id]
            TRN.add(sql, args)

            sql = """DELETE FROM qiita.processed_filepath
                     WHERE processed_data_id = %s"""
            TRN.add(sql, args)

            sql = """DELETE FROM qiita.study_processed_data
                     WHERE processed_data_id = %s"""
            TRN.add(sql, args)

            sql = """DELETE FROM qiita.processed_data
                     WHERE processed_data_id = %s"""
            TRN.add(sql, args)

            TRN.execute()

    @property
    def preprocessed_data(self):
        r"""The preprocessed data id used to generate the processed data"""
        with TRN:
            sql = """SELECT preprocessed_data_id
                     FROM qiita.{0}
                     WHERE processed_data_id=%s""".format(
                self._preprocessed_processed_table)
            TRN.add(sql, [self._id])
            return TRN.execute_fetchlast()

    @property
    def study(self):
        r"""The ID of the study to which this processed data belongs

        Returns
        -------
        int
            The study id to which this processed data belongs"""
        with TRN:
            sql = """SELECT study_id
                     FROM qiita.{0}
                     WHERE processed_data_id=%s""".format(
                self._study_processed_table)
            TRN.add(sql, [self._id])
            return TRN.execute_fetchlast()

    def data_type(self, ret_id=False):
        """Returns the data_type or data_type_id

        Parameters
        ----------
        ret_id : bool, optional
            Return the id instead of the string, default False

        Returns
        -------
        str or int
            string value of data_type or data_type_id
        """
        with TRN:
            ret = "_id" if ret_id else ""
            sql = """SELECT d.data_type{0}
                     FROM qiita.data_type d
                        JOIN qiita.{1} p ON p.data_type_id = d.data_type_id
                     WHERE p.processed_data_id = %s""".format(ret, self._table)
            TRN.add(sql, [self._id])
            return TRN.execute_fetchlast()

    @property
    def processing_info(self):
        """Return the processing item and settings used to create the data

        Returns
        -------
        dict
            Parameter settings keyed to the parameter, along with date and
            algorithm used
        """
        with TRN:
            # Get processed date and the info for the dynamic table
            sql = """SELECT processed_date, processed_params_table,
                processed_params_id FROM qiita.{0}
                WHERE processed_data_id=%s""".format(self._table)
            TRN.add(sql, [self.id])
            static_info = TRN.execute_fetchindex()[0]

            # Get the info from the dynamic table, including reference used
            sql = """SELECT * FROM qiita.{0}
                     JOIN qiita.reference USING (reference_id)
                     WHERE processed_params_id = %s""".format(
                static_info['processed_params_table'])
            TRN.add(sql, [static_info['processed_params_id']])
            dynamic_info = dict(TRN.execute_fetchindex()[0])

            # replace reference filepath_ids with full filepaths
            # figure out what columns have filepaths and what don't
            ref_fp_cols = {'sequence_filepath', 'taxonomy_filepath',
                           'tree_filepath'}
            fp_ids = tuple(dynamic_info[col] for col in ref_fp_cols
                           if dynamic_info[col] is not None)
            # Get the filepaths and create dict of fpid to filepath
            sql = """SELECT filepath_id, filepath
                     FROM qiita.filepath
                     WHERE filepath_id IN %s"""
            TRN.add(sql, [fp_ids])
            lookup = {fp[0]: fp[1] for fp in TRN.execute_fetchindex()}
            # Loop through and replace ids
            for key in ref_fp_cols:
                if dynamic_info[key] is not None:
                    dynamic_info[key] = lookup[dynamic_info[key]]

            # add missing info to the dictionary and remove id column info
            dynamic_info['processed_date'] = static_info['processed_date']
            dynamic_info['algorithm'] = static_info[
                'processed_params_table'].split('_')[-1]
            del dynamic_info['processed_params_id']
            del dynamic_info['reference_id']

            return dynamic_info

    @property
    def samples(self):
        """Return the samples available according to prep template

        Returns
        -------
        set
            all sample_ids available for the processed data
        """
        with TRN:
            # Get the prep template id for teh dynamic table lookup
            sql = """SELECT ptp.prep_template_id
                     FROM qiita.prep_template_preprocessed_data ptp
                        JOIN qiita.preprocessed_processed_data ppd
                            USING (preprocessed_data_id)
                     WHERE ppd.processed_data_id = %s"""
            TRN.add(sql, [self._id])
            prep_id = TRN.execute_fetchlast()

            # Get samples from dynamic table
            sql = """SELECT sample_id
                     FROM qiita.prep_template_sample
                     WHERE prep_template_id=%s"""
            TRN.add(sql, [prep_id])
            return set(TRN.execute_fetchflatten())

    @property
    def status(self):
        with TRN:
            sql = """SELECT pds.processed_data_status
                    FROM qiita.processed_data_status pds
                      JOIN qiita.processed_data pd
                        USING (processed_data_status_id)
                    WHERE pd.processed_data_id=%s"""
            TRN.add(sql, [self._id])
            return TRN.execute_fetchlast()

    @status.setter
    def status(self, status):
        """Set the status value

        Parameters
        ----------
        status : str
            The new status

        Raises
        ------
        QiitaDBStatusError
            If the processed data status is public
        """
        with TRN:
            if self.status == 'public':
                raise QiitaDBStatusError(
                    "Illegal operation on public processed data")

            status_id = convert_to_id(status, 'processed_data_status')

            sql = """UPDATE qiita.{0} SET processed_data_status_id = %s
                     WHERE processed_data_id=%s""".format(self._table)
            TRN.add(sql, [status_id, self._id])
            TRN.execute()
