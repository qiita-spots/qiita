# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from copy import deepcopy
from itertools import chain
from os.path import join

from iteration_utilities import duplicates

import qiita_db as qdb
from qiita_core.exceptions import IncompetentQiitaDeveloperError

from .base_metadata_template import QIITA_COLUMN_NAME, BaseSample, MetadataTemplate
from .constants import (
    PREP_TEMPLATE_COLUMNS,
    PREP_TEMPLATE_COLUMNS_TARGET_GENE,
    TARGET_GENE_DATA_TYPES,
)


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
    dups = set(duplicates(prep_cols))
    if dups:
        raise qdb.exceptions.QiitaDBColumnError(
            "Duplicated column names in the sample and prep info "
            "files: %s. You need to delete that duplicated field" % ",".join(dups)
        )


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
    _filepath_table = "prep_template_filepath"
    _forbidden_words = {
        "sampleid",
        "qiita_study_id",
        "qiita_prep_id",
        QIITA_COLUMN_NAME,
    }

    @classmethod
    def create(
        cls,
        md_template,
        study,
        data_type,
        investigation_type=None,
        name=None,
        creation_job_id=None,
    ):
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
        creation_job_id : str, optional
            The prep template creation_job_id

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
            # Check if the data_type is the id or the string
            if isinstance(data_type, int):
                data_type_id = data_type
                data_type_str = qdb.util.convert_from_id(data_type, "data_type")
            else:
                data_type_id = qdb.util.convert_to_id(data_type, "data_type")
                data_type_str = data_type

            # If the investigation_type is None let's add it based on the
            # data_type being created - if possible
            if investigation_type is None:
                if data_type_str in TARGET_GENE_DATA_TYPES:
                    investigation_type = "AMPLICON"
                elif data_type_str == "Metagenomic":
                    investigation_type = "WGS"
                elif data_type_str == "Metatranscriptomic":
                    investigation_type = "RNA-Seq"
            if investigation_type is not None:
                cls.validate_investigation_type(investigation_type)

            pt_cols = PREP_TEMPLATE_COLUMNS
            if data_type_str in TARGET_GENE_DATA_TYPES:
                pt_cols = deepcopy(PREP_TEMPLATE_COLUMNS)
                pt_cols.update(PREP_TEMPLATE_COLUMNS_TARGET_GENE)

            md_template = cls._clean_validate_template(md_template, study.id)
            _check_duplicated_columns(
                list(md_template.columns), study.sample_template.categories
            )

            # check that we are within the limit of number of samples
            ms = cls.max_samples()
            nsamples = md_template.shape[0]
            if ms is not None and nsamples > ms:
                raise ValueError(
                    f"{nsamples} exceeds the max allowed number of samples: {ms}"
                )

            # Insert the metadata template
            if creation_job_id:
                sql = """INSERT INTO qiita.prep_template
                            (data_type_id, investigation_type, creation_job_id)
                         VALUES (%s, %s, %s)
                         RETURNING prep_template_id"""
                qdb.sql_connection.TRN.add(
                    sql, [data_type_id, investigation_type, creation_job_id]
                )
            else:
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
                    qdb.sql_connection.TRN.execute_fetchflatten()
                )
                if unknown_samples:
                    raise qdb.exceptions.QiitaDBExecutionError(
                        "Samples found in prep template but not sample "
                        "template: %s" % ", ".join(unknown_samples)
                    )

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
            pt.name = name if name is not None else "Prep information %s" % pt.id

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
            ontology = qdb.ontology.Ontology(qdb.util.convert_to_id("ENA", "ontology"))
            terms = ontology.terms + ontology.user_defined_terms
            if investigation_type not in terms:
                raise qdb.exceptions.QiitaDBColumnError(
                    "'%s' is Not a valid investigation_type. Choose from: %s"
                    % (investigation_type, ", ".join(terms))
                )

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
                    " associated with it" % id_
                )

            # artifacts that are archived are not returned as part of the code
            # above and we need to clean them before moving forward
            sql = """SELECT artifact_id
                     FROM qiita.preparation_artifact
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, args)
            archived_artifacts = set(qdb.sql_connection.TRN.execute_fetchflatten())
            ANALYSIS = qdb.analysis.Analysis
            if archived_artifacts:
                for aid in archived_artifacts:
                    # before we can delete the archived artifact, we need
                    # to delete the analyses where they were used.
                    sql = """SELECT analysis_id
                             FROM qiita.analysis
                             WHERE analysis_id IN (
                                SELECT DISTINCT analysis_id
                                FROM qiita.analysis_sample
                                WHERE artifact_id IN %s)"""
                    qdb.sql_connection.TRN.add(sql, [tuple([aid])])
                    analyses = set(qdb.sql_connection.TRN.execute_fetchflatten())
                    for _id in analyses:
                        ANALYSIS.delete_analysis_artifacts(_id)
                    qdb.artifact.Artifact.delete(aid)

            # Delete the prep template filepaths
            sql = """DELETE FROM qiita.prep_template_filepath
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, args)

            # Drop the prep_X table
            sql = "DROP TABLE qiita.{0}".format(table_name)
            qdb.sql_connection.TRN.add(sql)

            # Remove the rows from prep_template_samples
            sql = "DELETE FROM qiita.{0} WHERE {1} = %s".format(
                cls._table, cls._id_column
            )
            qdb.sql_connection.TRN.add(sql, args)

            # Remove the row from study_prep_template
            sql = """DELETE FROM qiita.study_prep_template
                     WHERE {0} = %s""".format(cls._id_column)
            qdb.sql_connection.TRN.add(sql, args)

            # Remove the row from prep_template
            sql = "DELETE FROM qiita.prep_template WHERE {0} = %s".format(
                cls._id_column
            )
            qdb.sql_connection.TRN.add(sql, args)

            qdb.sql_connection.TRN.execute()

    def unique_ids(self):
        r"""Return a stable mapping of sample_name to integers

        Obtain a map from a sample_name to an integer. The association is
        unique Qiita-wide and 1-1.

        This method is idempotent.

        Returns
        ------
        dict
            {sample_name: integer_index}
        """
        sample_idx = qdb.study.Study(self.study_id).sample_template.unique_ids()

        paired = []
        for p_id in sorted(self.keys()):
            if p_id in sample_idx:
                paired.append([self._id, sample_idx[p_id]])

        with qdb.sql_connection.TRN:
            # insert any IDs not present
            sql = """INSERT INTO qiita.map_prep_sample_idx (prep_idx, sample_idx)
                     VALUES (%s, %s)
                     ON CONFLICT (prep_idx, sample_idx)
                     DO NOTHING"""
            qdb.sql_connection.TRN.add(sql, paired, many=True)

            # obtain the association
            sql = """SELECT
                         sample_name,
                         prep_sample_idx
                     FROM qiita.map_prep_sample_idx
                     JOIN qiita.map_sample_idx USING (sample_idx)
                     WHERE prep_idx=%s
                     """
            qdb.sql_connection.TRN.add(sql, [self._id, ])

            # form into a dict
            mapping = {r[0]: r[1] for r in qdb.sql_connection.TRN.execute_fetchindex()}

            # commit in the event changes were made
            qdb.sql_connection.TRN.commit()

        return mapping

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
            The dict of restrictions based on the data_type
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

            tg_columns = set(
                chain.from_iterable(
                    [v.columns for v in PREP_TEMPLATE_COLUMNS_TARGET_GENE.values()]
                )
            )

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
                        return False, (
                            "The artifact attached to the prep "
                            "template has already been processed. "
                            "No new samples can be added to the "
                            "prep template"
                        )

        _check_duplicated_columns(
            list(new_columns), qdb.study.Study(self.study_id).sample_template.categories
        )

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
                    "Prep template %d already has an artifact associated" % self.id
                )
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
        if investigation_type is not None:
            self.validate_investigation_type(investigation_type)

        sql = """UPDATE qiita.prep_template SET investigation_type = %s
                 WHERE {0} = %s""".format(self._id_column)
        qdb.sql_connection.perform_as_transaction(sql, [investigation_type, self.id])

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

    @property
    def deprecated(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT deprecated FROM qiita.prep_template
                     WHERE {0} = %s""".format(self._id_column)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @deprecated.setter
    def deprecated(self, deprecated):
        r"""Update deprecated value of prep information file

        Parameters
        ----------
        deprecated : bool
            If the prep info file is deprecated
        """
        sql = """UPDATE qiita.prep_template SET deprecated = %s
                 WHERE {0} = %s""".format(self._id_column)
        qdb.sql_connection.perform_as_transaction(sql, [deprecated, self.id])

    def generate_files(self, samples=None, columns=None):
        r"""Generates all the files that contain data from this template

        Parameters
        ----------
        samples : iterable of str, optional
            The samples that were added/updated
        columns : iterable of str, optional
            The columns that were added/updated
        """
        with qdb.sql_connection.TRN:
            # figuring out the filepath of the prep template
            _id, fp = qdb.util.get_mountpoint("templates")[0]
            # update timestamp in the DB first
            qdb.sql_connection.TRN.add(
                """UPDATE qiita.prep_template
                   SET modification_timestamp = CURRENT_TIMESTAMP
                   WHERE prep_template_id = %s""",
                [self._id],
            )
            ctime = self.modification_timestamp
            fp = join(
                fp,
                "%d_prep_%d_%s.txt"
                % (self.study_id, self._id, ctime.strftime("%Y%m%d-%H%M%S")),
            )
            # storing the template
            self.to_file(fp)
            # adding the fp to the object
            fp_id = qdb.util.convert_to_id("prep_template", "filepath_type")
            self.add_filepath(fp, fp_id=fp_id)

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
                     WHERE prep_template_id = %s and visibility_id NOT IN %s"""
            qdb.sql_connection.TRN.add(
                sql, [self._id, qdb.util.artifact_visibilities_to_skip()]
            )

            return qdb.util.infer_status(qdb.sql_connection.TRN.execute_fetchindex())

    @property
    def qiime_map_fp(self):
        """The QIIME mapping filepath attached to the prep template

        Returns
        -------
        str
            The filepath of the QIIME mapping file
        """
        for x in qdb.util.retrieve_filepaths(
            self._filepath_table, self._id_column, self.id, sort="descending"
        ):
            if x["fp_type"] == "qiime_map":
                return x["fp"]

    @property
    def ebi_experiment_accessions(self):
        """The EBI experiment accessions for the samples in the prep template

        Returns
        -------
        dict of {str: str}
            The EBI experiment accessions numbers keyed by sample id
        """
        return self._get_accession_numbers("ebi_experiment_accession")

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
        self._update_accession_numbers("ebi_experiment_accession", value)

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

    def delete_samples(self, sample_names):
        """Delete `sample_names` from prep information file

        Parameters
        ----------
        sample_names : list of str
            The sample names to be deleted

        Raises
        ------
        QiitaDBColumnError
            If the prep info file has been processed
        """
        if self.artifact:
            raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                "Prep info file '%d' has files attached, you cannot delete "
                "samples." % (self._id)
            )

        self._common_delete_sample_steps(sample_names)

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
        sql = """UPDATE qiita.prep_template
                 SET name = %s
                 WHERE prep_template_id = %s"""
        qdb.sql_connection.perform_as_transaction(sql, [value, self.id])

    def to_dataframe(self, add_ebi_accessions=False):
        """Returns the metadata template as a dataframe

        Parameters
        ----------
        add_ebi_accessions : bool, optional
            If this should add the ebi accessions
        """
        df = self._common_to_dataframe_steps()

        if add_ebi_accessions:
            accessions = self.ebi_experiment_accessions
            df["qiita_ebi_experiment_accessions"] = df.index.map(
                lambda sid: accessions[sid]
            )

        return df

    @property
    def creation_timestamp(self):
        """The creation timestamp of the prep information

        Returns
        -------
        datetime.datetime
            The creation timestamp of the prep information
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT creation_timestamp
                     FROM qiita.prep_template
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def modification_timestamp(self):
        """The modification timestamp of the prep information

        Returns
        -------
        datetime.datetime
            The modification timestamp of the prep information
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT modification_timestamp
                     FROM qiita.prep_template
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @staticmethod
    def max_samples():
        return qdb.util.max_preparation_samples()

    def add_default_workflow(self, user, workflow=None):
        """Adds the commands of the default workflow to this preparation

        Parameters
        ----------
        user : qiita_db.user.User
            The user that requested to add the default workflows
        workflow : qiita_db.processing_job.ProcessingWorkflow, optional
            The workflow to add the default processing

        Returns
        -------
        ProcessingWorkflow
            The workflow created

        Raises
        ------
        ValueError
            a. If this preparation doesn't have valid workflows
            b. This preparation has been fully processed (no new steps needed)
            c. If there is no valid initial artifact to start the workflow

        Notes
        -----
        This method adds the commands in a default workflow (definition) to
        the preparation, if a workflow (object) is passed it will add the
        commands to the last artifact in that workflow but if it's None it will
        create a new workflow (default)
        """
        # helper functions to avoid duplication of code

        def _get_node_info(workflow, node):
            # retrieves the merging scheme of a node
            parent = list(workflow.graph.predecessors(node))
            if parent:
                parent = parent.pop()
                pdp = parent.default_parameter
                pcmd = pdp.command
                pparams = pdp.values
            else:
                pcmd = None
                pparams = {}

            dp = node.default_parameter
            cparams = dp.values
            ccmd = dp.command

            parent_cmd_name = None
            parent_merging_scheme = None
            phms = None
            if pcmd is not None:
                parent_cmd_name = pcmd.name
                parent_merging_scheme = pcmd.merging_scheme
                if not parent_merging_scheme["ignore_parent_command"]:
                    phms = _get_node_info(workflow, parent)

            hms = qdb.util.human_merging_scheme(
                ccmd.name,
                ccmd.merging_scheme,
                parent_cmd_name,
                parent_merging_scheme,
                cparams,
                [],
                pparams,
            )

            # if the parent should not ignore its parent command, then we need
            # to merge the previous result with the new one
            if phms is not None:
                hms = qdb.util.merge_overlapping_strings(hms, phms)

            return hms

        def _get_predecessors(workflow, node):
            # recursive method to get predecessors of a given node
            pred = []

            parents = list(workflow.graph.predecessors(node))
            for pnode in parents:
                pred = _get_predecessors(workflow, pnode)
                cxns = {
                    x[0]: x[2]
                    for x in workflow.graph.get_edge_data(pnode, node)[
                        "connections"
                    ].connections
                }
                data = [pnode, node, cxns]
                if pred is None:
                    pred = []

                # making sure that if the node has extra parents they are
                # generated first
                parents.remove(pnode)
                if parents:
                    for pnode in parents:
                        # [-1] just adding the parent and not its ancestors
                        pred.extend([_get_predecessors(workflow, pnode)[-1]])

                pred.append(data)
                return pred

            # this is only helpful for when there are no _get_predecessors
            return pred

        # Note: we are going to use the final BIOMs to figure out which
        #       processing is missing from the back/end to the front, as this
        #       will prevent generating unnecessary steps (AKA already provided
        #       by another command), like "Split Library of Demuxed",
        #       when "Split per Sample" is alrady generated
        #
        # The steps to generate the default workflow are as follow:
        # 1. retrieve all valid merging schemes from valid jobs in the
        #    current preparation
        # 2. retrive all the valid workflows for the preparation data type and
        #    find the final BIOM missing from the valid available merging
        #    schemes
        # 3. loop over the missing merging schemes and create the commands
        #    missing to get to those processed samples and add them to a new
        #    workflow

        # 1.
        # let's assume that if there is a workflow, there are no jobs
        if workflow is not None:
            prep_jobs = []
        else:
            prep_jobs = [
                j
                for c in self.artifact.descendants.nodes()
                for j in c.jobs(show_hidden=True)
                if j.command.software.type == "artifact transformation"
            ]
        merging_schemes = {
            qdb.archive.Archive.get_merging_scheme_from_job(j): {
                x: str(y.id) for x, y in j.outputs.items()
            }
            # we are going to select only the jobs that were a 'success', that
            # are not 'hidden' and that have an output - jobs that are not
            # hidden and a successs but that do not have outputs are jobs which
            # resulting artifacts (outputs) were deleted
            for j in prep_jobs
            if j.status == "success" and not j.hidden and j.outputs
        }

        # 2.
        pt_dt = self.data_type()
        # if there is a workflow, we would need to get the artifact_type from
        # the job
        if workflow is not None:
            starting_job = list(workflow.graph.nodes())[0]
            pt_artifact = starting_job.parameters.values["artifact_type"]
        else:
            starting_job = None
            pt_artifact = self.artifact.artifact_type

        all_workflows = [wk for wk in qdb.software.DefaultWorkflow.iter()]
        # are there any workflows with parameters?
        ST = qdb.metadata_template.sample_template.SampleTemplate
        workflows = []
        for wk in all_workflows:
            if wk.artifact_type == pt_artifact and pt_dt in wk.data_type:
                wk_params = wk.parameters
                reqs_satisfied = True
                total_conditions_satisfied = 0

                if wk_params["sample"]:
                    df = ST(self.study_id).to_dataframe(samples=list(self))
                    for k, v in wk_params["sample"].items():
                        if k not in df.columns or (
                            v != "*" and v not in df[k].unique()
                        ):
                            reqs_satisfied = False
                        else:
                            total_conditions_satisfied += 1

                if wk_params["prep"]:
                    df = self.to_dataframe()
                    for k, v in wk_params["prep"].items():
                        if k not in df.columns or (
                            v != "*" and v not in df[k].unique()
                        ):
                            reqs_satisfied = False
                        else:
                            total_conditions_satisfied += 1

                if reqs_satisfied:
                    workflows.append((total_conditions_satisfied, wk))

        if not workflows:
            # raises option a.
            msg = (
                f'This preparation data type: "{pt_dt}" and/or artifact '
                f'type "{pt_artifact}" does not have valid workflows; this '
                "could be due to required parameters, please check the "
                "available workflows."
            )
            raise ValueError(msg)

        # let's just keep one, let's give it preference to the one with the
        # most total_conditions_satisfied
        _, wk = sorted(workflows, key=lambda x: x[0], reverse=True)[0]
        GH = wk.graph
        missing_artifacts = dict()
        for node, degree in GH.out_degree():
            if degree != 0:
                continue
            mscheme = _get_node_info(wk, node)
            if mscheme not in merging_schemes:
                missing_artifacts[mscheme] = node
        if not missing_artifacts:
            # raises option b.
            raise ValueError("This preparation is complete")

        # 3.
        previous_jobs = dict()
        for ma, node in missing_artifacts.items():
            predecessors = _get_predecessors(wk, node)
            predecessors.reverse()
            cmds_to_create = []
            init_artifacts = None
            for i, (pnode, cnode, cxns) in enumerate(predecessors):
                cdp = cnode.default_parameter
                cdp_cmd = cdp.command
                params = cdp.values.copy()

                icxns = {y: x for x, y in cxns.items()}
                reqp = {
                    x: icxns[y[1][0]] for x, y in cdp_cmd.required_parameters.items()
                }
                cmds_to_create.append([cdp, cdp_cmd, params, reqp])

                info = _get_node_info(wk, pnode)
                if info in merging_schemes:
                    if set(merging_schemes[info]) >= set(cxns):
                        init_artifacts = merging_schemes[info]
                        break
            if not predecessors:
                pnode = node
            if init_artifacts is None:
                pdp = pnode.default_parameter
                pdp_cmd = pdp.command
                params = pdp.values.copy()
                # verifying that the workflow.artifact_type is included
                # in the command input types or raise an error
                wkartifact_type = wk.artifact_type
                reqp = dict()
                for x, y in pdp_cmd.required_parameters.items():
                    if wkartifact_type not in y[1]:
                        raise ValueError(
                            f"{wkartifact_type} is not part "
                            "of this preparation and cannot "
                            "be applied"
                        )
                    reqp[x] = wkartifact_type

                cmds_to_create.append([pdp, pdp_cmd, params, reqp])

                if starting_job is not None:
                    init_artifacts = {wkartifact_type: f"{starting_job.id}:"}
                else:
                    init_artifacts = {wkartifact_type: str(self.artifact.id)}

            cmds_to_create.reverse()
            current_job = None
            loop_starting_job = starting_job
            previous_dps = dict()
            for i, (dp, cmd, params, rp) in enumerate(cmds_to_create):
                if loop_starting_job is not None:
                    previous_job = loop_starting_job
                    loop_starting_job = None
                else:
                    previous_job = current_job

                req_params = dict()
                if previous_job is None:
                    for iname, dname in rp.items():
                        if dname not in init_artifacts:
                            msg = (
                                f'Missing Artifact type: "{dname}" in '
                                "this preparation; this might be due "
                                "to missing steps or not having the "
                                "correct raw data."
                            )
                            # raises option c.
                            raise ValueError(msg)
                        req_params[iname] = init_artifacts[dname]
                    if len(dp.command.required_parameters) > 1:
                        for pn in GH.predecessors(node):
                            info = _get_node_info(wk, pn)
                            n, cnx, _ = GH.get_edge_data(pn, node)[
                                "connections"
                            ].connections[0]
                            if (
                                info not in merging_schemes
                                or n not in merging_schemes[info]
                            ):
                                msg = (
                                    "This workflow contains a step with "
                                    "multiple inputs so it cannot be "
                                    "completed automatically, please add "
                                    "the commands by hand."
                                )
                                raise ValueError(msg)
                            req_params[cnx] = merging_schemes[info][n]
                else:
                    if len(dp.command.required_parameters) == 1:
                        cxns = dict()
                        for iname, dname in rp.items():
                            req_params[iname] = f"{previous_job.id}{dname}"
                            cxns[dname] = iname
                        connections = {previous_job: cxns}
                    else:
                        connections = dict()
                        for pn in GH.predecessors(node):
                            pndp = pn.default_parameter
                            n, cnx, _ = GH.get_edge_data(pn, node)[
                                "connections"
                            ].connections[0]
                            _job = previous_dps[pndp.id]
                            req_params[cnx] = f"{_job.id}{n}"
                            connections[_job] = {n: cnx}
                params.update(req_params)
                job_params = qdb.software.Parameters.load(cmd, values_dict=params)

                if params in previous_jobs.values():
                    for x, y in previous_jobs.items():
                        if params == y:
                            current_job = x
                else:
                    if workflow is None:
                        PW = qdb.processing_job.ProcessingWorkflow
                        workflow = PW.from_scratch(user, job_params)
                        current_job = [j for j in workflow.graph.nodes()][0]
                    else:
                        if previous_job is None:
                            current_job = workflow.add(
                                job_params, req_params=req_params
                            )
                        else:
                            current_job = workflow.add(
                                job_params,
                                req_params=req_params,
                                connections=connections,
                            )
                    previous_jobs[current_job] = params
                previous_dps[dp.id] = current_job

        return workflow

    @property
    def archived_artifacts(self):
        """List of archived Artifacts

        Returns
        -------
        list of qiita_db.artifact.Artifact
            The list of archivde Artifacts
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT artifact_id
                     FROM qiita.preparation_artifact
                        LEFT JOIN qiita.artifact USING (artifact_id)
                     WHERE prep_template_id = %s AND visibility_id IN %s"""
            qdb.sql_connection.TRN.add(
                sql, [self.id, qdb.util.artifact_visibilities_to_skip()]
            )
            return [
                qdb.artifact.Artifact(ai)
                for ai in qdb.sql_connection.TRN.execute_fetchflatten()
            ]

    @property
    def creation_job_id(self):
        """The creation_job_id of the prep information

        Returns
        -------
        str
            The creation_job_id of the prep information
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT creation_job_id
                     FROM qiita.prep_template
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @creation_job_id.setter
    def creation_job_id(self, creation_job_id):
        with qdb.sql_connection.TRN:
            sql = """UPDATE qiita.prep_template
                     SET creation_job_id = %s
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [creation_job_id, self.id])
            qdb.sql_connection.TRN.execute()

    @property
    def current_human_filtering(self):
        """If the preparation is current with human filtering

        Returns
        -------
        bool
            The current_human_filtering of the prep information
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT current_human_filtering
                     FROM qiita.prep_template
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @current_human_filtering.setter
    def current_human_filtering(self, current_human_filtering):
        with qdb.sql_connection.TRN:
            sql = """UPDATE qiita.prep_template
                     SET current_human_filtering = %s
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [current_human_filtering, self.id])
            qdb.sql_connection.TRN.execute()

    @property
    def reprocess_job_id(self):
        """The job that was created to reprocess this prep info file

        Returns
        -------
        bool or None
            The reprocess_job_id of the prep file info
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT reprocess_job_id
                     FROM qiita.prep_template
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @reprocess_job_id.setter
    def reprocess_job_id(self, reprocess_job_id):
        with qdb.sql_connection.TRN:
            sql = """UPDATE qiita.prep_template
                     SET reprocess_job_id = %s
                     WHERE prep_template_id = %s"""
            qdb.sql_connection.TRN.add(sql, [reprocess_job_id, self.id])
            qdb.sql_connection.TRN.execute()
