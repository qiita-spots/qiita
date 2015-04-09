# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from future.builtins import zip
from os.path import join
from time import strftime
from os.path import basename

import pandas as pd
import warnings

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_db.exceptions import (QiitaDBDuplicateError, QiitaDBError,
                                 QiitaDBWarning)
from qiita_db.sql_connection import SQLConnectionHandler
from qiita_db.util import (get_table_cols, get_required_sample_info_status,
                           get_mountpoint, scrub_data)
from qiita_db.study import Study
from qiita_db.data import RawData
from .base_metadata_template import BaseSample, MetadataTemplate
from .util import as_python_types, get_datatypes
from .prep_template import PrepTemplate


class Sample(BaseSample):
    r"""Class that models a sample present in a SampleTemplate.

    See Also
    --------
    BaseSample
    PrepSample
    """
    _table = "required_sample_info"
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


class SampleTemplate(MetadataTemplate):
    r"""Represent the SampleTemplate of a study. Provides access to the
    tables in the DB that holds the sample metadata information.

    See Also
    --------
    MetadataTemplate
    PrepTemplate
    """
    _table = "required_sample_info"
    _table_prefix = "sample_"
    _column_table = "study_sample_columns"
    _id_column = "study_id"
    translate_cols_dict = {
        'required_sample_info_status_id': 'required_sample_info_status'}
    id_cols_handlers = {
        'required_sample_info_status_id': get_required_sample_info_status()}
    str_cols_handlers = {
        'required_sample_info_status_id': get_required_sample_info_status(
            key='required_sample_info_status_id')}
    _sample_cls = Sample

    @staticmethod
    def metadata_headers():
        """Returns metadata headers available

        Returns
        -------
        list
            Alphabetical list of all metadata headers available
        """
        conn_handler = SQLConnectionHandler()
        return [x[0] for x in
                conn_handler.execute_fetchall(
                "SELECT DISTINCT column_name FROM qiita.study_sample_columns "
                "UNION SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'required_sample_info' "
                "ORDER BY column_name")]

    @classmethod
    def _check_template_special_columns(cls, md_template, study_id):
        r"""Checks for special columns based on obj type

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by sample ids
        study_id : int
            The study to which the sample template belongs to.
        """
        return set()

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
        cls._check_subclass()

        # Check that we don't have a MetadataTemplate for study
        if cls.exists(study.id):
            raise QiitaDBDuplicateError(cls.__name__, 'id: %d' % study.id)

        conn_handler = SQLConnectionHandler()
        queue_name = "CREATE_SAMPLE_TEMPLATE_%d" % study.id
        conn_handler.create_queue(queue_name)

        # Clean and validate the metadata template given
        md_template = cls._clean_validate_template(md_template, study.id,
                                                   study.id, conn_handler)

        cls._add_common_creation_steps_to_queue(md_template, study.id,
                                                conn_handler, queue_name)

        conn_handler.execute_queue(queue_name)

        # figuring out the filepath of the backup
        _id, fp = get_mountpoint('templates')[0]
        fp = join(fp, '%d_%s.txt' % (study.id, strftime("%Y%m%d-%H%M%S")))
        # storing the backup
        st = cls(study.id)
        st.to_file(fp)

        # adding the fp to the object
        st.add_filepath(fp)

        return st

    @property
    def study_id(self):
        """Gets the study id with which this sample template is associated

        Returns
        -------
        int
            The ID of the study with which this sample template is associated
        """
        return self._id

    def extend(self, md_template):
        """Adds the given sample template to the current one

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by samples Ids
        """
        conn_handler = SQLConnectionHandler()
        queue_name = "EXTEND_SAMPLE_TEMPLATE_%d" % self.id
        conn_handler.create_queue(queue_name)

        md_template = self._clean_validate_template(md_template, self.study_id,
                                                    conn_handler)

        # Raise warning and filter out existing samples
        sample_ids = md_template.index.tolist()
        sql = ("SELECT sample_id FROM qiita.required_sample_info WHERE "
               "study_id = %d" % self.id)
        curr_samples = set(s[0] for s in conn_handler.execute_fetchall(sql))
        existing_samples = curr_samples.intersection(sample_ids)
        if existing_samples:
            warnings.warn(
                "The following samples already exist and will be ignored: "
                "%s" % ", ".join(curr_samples.intersection(
                                 sorted(existing_samples))), QiitaDBWarning)
            md_template.drop(existing_samples, inplace=True)

        # Get some useful information from the metadata template
        sample_ids = md_template.index.tolist()
        num_samples = len(sample_ids)
        headers = list(md_template.keys())

        # Get the required columns from the DB
        db_cols = get_table_cols(self._table, conn_handler)
        # Remove the sample_id and study_id columns
        db_cols.remove('sample_id')
        db_cols.remove(self._id_column)

        # Insert values on required columns
        values = as_python_types(md_template, db_cols)
        values.insert(0, sample_ids)
        values.insert(0, [self.study_id] * num_samples)
        values = [v for v in zip(*values)]
        conn_handler.add_to_queue(
            queue_name,
            "INSERT INTO qiita.{0} ({1}, sample_id, {2}) "
            "VALUES (%s, %s, {3})".format(self._table, self._id_column,
                                          ', '.join(db_cols),
                                          ', '.join(['%s'] * len(db_cols))),
            values, many=True)

        # Add missing columns to the sample template dynamic table
        headers = list(set(headers).difference(db_cols))
        datatypes = get_datatypes(md_template.ix[:, headers])
        table_name = self._table_name(self.study_id)
        new_cols = set(md_template.columns).difference(
            set(self.metadata_headers()))
        dtypes_dict = dict(zip(md_template.ix[:, headers], datatypes))
        for category in new_cols:
            # Insert row on *_columns table
            conn_handler.add_to_queue(
                queue_name,
                "INSERT INTO qiita.{0} ({1}, column_name, column_type) "
                "VALUES (%s, %s, %s)".format(self._column_table,
                                             self._id_column),
                (self.study_id, category, dtypes_dict[category]))
            # Insert row on dynamic table
            conn_handler.add_to_queue(
                queue_name,
                "ALTER TABLE qiita.{0} ADD COLUMN {1} {2}".format(
                    table_name, scrub_data(category), dtypes_dict[category]))

        # Insert values on custom table
        values = as_python_types(md_template, headers)
        values.insert(0, sample_ids)
        values = [v for v in zip(*values)]
        conn_handler.add_to_queue(
            queue_name,
            "INSERT INTO qiita.{0} (sample_id, {1}) "
            "VALUES (%s, {2})".format(table_name, ", ".join(headers),
                                      ', '.join(["%s"] * len(headers))),
            values, many=True)
        conn_handler.execute_queue(queue_name)

        # figuring out the filepath of the backup
        _id, fp = get_mountpoint('templates')[0]
        fp = join(fp, '%d_%s.txt' % (self.id, strftime("%Y%m%d-%H%M%S")))
        # storing the backup
        self.to_file(fp)

        # adding the fp to the object
        self.add_filepath(fp)

    def update(self, md_template):
        r"""Update values in the sample template

        Parameters
        ----------
        md_template : DataFrame
            The metadata template file contents indexed by samples Ids

        Raises
        ------
        QiitaDBError
            If md_template and db do not have the same sample ids
            If md_template and db do not have the same column headers
        """
        conn_handler = SQLConnectionHandler()

        # Clean and validate the metadata template given
        new_map = self._clean_validate_template(md_template, self.id,
                                                conn_handler)
        # Retrieving current metadata
        current_map = self._transform_to_dict(conn_handler.execute_fetchall(
            "SELECT * FROM qiita.{0} WHERE {1}=%s".format(self._table,
                                                          self._id_column),
            (self.id,)))
        dyn_vals = self._transform_to_dict(conn_handler.execute_fetchall(
            "SELECT * FROM qiita.{0}".format(self._table_name(self.id))))

        for k in current_map:
            current_map[k].update(dyn_vals[k])
            current_map[k].pop('study_id', None)

        # converting sql results to dataframe
        current_map = pd.DataFrame.from_dict(current_map, orient='index')

        # simple validations of sample ids and column names
        samples_diff = set(
            new_map.index.tolist()) - set(current_map.index.tolist())
        if samples_diff:
            raise QiitaDBError('The new sample template differs from what is '
                               'stored in database by these samples names: %s'
                               % ', '.join(samples_diff))
        columns_diff = set(new_map.columns) - set(current_map.columns)
        if columns_diff:
            raise QiitaDBError('The new sample template differs from what is '
                               'stored in database by these columns names: %s'
                               % ', '.join(columns_diff))

        # here we are comparing two dataframes following:
        # http://stackoverflow.com/a/17095620/4228285
        current_map.sort(axis=0, inplace=True)
        current_map.sort(axis=1, inplace=True)
        new_map.sort(axis=0, inplace=True)
        new_map.sort(axis=1, inplace=True)
        map_diff = (current_map != new_map).stack()
        map_diff = map_diff[map_diff]
        map_diff.index.names = ['id', 'column']
        changed_cols = map_diff.index.get_level_values('column').unique()

        for col in changed_cols:
            self.update_category(col, new_map[col].to_dict())

        # figuring out the filepath of the backup
        _id, fp = get_mountpoint('templates')[0]
        fp = join(fp, '%d_%s.txt' % (self.id, strftime("%Y%m%d-%H%M%S")))
        # storing the backup
        self.to_file(fp)

        # adding the fp to the object
        self.add_filepath(fp)

        # generating all new QIIME mapping files
        for rd_id in Study(self.id).raw_data():
            for pt_id in RawData(rd_id).prep_templates:
                pt = PrepTemplate(pt_id)
                for _, fp in pt.get_filepaths():
                    # the difference between a prep and a qiime template is the
                    # word qiime within the name of the file
                    if '_qiime_' not in basename(fp):
                        pt.create_qiime_mapping_file(fp)

    def add_category(self, category, samples_and_values, dtype, default):
        """Add a metadata category

        Parameters
        ----------
        category : str
            The category to add
        samples_and_values : dict
            A mapping of {sample_id: value}
        dtype : str
            The datatype of the column
        default : object
            The default value associated with the column. This must be
            specified as these columns are added "not null".

        Raises
        ------
        QiitaDBDuplicateError
            If the column already exists
        """
        table_name = self._table_name(self.study_id)
        conn_handler = SQLConnectionHandler()

        if category in self.categories():
            raise QiitaDBDuplicateError(category, "N/A")

        conn_handler.execute("""
            ALTER TABLE qiita.{0}
            ADD COLUMN {1} {2}
            NOT NULL DEFAULT '{3}'""".format(table_name, category, dtype,
                                             default))

        self.update_category(category, samples_and_values)
