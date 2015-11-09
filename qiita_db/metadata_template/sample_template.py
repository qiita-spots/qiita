# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from os.path import join
from time import strftime

from qiita_core.exceptions import IncompetentQiitaDeveloperError

import qiita_db as qdb


class Sample(qdb.metadata_template.base_metadata_template.BaseSample):
    r"""Class that models a sample present in a SampleTemplate.

    See Also
    --------
    BaseSample
    PrepSample
    """
    _table = "study_sample"
    _table_prefix = "sample_"
    _column_table = "study_sample_columns"
    _id_column = "study_id"

    def _check_template_class(self, md_template):
        r"""Checks that md_template is of the correct type

        Parameters
        ----------
        md_template : SampleTemplate
            The metadata template

        Raises
        ------
        IncompetentQiitaDeveloperError
            If `md_template` is not a SampleTemplate object
        """
        if not isinstance(md_template, SampleTemplate):
            raise IncompetentQiitaDeveloperError()


class SampleTemplate(
        qdb.metadata_template.base_metadata_template.MetadataTemplate):
    r"""Represent the SampleTemplate of a study. Provides access to the
    tables in the DB that holds the sample metadata information.

    See Also
    --------
    MetadataTemplate
    PrepTemplate
    """
    _table = "study_sample"
    _table_prefix = "sample_"
    _column_table = "study_sample_columns"
    _id_column = "study_id"
    _sample_cls = Sample
    _fp_id = qdb.util.convert_to_id("sample_template", "filepath_type")
    _filepath_table = 'sample_template_filepath'

    @staticmethod
    def metadata_headers():
        """Returns metadata headers available

        Returns
        -------
        list
            Alphabetical list of all metadata headers available
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT DISTINCT column_name
                     FROM qiita.study_sample_columns ORDER BY column_name"""
            qdb.sql_connection.TRN.add(sql)
            return qdb.sql_connection.TRN.execute_fetchflatten()

    @classmethod
    def create(cls, md_template, study):
        r"""Creates the sample template in the database

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by samples Ids
        study : Study
            The study to which the sample template belongs to.
        """
        with qdb.sql_connection.TRN:
            cls._check_subclass()

            # Check that we don't have a MetadataTemplate for study
            if cls.exists(study.id):
                raise qdb.exceptions.QiitaDBDuplicateError(
                    cls.__name__, 'id: %d' % study.id)

            # Clean and validate the metadata template given
            md_template = cls._clean_validate_template(
                md_template, study.id,
                qdb.metadata_template.constants.SAMPLE_TEMPLATE_COLUMNS)

            cls._common_creation_steps(md_template, study.id)

            st = cls(study.id)
            st.generate_files()

            return st

    @classmethod
    def delete(cls, id_):
        r"""Deletes the table from the database

        Parameters
        ----------
        id_ : integer
            The object identifier

        Raises
        ------
        QiitaDBUnknownIDError
            If no sample template with id id_ exists
        QiitaDBError
            If the study that owns this sample template has raw datas
        """
        with qdb.sql_connection.TRN:
            cls._check_subclass()

            if not cls.exists(id_):
                raise qdb.exceptions.QiitaDBUnknownIDError(id_, cls.__name__)

            # Check if there is any PrepTemplate
            sql = """SELECT EXISTS(SELECT * FROM qiita.study_prep_template
                                   WHERE study_id=%s)"""
            qdb.sql_connection.TRN.add(sql, [id_])
            has_prep_templates = qdb.sql_connection.TRN.execute_fetchlast()
            if has_prep_templates:
                raise qdb.exceptions.QiitaDBError(
                    "Sample template can not be erased because there are prep "
                    "templates associated.")

            table_name = cls._table_name(id_)

            # Delete the sample template filepaths
            sql = """DELETE FROM qiita.sample_template_filepath
                     WHERE study_id = %s"""
            args = [id_]
            qdb.sql_connection.TRN.add(sql, args)

            sql = "DROP TABLE qiita.{0}".format(table_name)
            qdb.sql_connection.TRN.add(sql)

            sql = "DELETE FROM qiita.{0} WHERE {1} = %s".format(
                cls._table, cls._id_column)
            qdb.sql_connection.TRN.add(sql, args)

            sql = "DELETE FROM qiita.{0} WHERE {1} = %s".format(
                cls._column_table, cls._id_column)
            qdb.sql_connection.TRN.add(sql, args)

            qdb.sql_connection.TRN.execute()

    @property
    def study_id(self):
        """Gets the study id with which this sample template is associated

        Returns
        -------
        int
            The ID of the study with which this sample template is associated
        """
        return self._id

    @property
    def columns_restrictions(self):
        """Gets the dictionary of colums required

        Returns
        -------
        dict
            The dict of restictions
        """
        return qdb.metadata_template.constants.SAMPLE_TEMPLATE_COLUMNS

    def can_be_updated(self, **kwargs):
        """Whether the template can be updated or not

        Parameters
        ----------
        kwargs : ignored
            Necessary to have in parameters to support other objects.

        Returns
        -------
        bool
            As this is the sample template, it will always return True. See the
            notes.

        Notes
        -----
        The prep template can't be updated in certain situations, see the
        its documentation for more info. However, the sample template
        doesn't have those restrictions. Thus, to be able to use the same
        update code in the base class, we need to have this method and it
        should always return True.
        """
        return True

    def can_be_extended(self, new_samples, new_columns):
        """Whether the template can be updated or not

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
        The prep template can't be extended in certain situations, see the
        its documentation for more info. However, the sample template
        doesn't have those restrictions. Thus, to be able to use the same
        extend code in the base class, we need to have this method and it
        should always return True.
        """
        return True, ""

    def generate_files(self):
        r"""Generates all the files that contain data from this template
        """
        with qdb.sql_connection.TRN:
            # figuring out the filepath of the sample template
            _id, fp = qdb.util.get_mountpoint('templates')[0]
            fp = join(fp, '%d_%s.txt' % (self.id, strftime("%Y%m%d-%H%M%S")))
            # storing the sample template
            self.to_file(fp)

            # adding the fp to the object
            self.add_filepath(fp)

            # generating all new QIIME mapping files
            for pt_id in qdb.study.Study(self._id).prep_templates():
                qdb.metadata_template.prep_template.PrepTemplate(
                    pt_id).generate_files()

    @property
    def ebi_sample_accessions(self):
        """The EBI sample accessions for the samples in the sample template

        Returns
        -------
        dict of {str: str}
            The EBI sample accession numbers keyed by sample id
        """
        return self._get_accession_numbers('ebi_sample_accession')

    @ebi_sample_accessions.setter
    def ebi_sample_accessions(self, value):
        """Sets the EBI sample accessions

        Parameters
        ----------
        values : dict of {str: str}
            The EBI sample accessions, keyed by sample id

        Raises
        ------
        QiitaDBError
            If a sample in `value` already has an accession number
        """
        self._update_accession_numbers('ebi_sample_accession', value)

    @property
    def biosample_accessions(self):
        """The biosample accessions for the samples in the sample template

        Returns
        -------
        dict of {str: str}
            The biosample accession numbers keyed by sample id
        """
        return self._get_accession_numbers('biosample_accession')

    @biosample_accessions.setter
    def biosample_accessions(self, value):
        """Sets the biosample accessions

        Parameters
        ----------
        values : dict of {str: str}
            The biosample accessions, keyed by sample id

        Raises
        ------
        QiitaDBError
            If a sample in `value` already has an accession number
        """
        self._update_accession_numbers('biosample_accession', value)
