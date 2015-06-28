# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from future.utils import viewvalues
from itertools import chain
from os.path import join
from time import strftime
from copy import deepcopy
import warnings

import pandas as pd

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.exceptions import (QiitaDBColumnError, QiitaDBUnknownIDError,
                                 QiitaDBError, QiitaDBExecutionError,
                                 QiitaDBWarning)
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.ontology import Ontology
from qiita_db.util import (convert_to_id,
                           convert_from_id, get_mountpoint, infer_status)
from .base_metadata_template import BaseSample, MetadataTemplate
from .util import load_template_to_dataframe
from .constants import (TARGET_GENE_DATA_TYPES, PREP_TEMPLATE_COLUMNS,
                        PREP_TEMPLATE_COLUMNS_TARGET_GENE)


class PrepSample(BaseSample):
    r"""Class that models a sample present in a PrepTemplate.

    See Also
    --------
    BaseSample
    Sample
    """
    _table = "prep_template_sample"
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
    _table = "prep_template_sample"
    _table_prefix = "prep_"
    _column_table = "prep_columns"
    _id_column = "prep_template_id"
    _sample_cls = PrepSample
    _fp_id = convert_to_id("prep_template", "filepath_type")
    _filepath_table = 'prep_template_filepath'

    @classmethod
    def create(cls, md_template, study, data_type, investigation_type=None):
        r"""Creates the metadata template in the database

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by samples Ids
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
        queue_name = "CREATE_PREP_TEMPLATE_%d_%d" % (study.id, id(md_template))
        conn_handler.create_queue(queue_name)

        # Check if the data_type is the id or the string
        if isinstance(data_type, (int, long)):
            data_type_id = data_type
            data_type_str = convert_from_id(data_type, "data_type")
        else:
            data_type_id = convert_to_id(data_type, "data_type")
            data_type_str = data_type

        pt_cols = PREP_TEMPLATE_COLUMNS
        if data_type_str in TARGET_GENE_DATA_TYPES:
            pt_cols = deepcopy(PREP_TEMPLATE_COLUMNS)
            pt_cols.update(PREP_TEMPLATE_COLUMNS_TARGET_GENE)

        md_template = cls._clean_validate_template(md_template, study.id,
                                                   pt_cols)

        # Insert the metadata template
        # We need the prep_id for multiple calls below, which currently is not
        # supported by the queue system. Thus, executing this outside the queue
        prep_id = conn_handler.execute_fetchone(
            "INSERT INTO qiita.prep_template "
            "(data_type_id, investigation_type) "
            "VALUES (%s, %s) RETURNING prep_template_id",
            (data_type_id, investigation_type))[0]

        cls._add_common_creation_steps_to_queue(md_template, prep_id,
                                                conn_handler, queue_name)

        # Link the prep template with the study
        sql = ("INSERT INTO qiita.study_prep_template "
               "(study_id, prep_template_id) VALUES (%s, %s)")
        conn_handler.add_to_queue(queue_name, sql, (study.id, prep_id))

        try:
            conn_handler.execute_queue(queue_name)
        except Exception:
            # Clean up row from qiita.prep_template
            conn_handler.execute(
                "DELETE FROM qiita.prep_template where "
                "{0} = %s".format(cls._id_column), (prep_id,))

            # Check if sample IDs present here but not in sample template
            sql = ("SELECT sample_id from qiita.study_sample WHERE "
                   "study_id = %s")
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

        pt = cls(prep_id)
        pt.generate_files()

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
    def delete(cls, id_):
        r"""Deletes the table from the database

        Parameters
        ----------
        id_ : obj
            The object identifier

        Raises
        ------
        QiitaDBExecutionError
            If the prep template already has a preprocessed data
            If the prep template has a raw data attached
        QiitaDBUnknownIDError
            If no prep template with id = id_ exists
        """
        table_name = cls._table_name(id_)
        conn_handler = SQLConnectionHandler()

        if not cls.exists(id_):
            raise QiitaDBUnknownIDError(id_, cls.__name__)

        preprocessed_data_exists = conn_handler.execute_fetchone(
            "SELECT EXISTS(SELECT * FROM qiita.prep_template_preprocessed_data"
            " WHERE prep_template_id=%s)", (id_,))[0]

        if preprocessed_data_exists:
            raise QiitaDBExecutionError("Cannot remove prep template %d "
                                        "because a preprocessed data has been"
                                        " already generated using it." % id_)

        sql = """SELECT (
                    SELECT raw_data_id
                    FROM qiita.prep_template
                    WHERE prep_template_id=%s)
                IS NOT NULL"""
        raw_data_attached = conn_handler.execute_fetchone(sql, (id_,))[0]
        if raw_data_attached:
            raise QiitaDBExecutionError(
                "Cannot remove prep template %d because it has raw data "
                "associated with it" % id_)

        # Delete the prep template filepaths
        conn_handler.execute(
            "DELETE FROM qiita.prep_template_filepath WHERE "
            "prep_template_id = %s", (id_, ))

        # Drop the prep_X table
        conn_handler.execute(
            "DROP TABLE qiita.{0}".format(table_name))

        # Remove the rows from prep_template_samples
        conn_handler.execute(
            "DELETE FROM qiita.{0} where {1} = %s".format(cls._table,
                                                          cls._id_column),
            (id_,))

        # Remove the rows from prep_columns
        conn_handler.execute(
            "DELETE FROM qiita.{0} where {1} = %s".format(cls._column_table,
                                                          cls._id_column),
            (id_,))

        # Remove the row from study_prep_template
        conn_handler.execute(
            "DELETE FROM qiita.study_prep_template "
            "WHERE {0} = %s".format(cls._id_column), (id_,))

        # Remove the row from prep_template
        conn_handler.execute(
            "DELETE FROM qiita.prep_template where "
            "{0} = %s".format(cls._id_column), (id_,))

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
    def columns_restrictions(self):
        """Gets the dictionary of colums required based on data_type

        Returns
        -------
        dict
            The dict of restictions based on the data_type
        """
        pt_cols = deepcopy(PREP_TEMPLATE_COLUMNS)
        if self.data_type() in TARGET_GENE_DATA_TYPES:
            pt_cols.update(PREP_TEMPLATE_COLUMNS_TARGET_GENE)

        return pt_cols

    def can_be_updated(self, columns):
        """Gets if the template can be updated

        Parameters
        ----------
        columns : set
            A set of the names of the columns to be updated

        Returns
        -------
        bool
            If the template can be updated

        Notes
        -----
        The prep template can be updated when (1) it has no preprocessed data
        or the prep template data-type is not part of TARGET_GENE_DATA_TYPES,
        (2) if is part of TARGET_GENE_DATA_TYPES then we will only update if
        the columns being updated are not part of
        PREP_TEMPLATE_COLUMNS_TARGET_GENE
        """
        if (not self.preprocessed_data or
           self.data_type() not in TARGET_GENE_DATA_TYPES):
            return True

        tg_columns = set(chain.from_iterable(
            [v.columns for v in
             viewvalues(PREP_TEMPLATE_COLUMNS_TARGET_GENE)]))

        if not columns & tg_columns:
            return True

        return False

    @property
    def raw_data(self):
        conn_handler = SQLConnectionHandler()
        result = conn_handler.execute_fetchone(
            "SELECT raw_data_id FROM qiita.prep_template "
            "WHERE prep_template_id=%s", (self.id,))
        if result:
            return result[0]
        return None

    @raw_data.setter
    def raw_data(self, raw_data):
        conn_handler = SQLConnectionHandler()
        sql = """SELECT (
                    SELECT raw_data_id
                    FROM qiita.prep_template
                    WHERE prep_template_id=%s)
                IS NOT NULL"""
        exists = conn_handler.execute_fetchone(sql, (self.id,))[0]
        if exists:
            raise QiitaDBError(
                "Prep template %d already has a raw data associated"
                % self.id)
        sql = """UPDATE qiita.prep_template
                 SET raw_data_id = %s
                 WHERE prep_template_id = %s"""
        conn_handler.execute(sql, (raw_data.id, self.id))

    @property
    def preprocessed_data(self):
        conn_handler = SQLConnectionHandler()
        prep_datas = conn_handler.execute_fetchall(
            "SELECT preprocessed_data_id FROM "
            "qiita.prep_template_preprocessed_data WHERE prep_template_id=%s",
            (self.id,))
        return [x[0] for x in prep_datas]

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
        sql = ("SELECT study_id FROM qiita.study_prep_template "
               "WHERE prep_template_id=%s")
        study_id = conn.execute_fetchone(sql, (self.id,))
        if study_id:
            return study_id[0]
        else:
            raise QiitaDBError("No studies found associated with prep "
                               "template ID %d" % self._id)

    def generate_files(self):
        r"""Generates all the files that contain data from this template
        """
        # figuring out the filepath of the prep template
        _id, fp = get_mountpoint('templates')[0]
        fp = join(fp, '%d_prep_%d_%s.txt' % (self.study_id, self._id,
                  strftime("%Y%m%d-%H%M%S")))
        # storing the template
        self.to_file(fp)

        # adding the fp to the object
        self.add_filepath(fp)

        # creating QIIME mapping file
        self.create_qiime_mapping_file()

    def create_qiime_mapping_file(self):
        """This creates the QIIME mapping file and links it in the db.

        Returns
        -------
        filepath : str
            The filepath of the created QIIME mapping file

        Raises
        ------
        ValueError
            If the prep template is not a subset of the sample template
        QiitaDBWarning
            If the QIIME-required columns are not present in the template

        Notes
        -----
        We cannot ensure that the QIIME-required columns are present in the
        metadata map. However, we have to generate a QIIME-compliant mapping
        file. Since the user may need a QIIME mapping file, but not these
        QIIME-required columns, we are going to create them and
        populate them with the value XXQIITAXX.
        """
        rename_cols = {
            'barcode': 'BarcodeSequence',
            'primer': 'LinkerPrimerSequence',
            'description': 'Description',
        }

        if 'reverselinkerprimer' in self.categories():
            rename_cols['reverselinkerprimer'] = 'ReverseLinkerPrimer'
            new_cols = ['BarcodeSequence', 'LinkerPrimerSequence',
                        'ReverseLinkerPrimer']
        else:
            new_cols = ['BarcodeSequence', 'LinkerPrimerSequence']

        # getting the latest sample template
        conn_handler = SQLConnectionHandler()
        sql = """SELECT filepath_id, filepath
                 FROM qiita.filepath
                    JOIN qiita.sample_template_filepath
                    USING (filepath_id)
                 WHERE study_id=%s
                 ORDER BY filepath_id DESC"""
        sample_template_fname = conn_handler.execute_fetchall(
            sql, (self.study_id,))[0][1]
        _, fp = get_mountpoint('templates')[0]
        sample_template_fp = join(fp, sample_template_fname)

        # reading files via pandas
        st = load_template_to_dataframe(sample_template_fp)
        pt = self.to_dataframe()

        st_sample_names = set(st.index)
        pt_sample_names = set(pt.index)

        if not pt_sample_names.issubset(st_sample_names):
            raise ValueError(
                "Prep template is not a sub set of the sample template, files"
                "%s - samples: %s"
                % (sample_template_fp,
                   ', '.join(pt_sample_names-st_sample_names)))

        mapping = pt.join(st, lsuffix="_prep")
        mapping.rename(columns=rename_cols, inplace=True)

        # Pre-populate the QIIME-required columns with the value XXQIITAXX
        index = mapping.index
        placeholder = ['XXQIITAXX'] * len(index)
        missing = []
        for val in viewvalues(rename_cols):
            if val not in mapping:
                missing.append(val)
                mapping[val] = pd.Series(placeholder, index=index)

        if missing:
            warnings.warn(
                "Some columns required to generate a QIIME-compliant mapping "
                "file are not present in the template. A placeholder value "
                "(XXQIITAXX) has been used to populate these columns. Missing "
                "columns: %s" % ', '.join(missing),
                QiitaDBWarning)

        # Gets the orginal mapping columns and readjust the order to comply
        # with QIIME requirements
        cols = mapping.columns.values.tolist()
        cols.remove('BarcodeSequence')
        cols.remove('LinkerPrimerSequence')
        cols.remove('Description')
        new_cols.extend(cols)
        new_cols.append('Description')
        mapping = mapping[new_cols]

        # figuring out the filepath for the QIIME map file
        _id, fp = get_mountpoint('templates')[0]
        filepath = join(fp, '%d_prep_%d_qiime_%s.txt' % (self.study_id,
                        self.id, strftime("%Y%m%d-%H%M%S")))

        # Save the mapping file
        mapping.to_csv(filepath, index_label='#SampleID', na_rep='',
                       sep='\t')

        # adding the fp to the object
        self.add_filepath(
            filepath,
            fp_id=convert_to_id("qiime_map", "filepath_type"))

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

    @property
    def qiime_map_fp(self):
        """The QIIME mapping filepath attached to the prep template

        Returns
        -------
        str
            The filepath of the QIIME mapping file
        """
        conn_handler = SQLConnectionHandler()

        sql = """SELECT filepath_id, filepath
                 FROM qiita.filepath
                    JOIN qiita.{0} USING (filepath_id)
                    JOIN qiita.filepath_type USING (filepath_type_id)
                 WHERE {1} = %s AND filepath_type = 'qiime_map'
                 ORDER BY filepath_id DESC""".format(self._filepath_table,
                                                     self._id_column)
        fn = conn_handler.execute_fetchall(sql, (self._id,))[0][1]
        base_dir = get_mountpoint('templates')[0][1]
        return join(base_dir, fn)
