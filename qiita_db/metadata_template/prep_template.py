# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from future.builtins import zip
from future.utils import viewvalues
from copy import deepcopy
from os.path import join
from time import strftime

from skbio.util import find_duplicates
import pandas as pd

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.exceptions import (QiitaDBColumnError, QiitaDBUnknownIDError,
                                 QiitaDBDuplicateHeaderError, QiitaDBError,
                                 QiitaDBExecutionError)
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.ontology import Ontology
from qiita_db.util import (convert_to_id, convert_from_id, get_mountpoint,
                           infer_status)
from .base_metadata_template import BaseSample, MetadataTemplate
from .util import (as_python_types, get_invalid_sample_names, get_datatypes,
                   prefix_sample_names_with_id, load_template_to_dataframe)
from .constants import TARGET_GENE_DATA_TYPES, PREP_TEMPLATE_COLUMNS


class PrepSample(BaseSample):
    r"""Class that models a sample present in a PrepTemplate.

    See Also
    --------
    BaseSample
    Sample
    """
    _table = "common_prep_info"
    _table_prefix = "prep_"
    _column_table = "prep_columns"
    _id_column = "prep_template_id"

    def _check_template_class(self, md_template):
        r"""Checks that md_template is of the correct type

        Parameters
        ----------
        md_template : PrepTemplate
            The metadata template

        Raises
        ------
        IncompetentQiitaDeveloperError
            If `md_template` is not a PrepTemplate object
        """
        if not isinstance(md_template, PrepTemplate):
            raise IncompetentQiitaDeveloperError()


