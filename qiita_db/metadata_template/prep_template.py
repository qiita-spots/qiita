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
from skbio.util import find_duplicates

import pandas as pd

from qiita_core.exceptions import IncompetentQiitaDeveloperError
import qiita_db as qdb
from .constants import (PREP_TEMPLATE_COLUMNS, TARGET_GENE_DATA_TYPES,
                        PREP_TEMPLATE_COLUMNS_TARGET_GENE)
from .base_metadata_template import BaseSample, MetadataTemplate


def _check_duplicated_columns(prep_cols, sample_cols):
    r"""Check for duplicated colums in the prep_cols and sample_cols

    Parameters
    ----------
    prep_cols : list of str
        Column names in the prep info file
    sample_cols : list of str
        Column names in the sample info file

    Raises
    ------
    QiitaDBColumnError
        If there are duplicated columns names in the sample and the prep
    """
    prep_cols.extend(sample_cols)
    dups = find_duplicates(prep_cols)
    if dups:
        raise qdb.exceptions.QiitaDBColumnError(
            'Duplicated column names in the sample and prep info '
            'files: %s. You need to delete that duplicated field' %
            ','.join(dups))


class PrepSample(BaseSample):
    r"""Class that models a sample present in a PrepTemplate.

    See Also
    --------
    BaseSample
    Sample
    """
    _table = "prep_template_sample"
    _table_prefix = "prep_"
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
    _id_column = "prep_template_id"
    _sample_cls = PrepSample
    _filepath_table = 'prep_template_filepath'

    @classmethod
    def create(cls, md_template, study, data_type, investigation_type=None,
               name=None):
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
        name : str, optional
            The prep template name

        Returns
        -------
        A new instance of `cls` to access to the PrepTemplate stored in the DB

        Raises
        ------
        QiitaDBColumnError
            If the investigation_type is not valid
            If a required column is missing in md_template
        """
        with qdb.sql_connection.TRN:
            # If the investigation_type is supplied, make sure it is one of
            # the recognized investigation types
            if investigation_type is not None:
                cls.validate_investigation_type(investigation_type)

            # Check if the data_type is the id or the string
            if isinstance(data_type, (int, long)):
                data_type_id = data_type
                data_type_str = qdb.util.convert_from_id(data_type,
                                                         "data_type")
            else:
                data_type_id = qdb.util.convert_to_id(data_type, "data_type")
                data_type_str = data_type

            pt_cols = PREP_TEMPLATE_COLUMNS
            if data_type_str in TARGET_GENE_DATA_TYPES:
                pt_cols = deepcopy(PREP_TEMPLATE_COLUMNS)
                pt_cols.update(PREP_TEMPLATE_COLUMNS_TARGET_GENE)

            md_template = cls._clean_validate_template(md_template, study.id)
            _check_duplicated_columns(list(md_template.columns),
                                      study.sample_template.categories())

            # Insert the metadata template
            sql = """INSERT INTO qiita.prep_template
                        (data_type_id, investigation_type)
                     VALUES (%s, %s)
                     RETURNING prep_template_id"""
            qdb.sql_connection.TRN.add(sql, [data_type_id, investigation_type])
            prep_id = qdb.sql_connection.TRN.execute_fetchlast()

            try:
                cls._common_creation_steps(md_template, prep_id)
            except Exception:
                # Check if sample IDs present here but not in sample template
                sql = """SELECT sample_id from qiita.study_sample
                         WHERE study_id = %s"""
                # Get list of study sample IDs, prep template study IDs,
                # and their intersection
                qdb.sql_connection.TRN.add(sql, [study.id])
                prep_samples = set(md_template.index.values)
                unknown_samples = prep_samples.difference(
                    qdb.sql_connection.TRN.execute_fetchflatten())
                if unknown_samples:
                    raise qdb.exceptions.QiitaDBExecutionError(
                        'Samples found in prep template but not sample '
                        'template: %s' % ', '.join(unknown_samples))

                # some other error we haven't seen before so raise it
                raise

            # Link the prep template with the study
            sql = """INSERT INTO qiita.study_prep_template
                        (study_id, prep_template_id)
                     VALUES (%s, %s)"""
            qdb.sql_connection.TRN.add(sql, [study.id, prep_id])

            qdb.sql_connection.TRN.execute()

            pt = cls(prep_id)
            pt.validate(pt_cols)
            pt.generate_files()

            # Add the name to the prep information
            pt.name = (name if name is not None
                       else "Prep information %s" % pt.id)

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
        with qdb.sql_connection.TRN:
            ontology = qdb.ontology.Ontology(
                qdb.util.convert_to_id('ENA', 'ontology'))
            terms = ontology.terms + ontology.user_defined_terms
            if investigation_type not in terms:
                raise qdb.exceptions.QiitaDBColumnError(
                    "'%s' is Not a valid investigation_type. Choose from: %s"
                    % (investigation_type, ', '.join(terms)))

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
            If the prep template already has an artifact attached
        QiitaDBUnknownIDError
            If no prep template with id = id_ exists
        """
        with qdb.sql_connection.TRN:
            table_name = cls._table_name(id_)

            if not cls.exists(id_):
                raise qdb.exceptions.QiitaDBUnknownIDError(id_, cls.__name__)

            sql = """SELECT (
                        SELECT artifact_id
                        FROM qiita.prep_template
                        WHERE prep_template_id=%s)
                    IS NOT NULL"""
            args = [id_]
            qdb.sql_connection.TRN.add(sql, args)
            artifact_attached = qdb.sql_connection.TRN.execute_fetchlast()
            if artifact_attached:
                raise qdb.exceptions.QiitaDBExecutionError(
                    "Cannot remove prep template %d because it has an artifact"
                    " associated with it" % id_)

            # Delete the prep template filepaths
            sql = """DELETE FROM qiita.prep_template_filepath
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, args)

            # Drop the prep_X table
            sql = "DROP TABLE qiita.{0}".format(table_name)
            qdb.sql_connection.TRN.add(sql)

            # Remove the rows from prep_template_samples
            sql = "DELETE FROM qiita.{0} WHERE {1} = %s".format(
                cls._table, cls._id_column)
            qdb.sql_connection.TRN.add(sql, args)

            # Remove the row from study_prep_template
            sql = """DELETE FROM qiita.study_prep_template
                     WHERE {0} = %s""".format(cls._id_column)
            qdb.sql_connection.TRN.add(sql, args)

            # Remove the row from prep_template
            sql = "DELETE FROM qiita.prep_template WHERE {0} = %s".format(
                cls._id_column)
            qdb.sql_connection.TRN.add(sql, args)

            qdb.sql_connection.TRN.execute()

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
        with qdb.sql_connection.TRN:
            ret = "_id" if ret_id else ""
            sql = """SELECT d.data_type{0}
                     FROM qiita.data_type d
                        JOIN qiita.prep_template p
                            ON p.data_type_id = d.data_type_id
                     WHERE p.prep_template_id=%s""".format(ret)
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

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
        """Whether the template can be updated or not

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
        with qdb.sql_connection.TRN:
            if self.data_type() not in TARGET_GENE_DATA_TYPES:
                return True

            artifact = self.artifact
            if not artifact:
                return True

            sql = """SELECT EXISTS(SELECT *
                                   FROM qiita.parent_artifact
                                   WHERE parent_id = %s)"""
            qdb.sql_connection.TRN.add(sql, [artifact.id])
            if not qdb.sql_connection.TRN.execute_fetchlast():
                return True

            tg_columns = set(chain.from_iterable(
                [v.columns for v in
                 viewvalues(PREP_TEMPLATE_COLUMNS_TARGET_GENE)]))

            if not columns & tg_columns:
                return True

            return False

    def can_be_extended(self, new_samples, new_columns):
        """Whether the template can be extended or not

        Parameters
        ----------
        new_samples : list of str
            The new samples to be added to the template
        new_columns : list of str
            The new columns to be added to the template

        Returns
        -------
        bool
            Whether the template can be extended or not
        str
            The error message in case that it can't be extended

        Notes
        -----
        New samples can't be added to the prep template if a preprocessed
        data has been already generated.
        """
        if new_samples:
            with qdb.sql_connection.TRN:
                artifact = self.artifact
                if artifact:
                    sql = """SELECT EXISTS(SELECT *
                                           FROM qiita.parent_artifact
                                           WHERE parent_id = %s)"""
                    qdb.sql_connection.TRN.add(sql, [artifact.id])
                    if qdb.sql_connection.TRN.execute_fetchlast():
                        return False, ("The artifact attached to the prep "
                                       "template has already been processed. "
                                       "No new samples can be added to the "
                                       "prep template")

        _check_duplicated_columns(list(new_columns), qdb.study.Study(
            self.study_id).sample_template.categories())

        return True, ""

    @property
    def artifact(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT artifact_id
                     FROM qiita.prep_template
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            result = qdb.sql_connection.TRN.execute_fetchlast()
            if result:
                return qdb.artifact.Artifact(result)
            return None

    @artifact.setter
    def artifact(self, artifact):
        with qdb.sql_connection.TRN:
            sql = """SELECT (SELECT artifact_id
                             FROM qiita.prep_template
                             WHERE prep_template_id = %s)
                     IS NOT NULL"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            if qdb.sql_connection.TRN.execute_fetchlast():
                raise qdb.exceptions.QiitaDBError(
                    "Prep template %d already has an artifact associated"
                    % self.id)
            sql = """UPDATE qiita.prep_template
                     SET artifact_id = %s
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [artifact.id, self.id])
            qdb.sql_connection.TRN.execute()

    @property
    def investigation_type(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT investigation_type FROM qiita.prep_template
                     WHERE {0} = %s""".format(self._id_column)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

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
        with qdb.sql_connection.TRN:
            if investigation_type is not None:
                self.validate_investigation_type(investigation_type)

            sql = """UPDATE qiita.prep_template SET investigation_type = %s
                     WHERE {0} = %s""".format(self._id_column)
            qdb.sql_connection.TRN.add(sql, [investigation_type, self.id])
            qdb.sql_connection.TRN.execute()

    @property
    def study_id(self):
        """Gets the study id with which this prep template is associated

        Returns
        -------
        int
            The ID of the study with which this prep template is associated
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT study_id FROM qiita.study_prep_template
                     WHERE prep_template_id=%s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    def generate_files(self):
        r"""Generates all the files that contain data from this template
        """
        with qdb.sql_connection.TRN:
            # figuring out the filepath of the prep template
            _id, fp = qdb.util.get_mountpoint('templates')[0]
            fp = join(fp, '%d_prep_%d_%s.txt' % (self.study_id, self._id,
                      strftime("%Y%m%d-%H%M%S")))
            # storing the template
            self.to_file(fp)

            # adding the fp to the object
            fp_id = qdb.util.convert_to_id("prep_template", "filepath_type")
            self.add_filepath(fp, fp_id=fp_id)

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
        with qdb.sql_connection.TRN:
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

            # Retrieve the latest sample template
            # Since we sorted the filepath retrieval, the first result contains
            # the filepath that we want. `retrieve_filepaths` returns a
            # 3-tuple, in which the fp is the second element
            sample_template_fp = qdb.util.retrieve_filepaths(
                "sample_template_filepath", "study_id", self.study_id,
                sort='descending')[0][1]

            # reading files via pandas
            st = qdb.metadata_template.util.load_template_to_dataframe(
                sample_template_fp)
            pt = self.to_dataframe()

            st_sample_names = set(st.index)
            pt_sample_names = set(pt.index)

            if not pt_sample_names.issubset(st_sample_names):
                raise ValueError(
                    "Prep template is not a sub set of the sample template, "
                    "file: %s - samples: %s"
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
                    "Some columns required to generate a QIIME-compliant "
                    "mapping file are not present in the template. A "
                    "placeholder value (XXQIITAXX) has been used to populate "
                    "these columns. Missing columns: %s"
                    % ', '.join(sorted(missing)),
                    qdb.exceptions.QiitaDBWarning)

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
            _id, fp = qdb.util.get_mountpoint('templates')[0]
            filepath = join(fp, '%d_prep_%d_qiime_%s.txt' % (self.study_id,
                            self.id, strftime("%Y%m%d-%H%M%S")))

            # Save the mapping file
            mapping.to_csv(filepath, index_label='#SampleID', na_rep='',
                           sep='\t', encoding='utf-8')

            # adding the fp to the object
            self.add_filepath(
                filepath,
                fp_id=qdb.util.convert_to_id("qiime_map", "filepath_type"))

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
        with qdb.sql_connection.TRN:
            sql = """SELECT visibility
                     FROM qiita.prep_template
                        JOIN qiita.artifact USING (artifact_id)
                        JOIN qiita.visibility USING (visibility_id)
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self._id])

            return qdb.util.infer_status(
                qdb.sql_connection.TRN.execute_fetchindex())

    @property
    def qiime_map_fp(self):
        """The QIIME mapping filepath attached to the prep template

        Returns
        -------
        str
            The filepath of the QIIME mapping file
        """
        for _, fp, fp_type in qdb.util.retrieve_filepaths(
                self._filepath_table, self._id_column, self.id,
                sort='descending'):
            if fp_type == 'qiime_map':
                return fp

    @property
    def ebi_experiment_accessions(self):
        """The EBI experiment accessions for the samples in the prep template

        Returns
        -------
        dict of {str: str}
            The EBI experiment accessions numbers keyed by sample id
        """
        return self._get_accession_numbers('ebi_experiment_accession')

    @ebi_experiment_accessions.setter
    def ebi_experiment_accessions(self, value):
        """Sets the EBI experiment accessions

        Parameters
        ----------
        values : dict of {str: str}
            The EBI experiment accessions, keyed by sample id

        Raises
        ------
        QiitaDBError
            If a sample in `value` already has an accession number
        """
        self._update_accession_numbers('ebi_experiment_accession', value)

    @property
    def is_submitted_to_ebi(self):
        """Inquires if the prep template has been submitted to EBI or not

        Returns
        -------
        bool
            True if the prep template has been submitted to EBI,
            false otherwise
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(
                        SELECT sample_id, ebi_experiment_accession
                        FROM qiita.{0}
                        WHERE {1}=%s
                            AND ebi_experiment_accession IS NOT NULL)
                  """.format(self._table, self._id_column)
            qdb.sql_connection.TRN.add(sql, [self.id])
            is_submitted = qdb.sql_connection.TRN.execute_fetchlast()
        return is_submitted

    def delete_sample(self, sample_name):
        """Delete `sample_name` from prep information file

        Parameters
        ----------
        sample_name : str
            The sample name to be deleted

        Raises
        ------
        QiitaDBColumnError
            If the prep info file has been processed
        """
        if self.artifact:
            raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                "Prep info file '%d' has files attached, you cannot delete "
                "samples." % (self._id))

        self._common_delete_sample_steps(sample_name)

    @property
    def name(self):
        """The name of the prep information

        Returns
        -------
        str
            The name of the prep information
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT name
                     FROM qiita.prep_template
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @name.setter
    def name(self, value):
        """Changes the name of the prep template"""
        with qdb.sql_connection.TRN:
            sql = """UPDATE qiita.prep_template
                     SET name = %s
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [value, self.id])
            qdb.sql_connection.TRN.execute()