class PrepTemplate(MetadataTemplate):
    r"""Represent the PrepTemplate of a raw data. Provides access to the
    tables in the DB that holds the sample preparation information.

    See Also
    --------
    MetadataTemplate
    SampleTemplate
    """
    _table = "common_prep_info"
    _table_prefix = "prep_"
    _column_table = "prep_columns"
    _id_column = "prep_template_id"
    _sample_cls = PrepSample
    _filepath_table = "prep_template_filepath"

    @classmethod
    def create(cls, md_template, raw_data, study, data_type,
               investigation_type=None):
        r"""Creates the metadata template in the database

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by samples Ids
        raw_data : RawData
            The raw_data to which the prep template belongs to.
        study : Study
            The study to which the prep template belongs to.
        data_type : str or int
            The data_type of the prep template
        investigation_type : str, optional
            The investigation type, if relevant

        Returns
        -------
        A new instance of `cls` to access to the PrepTemplate stored in the DB

        Raises
        ------
        QiitaDBColumnError
            If the investigation_type is not valid
            If a required column is missing in md_template
        """
        # If the investigation_type is supplied, make sure it is one of
        # the recognized investigation types
        if investigation_type is not None:
            cls.validate_investigation_type(investigation_type)

        # Get a connection handler
        conn_handler = SQLConnectionHandler()
        queue_name = "CREATE_PREP_TEMPLATE_%d" % raw_data.id
        conn_handler.create_queue(queue_name)

        md_template = cls._clean_validate_template(md_template, study.id,
                                                   PREP_TEMPLATE_COLUMNS)

        # Check if the data_type is the id or the string
        data_type_id = (data_type if isinstance(data_type, (int, long))
                        else convert_to_id(data_type, "data_type",
                                           conn_handler))

        # Get some useful information from the metadata template
        sample_ids = md_template.index.tolist()
        headers = list(md_template.keys())

        # Insert the metadata template
        # We need the prep_id for multiple calls below, which currently is not
        # supported by the queue system. Thus, executing this outside the queue
        sql = """INSERT INTO qiita.prep_template
                    (data_type_id, raw_data_id, investigation_type)
                  VALUES (%s, %s, %s)
                  RETURNING prep_template_id"""
        prep_id = conn_handler.execute_fetchone(
            sql, (data_type_id, raw_data.id, investigation_type))[0]

        # Insert values on required columns
        values = [(prep_id, s_id) for s_id in sample_ids]
        sql = "INSERT INTO qiita.{0} ({1}, sample_id) VALUES (%s, %s)".format(
            cls._table, cls._id_column)
        conn_handler.add_to_queue(queue_name, sql, values, many=True)

        # Insert rows on *_columns table
        datatypes = get_datatypes(md_template.ix[:, headers])
        # psycopg2 requires a list of tuples, in which each tuple is a set
        # of values to use in the string formatting of the query. We have all
        # the values in different lists (but in the same order) so use zip
        # to create the list of tuples that psycopg2 requires.
        values = [(prep_id, h, d) for h, d in zip(headers, datatypes)]
        sql = """INSERT INTO qiita.{0} ({1}, column_name, column_type)
                 VALUES (%s, %s, %s)""".format(cls._column_table,
                                               cls._id_column)
        conn_handler.add_to_queue(queue_name, sql, values, many=True)

        # Create table with custom columns
        table_name = cls._table_name(prep_id)
        column_datatype = ["%s %s" % (col, dtype)
                           for col, dtype in zip(headers, datatypes)]
        conn_handler.add_to_queue(
            queue_name,
            "CREATE TABLE qiita.{0} (sample_id varchar, {1})".format(
                table_name, ', '.join(column_datatype)))

        # Insert values on custom table
        values = as_python_types(md_template, headers)
        values.insert(0, sample_ids)
        values = [v for v in zip(*values)]
        sql = "INSERT INTO qiita.{0} (sample_id, {1}) VALUES (%s, {2})".format(
            table_name, ", ".join(headers), ', '.join(["%s"] * len(headers)))
        conn_handler.add_to_queue(queue_name, sql, values, many=True)

        try:
            conn_handler.execute_queue(queue_name)
        except Exception:
            # Clean up row from qiita.prep_template
            conn_handler.execute(
                "DELETE FROM qiita.prep_template WHERE {0} = %s".format(
                    cls._id_column),
                (prep_id,))

            # Check if sample IDs present here but not in sample template
            sql = """SELECT sample_id FROM qiita.required_sample_info
                     WHERE study_id = %s"""
            # Get list of study sample IDs, prep template study IDs,
            # and their intersection
            prep_samples = set(md_template.index.values)
            unknown_samples = prep_samples.difference(
                s[0] for s in conn_handler.execute_fetchall(sql, [study.id]))
            if unknown_samples:
                raise QiitaDBExecutionError(
                    'Samples found in prep template but not sample template: '
                    '%s' % ', '.join(unknown_samples))

            # some other error we haven't seen before so raise it
            raise

        # figuring out the filepath of the backup
        _id, fp = get_mountpoint('templates')[0]
        fp = join(fp, '%d_prep_%d_%s.txt' % (study.id, prep_id,
                  strftime("%Y%m%d-%H%M%S")))
        # storing the backup
        pt = cls(prep_id)
        pt.to_file(fp)

        # adding the fp to the object
        pt.add_filepath(fp)

        # creating QIIME mapping file
        pt.create_qiime_mapping_file(fp)

        return pt

    @classmethod
    def validate_investigation_type(self, investigation_type):
        """Simple investigation validation to avoid code duplication

        Parameters
        ----------
        investigation_type : str
            The investigation type, should be part of the ENA ontology

        Raises
        -------
        QiitaDBColumnError
            The investigation type is not in the ENA ontology
        """
        ontology = Ontology(convert_to_id('ENA', 'ontology'))
        terms = ontology.terms + ontology.user_defined_terms
        if investigation_type not in terms:
            raise QiitaDBColumnError("'%s' is Not a valid investigation_type. "
                                     "Choose from: %s" % (investigation_type,
                                                          ', '.join(terms)))

    @classmethod
    def _delete_checks(cls, id_, conn_handler=None):
        r"""Performs the checks to know if a PrepTemplate can be deleted

        A prep template cannot be removed if a preprocessed data has been
        generated using it

        Parameters
        ----------
        id_ : int
            The prep template identifier
        conn_handler : SQLConnectionHandler, optional
            The connection handler connected to the DB

        Raises
        ------
        QiitaDBExecutionError
            Should be implemented in the subclasses
        """
        sql = """SELECT EXISTS(
                    SELECT *
                    FROM qiita.prep_template_preprocessed_data
                    WHERE prep_template_id=%s)"""
        exists = conn_handler.execute_fetchone(sql, (id_,))[0]
        if exists:
            raise QiitaDBExecutionError(
                "Cannot remove prep template %d because a preprocessed data "
                "has been already generated using it." % id_)

    @classmethod
    def _add_delete_extra_cleanup(cls, id_, conn_handler, queue):
        r"""Adds any extra needed clean up to the queue

        Parameters
        ----------
        id_ : obj id
            The object identifier
        conn_handler : SQLConnectionHandler
            The connection handler connected to the DB
        queue : str
            The queue from conn_handler to add the extra clean up sql commands
        """
        # Remove the row from prep_template
        sql = "DELETE FROM qiita.prep_template where {0} = %s".format(
            cls._id_column)
        conn_handler.add_to_queue(queue, sql, (id_,))

    def data_type(self, ret_id=False):
        """Returns the data_type or the data_type id

        Parameters
        ----------
        ret_id : bool, optional
            If true, return the id instead of the string, default false.

        Returns
        -------
        str or int
            string value of data_type or data_type_id if ret_id is True
        """
        ret = "_id" if ret_id else ""
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(
            "SELECT d.data_type{0} FROM qiita.data_type d JOIN "
            "qiita.prep_template p ON p.data_type_id = d.data_type_id WHERE "
            "p.prep_template_id=%s".format(ret), (self.id,))[0]

    @property
    def raw_data(self):
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(
            "SELECT raw_data_id FROM qiita.prep_template "
            "WHERE prep_template_id=%s", (self.id,))[0]

    @property
    def preprocessed_data(self):
        conn_handler = SQLConnectionHandler()
        prep_data = conn_handler.execute_fetchall(
            "SELECT preprocessed_data_id FROM "
            "qiita.prep_template_preprocessed_data WHERE prep_template_id=%s",
            (self.id,))
        return [x[0] for x in prep_data]

    @property
    def preprocessing_status(self):
        r"""Tells if the data has been preprocessed or not

        Returns
        -------
        str
            One of {'not_preprocessed', 'preprocessing', 'success', 'failed'}
        """
        conn_handler = SQLConnectionHandler()
        return conn_handler.execute_fetchone(
            "SELECT preprocessing_status FROM qiita.prep_template "
            "WHERE {0}=%s".format(self._id_column), (self.id,))[0]

    @preprocessing_status.setter
    def preprocessing_status(self, state):
        r"""Update the preprocessing status

        Parameters
        ----------
        state : str, {'not_preprocessed', 'preprocessing', 'success', 'failed'}
            The current status of preprocessing

        Raises
        ------
        ValueError
            If the state is not known.
        """
        if (state not in ('not_preprocessed', 'preprocessing', 'success') and
                not state.startswith('failed:')):
            raise ValueError('Unknown state: %s' % state)

        conn_handler = SQLConnectionHandler()

        conn_handler.execute(
            "UPDATE qiita.prep_template SET preprocessing_status = %s "
            "WHERE {0} = %s".format(self._id_column),
            (state, self.id))

    @property
    def investigation_type(self):
        conn_handler = SQLConnectionHandler()
        sql = ("SELECT investigation_type FROM qiita.prep_template "
               "WHERE {0} = %s".format(self._id_column))
        return conn_handler.execute_fetchone(sql, [self._id])[0]

    @investigation_type.setter
    def investigation_type(self, investigation_type):
        r"""Update the investigation type

        Parameters
        ----------
        investigation_type : str
            The investigation type to set, should be part of the ENA ontology

        Raises
        ------
        QiitaDBColumnError
            If the investigation type is not a valid ENA ontology
        """
        if investigation_type is not None:
            self.validate_investigation_type(investigation_type)

        conn_handler = SQLConnectionHandler()

        conn_handler.execute(
            "UPDATE qiita.prep_template SET investigation_type = %s "
            "WHERE {0} = %s".format(self._id_column),
            (investigation_type, self.id))

    @property
    def study_id(self):
        """Gets the study id with which this prep template is associated

        Returns
        -------
        int
            The ID of the study with which this prep template is associated
        """
        conn = SQLConnectionHandler()
        sql = ("SELECT srd.study_id FROM qiita.prep_template pt JOIN "
               "qiita.study_raw_data srd ON pt.raw_data_id = srd.raw_data_id "
               "WHERE prep_template_id = %d" % self.id)
        study_id = conn.execute_fetchone(sql)
        if study_id:
            return study_id[0]
        else:
            raise QiitaDBError("No studies found associated with prep "
                               "template ID %d" % self._id)

    def create_qiime_mapping_file(self, prep_template_fp):
        """This creates the QIIME mapping file and links it in the db.

        Parameters
        ----------
        prep_template_fp : str
            The prep template filepath that should be concatenated to the
            sample template go used to generate a new  QIIME mapping file

        Returns
        -------
        filepath : str
            The filepath of the created QIIME mapping file

        Raises
        ------
        ValueError
            If the prep template is not a subset of the sample template
        """
        rename_cols = {
            'barcode': 'BarcodeSequence',
            'primer': 'LinkerPrimerSequence',
            'description': 'Description',
        }

        # getting the latest sample template
        sql = """SELECT filepath_id, filepath
                 FROM qiita.filepath
                    JOIN qiita.sample_template_filepath
                    USING (filepath_id)
                 WHERE study_id=%s
                 ORDER BY filepath_id DESC"""
        conn_handler = SQLConnectionHandler()
        sample_template_fname = conn_handler.execute_fetchall(
            sql, (self.study_id,))[0][1]
        _, fp = get_mountpoint('templates')[0]
        sample_template_fp = join(fp, sample_template_fname)

        # reading files via pandas
        st = load_template_to_dataframe(sample_template_fp)
        pt = load_template_to_dataframe(prep_template_fp)
        st_sample_names = set(st.index)
        pt_sample_names = set(pt.index)

        if not pt_sample_names.issubset(st_sample_names):
            raise ValueError(
                "Prep template is not a sub set of the sample template, files:"
                "%s %s - samples: %s"
                % (sample_template_fp, prep_template_fp,
                   str(pt_sample_names - st_sample_names)))

        mapping = pt.join(st, lsuffix="_prep")
        mapping.rename(columns=rename_cols, inplace=True)

        # We cannot ensure that the QIIME-required columns are present in the
        # metadata map. However, we have to generate a QIIME-compliant mapping
        # file. Since the user may need a QIIME mapping file, but not these
        # QIIME-required columns, we are going to create them here and
        # populate them with the value XXQIITAXX
        index = mapping.index
        placeholder = ['XXQIITAXX'] * len(index)
        for val in viewvalues(rename_cols):
            if val not in mapping:
                mapping[val] = pd.Series(placeholder, index=index)

        # Gets the orginal mapping columns and readjust the order to comply
        # with QIIME requirements
        cols = mapping.columns.values.tolist()
        cols.remove('BarcodeSequence')
        cols.remove('LinkerPrimerSequence')
        cols.remove('Description')
        new_cols = ['BarcodeSequence', 'LinkerPrimerSequence']
        new_cols.extend(cols)
        new_cols.append('Description')
        mapping = mapping[new_cols]

        # figuring out the filepath for the QIIME map file
        filepath = join(fp, '%d_prep_%d_qiime_%s.txt' % (self.study_id,
                        self.id, strftime("%Y%m%d-%H%M%S")))

        # Save the mapping file
        mapping.to_csv(filepath, index_label='#SampleID', na_rep='unknown',
                       sep='\t')

        # adding the fp to the object
        self.add_filepath(filepath)

        return filepath

    @property
    def status(self):
        """The status of the prep template

        Returns
        -------
        str
            The status of the prep template

        Notes
        -----
        The status of a prep template is inferred by the status of the
        processed data generated from this prep template. If no processed
        data has been generated with this prep template; then the status
        is 'sandbox'.
        """
        conn_handler = SQLConnectionHandler()
        sql = """SELECT processed_data_status
                FROM qiita.processed_data_status pds
                  JOIN qiita.processed_data pd
                    USING (processed_data_status_id)
                  JOIN qiita.preprocessed_processed_data ppd_pd
                    USING (processed_data_id)
                  JOIN qiita.prep_template_preprocessed_data pt_ppd
                    USING (preprocessed_data_id)
                WHERE pt_ppd.prep_template_id=%s"""
        pd_statuses = conn_handler.execute_fetchall(sql, (self._id,))

        return infer_status(pd_statuses)
