# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from future.utils import viewitems
from itertools import chain
from datetime import datetime

import networkx as nx

import qiita_db as qdb


class Artifact(qdb.base.QiitaObject):
    r"""Any kind of file (or group of files) stored in the system and its
    attributes

    Attributes
    ----------
    timestamp
    processing_parameters
    visibility
    artifact_type
    data_type
    can_be_submitted_to_ebi
    can_be_submitted_to_vamps
    is_submitted_to_vamps
    filepaths
    parents
    prep_template
    ebi_run_accession
    study

    Methods
    -------
    create
    delete

    See Also
    --------
    qiita_db.QiitaObject
    """
    _table = "artifact"

    @classmethod
    def iter_by_visibility(cls, visibility):
        r"""Iterator over the artifacts with the given visibility

        Parameters
        ----------
        visibility : str
            The visibility level

        Returns
        -------
        generator of qiita_db.artifact.Artifact
            The artifacts available in the system with the given visibility
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT artifact_id
                     FROM qiita.artifact
                        JOIN qiita.visibility USING (visibility_id)
                     WHERE visibility = %s
                     ORDER BY artifact_id"""
            qdb.sql_connection.TRN.add(sql, [visibility])
            for a_id in qdb.sql_connection.TRN.execute_fetchflatten():
                yield cls(a_id)

    @classmethod
    def iter_public(cls):
        r"""Iterator over the public artifacts available in the system

        Returns
        -------
        generator of qiita_db.artifact.Artifact
            The public artifacts available in the system
        """
        return cls.iter_by_visibility('public')

    @staticmethod
    def types():
        """Returns list of all artifact types available and their descriptions

        Returns
        -------
        list of list of str
            The artifact type and description of the artifact type, in the form
            [[artifact_type, description], ...]
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT artifact_type, description
                     FROM qiita.artifact_type
                     ORDER BY artifact_type"""
            qdb.sql_connection.TRN.add(sql)
            return qdb.sql_connection.TRN.execute_fetchindex()

    @classmethod
    def copy(cls, artifact, prep_template):
        """Creates a copy of `artifact` and attaches it to `prep_template`

        Parameters
        ----------
        artifact : qiita_db.artifact.Artifact
            Artifact to copy from
        prep_template : qiita_db.metadata_template.prep_template.PrepTemplate
            The prep template to attach the new artifact to

        Returns
        -------
        qiita_db.artifact.Artifact
            A new instance of Artifact
        """
        with qdb.sql_connection.TRN:
            visibility_id = qdb.util.convert_to_id("sandbox", "visibility")
            atype = artifact.artifact_type
            atype_id = qdb.util.convert_to_id(atype, "artifact_type")
            dtype_id = qdb.util.convert_to_id(
                prep_template.data_type(), "data_type")
            sql = """INSERT INTO qiita.artifact (
                        generated_timestamp, visibility_id, artifact_type_id,
                        data_type_id, submitted_to_vamps)
                     VALUES (%s, %s, %s, %s, %s)
                     RETURNING artifact_id"""
            sql_args = [datetime.now(), visibility_id, atype_id, dtype_id,
                        False]
            qdb.sql_connection.TRN.add(sql, sql_args)
            a_id = qdb.sql_connection.TRN.execute_fetchlast()

            # Associate the artifact with the prep template
            instance = cls(a_id)
            prep_template.artifact = instance

            # Associate the artifact with the study
            sql = """INSERT INTO qiita.study_artifact (study_id, artifact_id)
                     VALUES (%s, %s)"""
            sql_args = [prep_template.study_id, a_id]
            qdb.sql_connection.TRN.add(sql, sql_args)

            # Associate the artifact with its filepaths
            filepaths = [(fp, f_type) for _, fp, f_type in artifact.filepaths]
            fp_ids = qdb.util.insert_filepaths(
                filepaths, a_id, atype, "filepath", copy=True)
            sql = """INSERT INTO qiita.artifact_filepath
                        (artifact_id, filepath_id)
                     VALUES (%s, %s)"""
            sql_args = [[a_id, fp_id] for fp_id in fp_ids]
            qdb.sql_connection.TRN.add(sql, sql_args, many=True)
            qdb.sql_connection.TRN.execute()

        return instance

    @classmethod
    def create(cls, filepaths, artifact_type, name=None, prep_template=None,
               parents=None, processing_parameters=None):
        r"""Creates a new artifact in the system

        The parameters depend on how the artifact was generated:
            - If the artifact was uploaded by the user, the parameter
            `prep_template` should be provided and the parameters `parents` and
            `processing_parameters` should not be provided.
            - If the artifact was generated by processing one or more
            artifacts, the parameters `parents` and `processing_parameters`
            should be provided and the parameter `prep_template` should not
            be provided.

        Parameters
        ----------
        filepaths : iterable of tuples (str, int)
            A list of 2-tuples in which the first element is the artifact
            file path and the second one is the file path type id
        artifact_type : str
            The type of the artifact
        name : str, optional
            The artifact's name
        prep_template : qiita_db.metadata_template.PrepTemplate, optional
            If the artifact is being uploaded by the user, the prep template
            to which the artifact should be linked to. If not provided,
            `parents` should be provided.
        parents : iterable of qiita_db.artifact.Artifact, optional
            The list of artifacts from which the new artifact has been
            generated. If not provided, `prep_template` should be provided.
        processing_parameters : qiita_db.software.Parameters, optional
            The processing parameters used to generate the new artifact
            from `parents`. It is required if `parents` is provided. It should
            not be provided if `prep_template` is provided.

        Returns
        -------
        qiita_db.artifact.Artifact
            A new instance of Artifact

        Raises
        ------
        QiitaDBArtifactCreationError
            If `filepaths` is not provided
            If both `parents` and `prep_template` are provided
            If none of `parents` and `prep_template` are provided
            If `parents` is provided but `processing_parameters` is not
            If both `prep_template` and `processing_parameters` is provided
            If not all the artifacts in `parents` belong to the same study

        Notes
        -----
        The visibility of the artifact is set by default to `sandbox`
        The timestamp of the artifact is set by default to `datetime.now()`
        The value of `submitted_to_vamps` is set by default to `False`
        """
        # We need at least one file
        if not filepaths:
            raise qdb.exceptions.QiitaDBArtifactCreationError(
                "at least one filepath is required.")

        # Parents or prep template must be provided, but not both
        if parents and prep_template:
            raise qdb.exceptions.QiitaDBArtifactCreationError(
                "parents or prep_template should be provided but not both")
        elif not (parents or prep_template):
            raise qdb.exceptions.QiitaDBArtifactCreationError(
                "at least parents or prep_template must be provided")
        elif parents and not processing_parameters:
            # If parents is provided, processing parameters should also be
            # provided
            raise qdb.exceptions.QiitaDBArtifactCreationError(
                "if parents is provided, processing_parameters should also be"
                "provided.")
        elif prep_template and processing_parameters:
            # If prep_template is provided, processing_parameters should not be
            # provided
            raise qdb.exceptions.QiitaDBArtifactCreationError(
                "if prep_template is provided, processing_parameters should "
                "not be provided.")

        timestamp = datetime.now()

        with qdb.sql_connection.TRN:
            visibility_id = qdb.util.convert_to_id("sandbox", "visibility")
            artifact_type_id = qdb.util.convert_to_id(
                artifact_type, "artifact_type")

            if parents:
                # Check that all parents belong to the same study
                studies = {p.study.id for p in parents}
                if len(studies) > 1:
                    raise qdb.exceptions.QiitaDBArtifactCreationError(
                        "parents from multiple studies provided: %s"
                        % ', '.join(studies))
                study_id = studies.pop()

                # Check that all parents have the same data type
                dtypes = {p.data_type for p in parents}
                if len(dtypes) > 1:
                    raise qdb.exceptions.QiitaDBArtifactCreationError(
                        "parents have multiple data types: %s"
                        % ", ".join(dtypes))
                dtype_id = qdb.util.convert_to_id(dtypes.pop(), "data_type")

                # Create the artifact
                sql = """INSERT INTO qiita.artifact
                            (generated_timestamp, command_id, data_type_id,
                             command_parameters, visibility_id,
                             artifact_type_id, submitted_to_vamps)
                         VALUES (%s, %s, %s, %s, %s, %s, %s)
                         RETURNING artifact_id"""
                sql_args = [timestamp, processing_parameters.command.id,
                            dtype_id, processing_parameters.dump(),
                            visibility_id, artifact_type_id, False]
                qdb.sql_connection.TRN.add(sql, sql_args)
                a_id = qdb.sql_connection.TRN.execute_fetchlast()

                # Associate the artifact with its parents
                sql = """INSERT INTO qiita.parent_artifact
                            (artifact_id, parent_id)
                         VALUES (%s, %s)"""
                sql_args = [(a_id, p.id) for p in parents]
                qdb.sql_connection.TRN.add(sql, sql_args, many=True)

                instance = cls(a_id)
            else:
                dtype_id = qdb.util.convert_to_id(prep_template.data_type(),
                                                  "data_type")
                # Create the artifact
                sql = """INSERT INTO qiita.artifact
                            (generated_timestamp, visibility_id,
                             artifact_type_id, data_type_id,
                             submitted_to_vamps)
                         VALUES (%s, %s, %s, %s, %s)
                         RETURNING artifact_id"""
                sql_args = [timestamp, visibility_id, artifact_type_id,
                            dtype_id, False]
                qdb.sql_connection.TRN.add(sql, sql_args)
                a_id = qdb.sql_connection.TRN.execute_fetchlast()

                # Associate the artifact with the prep template
                instance = cls(a_id)
                prep_template.artifact = instance
                study_id = prep_template.study_id

            # Associate the artifact with the study
            sql = """INSERT INTO qiita.study_artifact (study_id, artifact_id)
                     VALUES (%s, %s)"""
            sql_args = [study_id, a_id]
            qdb.sql_connection.TRN.add(sql, sql_args)

            # Associate the artifact with its filepaths
            fp_ids = qdb.util.insert_filepaths(
                filepaths, a_id, artifact_type, "filepath")
            sql = """INSERT INTO qiita.artifact_filepath
                        (artifact_id, filepath_id)
                     VALUES (%s, %s)"""
            sql_args = [[a_id, fp_id] for fp_id in fp_ids]
            qdb.sql_connection.TRN.add(sql, sql_args, many=True)
            qdb.sql_connection.TRN.execute()

            if name:
                instance.name = name

        return instance

    @classmethod
    def delete(cls, artifact_id):
        r"""Deletes an artifact from the system

        Parameters
        ----------
        artifact_id : int
            The artifact to be removed

        Raises
        ------
        QiitaDBArtifactDeletionError
            If the artifact is public
            If the artifact has children
            If the artifact has been analyzed
            If the artifact has been submitted to EBI
            If the artifact has been submitted to VAMPS
        """
        with qdb.sql_connection.TRN:
            # This will fail if the artifact with id=artifact_id doesn't exist
            instance = cls(artifact_id)

            # Check if the artifact is public
            if instance.visibility == 'public':
                raise qdb.exceptions.QiitaDBArtifactDeletionError(
                    artifact_id, "it is public")

            # Check if this artifact has any children
            if instance.children:
                raise qdb.exceptions.QiitaDBArtifactDeletionError(
                    artifact_id,
                    "it has children: %s"
                    % ', '.join([str(c.id) for c in instance.children]))

            # Check if the artifact has been analyzed
            sql = """SELECT EXISTS(SELECT *
                                   FROM qiita.analysis_sample
                                   WHERE artifact_id = %s)"""
            qdb.sql_connection.TRN.add(sql, [artifact_id])
            if qdb.sql_connection.TRN.execute_fetchlast():
                raise qdb.exceptions.QiitaDBArtifactDeletionError(
                    artifact_id, "it has been analyzed")

            # Check if the artifact has been submitted to EBI
            if instance.can_be_submitted_to_ebi and \
                    instance.ebi_run_accessions:
                raise qdb.exceptions.QiitaDBArtifactDeletionError(
                    artifact_id, "it has been submitted to EBI")

            # Check if the artifact has been submitted to VAMPS
            if instance.can_be_submitted_to_vamps and \
                    instance.is_submitted_to_vamps:
                raise qdb.exceptions.QiitaDBArtifactDeletionError(
                    artifact_id, "it has been submitted to VAMPS")

            # Check if there is a job queued, running, waiting or
            # in_construction that will use/is using the artifact
            sql = """SELECT EXISTS(
                        SELECT *
                        FROM qiita.artifact_processing_job
                            JOIN qiita.processing_job USING (processing_job_id)
                            JOIN qiita.processing_job_status
                                USING (processing_job_status_id)
                        WHERE artifact_id = %s
                            AND processing_job_status IN (
                                'queued', 'running', 'waiting',
                                'in_construction'))"""
            qdb.sql_connection.TRN.add(sql, [artifact_id])
            if qdb.sql_connection.TRN.execute_fetchlast():
                raise qdb.exceptions.QiitaDBArtifactDeletionError(
                    artifact_id,
                    "there is a queued/running job that uses this artifact")

            # We can now remove the artifact
            filepaths = instance.filepaths
            study = instance.study

            # Delete any failed/successful job that had the artifact as input
            sql = """SELECT processing_job_id
                     FROM qiita.artifact_processing_job
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [artifact_id])
            job_ids = tuple(qdb.sql_connection.TRN.execute_fetchflatten())

            if job_ids:
                sql = """DELETE FROM qiita.artifact_processing_job
                         WHERE artifact_id = %s"""
                qdb.sql_connection.TRN.add(sql, [artifact_id])

                sql = """DELETE FROM qiita.processing_job
                         WHERE processing_job_id IN %s"""
                qdb.sql_connection.TRN.add(sql, [job_ids])

            # Delete the entry from the artifact_output_processing_job table
            sql = """DELETE FROM qiita.artifact_output_processing_job
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [artifact_id])

            # Detach the artifact from its filepaths
            sql = """DELETE FROM qiita.artifact_filepath
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [artifact_id])

            # If the artifact doesn't have parents, we move the files to the
            # uploads folder. We also need to nullify the column in the prep
            # template table
            if not instance.parents:
                qdb.util.move_filepaths_to_upload_folder(study.id, filepaths)

                sql = """UPDATE qiita.prep_template
                         SET artifact_id = NULL
                         WHERE prep_template_id IN %s"""
                qdb.sql_connection.TRN.add(
                    sql, [tuple(pt.id for pt in instance.prep_templates)])
            else:
                sql = """DELETE FROM qiita.parent_artifact
                         WHERE artifact_id = %s"""
                qdb.sql_connection.TRN.add(sql, [artifact_id])

            # Detach the artifact from the study_artifact table
            sql = "DELETE FROM qiita.study_artifact WHERE artifact_id = %s"
            qdb.sql_connection.TRN.add(sql, [artifact_id])

            # Delete the row in the artifact table
            sql = "DELETE FROM qiita.artifact WHERE artifact_id = %s"
            qdb.sql_connection.TRN.add(sql, [artifact_id])

    @property
    def name(self):
        """The name of the artifact

        Returns
        -------
        str
            The artifact name
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT name
                     FROM qiita.artifact
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @name.setter
    def name(self, value):
        """Set the name of the artifact

        Parameters
        ----------
        value : str
            The new artifact's name

        Raises
        ------
        ValueError
            If `value` contains more than 35 chars
        """
        if len(value) > 35:
            raise ValueError("The name of an artifact cannot exceed 35 chars. "
                             "Current length: %d" % len(value))
        with qdb.sql_connection.TRN:
            sql = """UPDATE qiita.artifact
                     SET name = %s
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [value, self.id])
            qdb.sql_connection.TRN.execute()

    @property
    def timestamp(self):
        """The timestamp when the artifact was generated

        Returns
        -------
        datetime
            The timestamp when the artifact was generated
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT generated_timestamp
                     FROM qiita.artifact
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def processing_parameters(self):
        """The processing parameters used to generate the artifact

        Returns
        -------
        qiita_db.software.Parameters or None
            The parameters used to generate the artifact if it has parents.
            None otherwise.
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT command_id, command_parameters
                     FROM qiita.artifact
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            # Only one row will be returned
            res = qdb.sql_connection.TRN.execute_fetchindex()[0]
            if res[0] is None:
                return None
            return qdb.software.Parameters.load(
                qdb.software.Command(res[0]), values_dict=res[1])

    @property
    def visibility(self):
        """The visibility of the artifact

        Returns
        -------
        str
            The visibility of the artifact
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT visibility
                     FROM qiita.artifact
                        JOIN qiita.visibility USING (visibility_id)
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @visibility.setter
    def visibility(self, value):
        """Sets the visibility of the artifact

        Parameters
        ----------
        value : str
            The new visibility of the artifact
        """
        with qdb.sql_connection.TRN:
            sql = """UPDATE qiita.artifact
                     SET visibility_id = %s
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(
                sql, [qdb.util.convert_to_id(value, "visibility"), self.id])
            qdb.sql_connection.TRN.execute()

    @property
    def artifact_type(self):
        """The artifact type

        Returns
        -------
        str
            The artifact type
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT artifact_type
                     FROM qiita.artifact
                        JOIN qiita.artifact_type USING (artifact_type_id)
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def data_type(self):
        """The data type of the artifact

        Returns
        -------
        str
            The artifact data type
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT data_type
                     FROM qiita.artifact
                        JOIN qiita.data_type USING (data_type_id)
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def can_be_submitted_to_ebi(self):
        """Whether the artifact can be submitted to EBI or not

        Returns
        -------
        bool
            True if the artifact can be submitted to EBI. False otherwise.
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT can_be_submitted_to_ebi
                     FROM qiita.artifact_type
                        JOIN qiita.artifact USING (artifact_type_id)
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def is_submitted_to_ebi(self):
        """Whether the artifact has been submitted to EBI or not

        Returns
        -------
        bool
            True if the artifact has been submitted to EBI. False otherwise

        Raises
        ------
        QiitaDBOperationNotPermittedError
            If the artifact cannot be submitted to EBI
        """
        with qdb.sql_connection.TRN:
            if not self.can_be_submitted_to_ebi:
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Artifact %s cannot be submitted to EBI" % self.id)
            sql = """SELECT EXISTS(
                        SELECT *
                        FROM qiita.ebi_run_accession
                        WHERE artifact_id = %s)"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def ebi_run_accessions(self):
        """The EBI run accessions attached to this artifact

        Returns
        -------
        dict of {str: str}
            The EBI run accessions keyed by sample id

        Raises
        ------
        QiitaDBOperationNotPermittedError
            If the artifact cannot be submitted to EBI
        """
        with qdb.sql_connection.TRN:
            if not self.can_be_submitted_to_ebi:
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Artifact %s cannot be submitted to EBI" % self.id)
            sql = """SELECT sample_id, ebi_run_accession
                     FROM qiita.ebi_run_accession
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return {s_id: ebi_acc for s_id, ebi_acc in
                    qdb.sql_connection.TRN.execute_fetchindex()}

    @ebi_run_accessions.setter
    def ebi_run_accessions(self, values):
        """Set the EBI run accession attached to this artifact

        Parameters
        ----------
        values : dict of {str: str}
            The EBI accession number keyed by sample id

        Raises
        ------
        QiitaDBOperationNotPermittedError
            If the artifact cannot be submitted to EBI
            If the artifact has been already submitted to EBI
        """
        with qdb.sql_connection.TRN:
            if not self.can_be_submitted_to_ebi:
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Artifact %s cannot be submitted to EBI" % self.id)

            sql = """SELECT EXISTS(SELECT *
                                   FROM qiita.ebi_run_accession
                                   WHERE artifact_id = %s)"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            if qdb.sql_connection.TRN.execute_fetchlast():
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Artifact %s already submitted to EBI" % self.id)

            sql = """INSERT INTO qiita.ebi_run_accession
                        (sample_id, artifact_id, ebi_run_accession)
                     VALUES (%s, %s, %s)"""
            sql_args = [[sample, self.id, accession]
                        for sample, accession in viewitems(values)]
            qdb.sql_connection.TRN.add(sql, sql_args, many=True)
            qdb.sql_connection.TRN.execute()

    @property
    def can_be_submitted_to_vamps(self):
        """Whether the artifact can be submitted to VAMPS or not

        Returns
        -------
        bool
            True if the artifact can be submitted to VAMPS. False otherwise.
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT can_be_submitted_to_vamps
                     FROM qiita.artifact_type
                        JOIN qiita.artifact USING (artifact_type_id)
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def is_submitted_to_vamps(self):
        """Whether if the artifact has been submitted to VAMPS or not

        Returns
        -------
        bool
            True if the artifact has been submitted to VAMPS. False otherwise

        Raises
        ------
        QiitaDBOperationNotPermittedError
            If the artifact cannot be submitted to VAMPS
        """
        with qdb.sql_connection.TRN:
            if not self.can_be_submitted_to_vamps:
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Artifact %s cannot be submitted to VAMPS" % self.id)
            sql = """SELECT submitted_to_vamps
                     FROM qiita.artifact
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @is_submitted_to_vamps.setter
    def is_submitted_to_vamps(self, value):
        """Set if the artifact has been submitted to VAMPS

        Parameters
        ----------
        value : bool
            Whether the artifact has been submitted to VAMPS or not

        Raises
        ------
        QiitaDBOperationNotPermittedError
            If the artifact cannot be submitted to VAMPS
        """
        with qdb.sql_connection.TRN:
            if not self.can_be_submitted_to_vamps:
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Artifact %s cannot be submitted to VAMPS" % self.id)
            sql = """UPDATE qiita.artifact
                     SET submitted_to_vamps = %s
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [value, self.id])
            qdb.sql_connection.TRN.execute()

    @property
    def filepaths(self):
        """Returns the filepaths associated with the artifact

        Returns
        -------
        list of (int, str, str)
            A list of (filepath_id, path, filetype) of all the files associated
            with the artifact
        """
        return qdb.util.retrieve_filepaths(
            "artifact_filepath", "artifact_id", self.id, sort='ascending')

    @property
    def html_summary_fp(self):
        """Returns the HTML summary filepath

        Returns
        -------
        tuple of (int, str)
            The filepath id and the path to the HTML summary
        """
        fps = qdb.util.retrieve_filepaths("artifact_filepath", "artifact_id",
                                          self.id, fp_type='html_summary')
        if fps:
            # If fps is not the empty list, then we have exactly one file
            # retrieve_filepaths returns a list of lists of 3 values: the
            # filepath id, the filepath and the filepath type. We don't want
            # to return the filepath type here, so just grabbing the first and
            # second element of the list
            res = (fps[0][0], fps[0][1])
        else:
            res = None

        return res

    @property
    def parents(self):
        """Returns the parents of the artifact

        Returns
        -------
        list of qiita_db.artifact.Artifact
            The parent artifacts
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT parent_id
                     FROM qiita.parent_artifact
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return [Artifact(p_id)
                    for p_id in qdb.sql_connection.TRN.execute_fetchflatten()]

    def _create_lineage_graph_from_edge_list(self, edge_list):
        """Generates an artifact graph from the given `edge_list`

        Parameters
        ----------
        edge_list : list of (int, int)
            List of (parent_artifact_id, artifact_id)

        Returns
        -------
        networkx.DiGraph
            The graph representing the artifact lineage stored in `edge_list`
        """
        lineage = nx.DiGraph()
        # In case the edge list is empty, only 'self' is present in the graph
        if edge_list:
            # By creating all the artifacts here we are saving DB calls
            nodes = {a_id: Artifact(a_id)
                     for a_id in set(chain.from_iterable(edge_list))}

            for parent, child in edge_list:
                lineage.add_edge(nodes[parent], nodes[child])
        else:
            lineage.add_node(self)

        return lineage

    @property
    def ancestors(self):
        """Returns the ancestors of the artifact

        Returns
        -------
        networkx.DiGraph
            The ancestors of the artifact
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT parent_id, artifact_id
                     FROM qiita.artifact_ancestry(%s)"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            edges = qdb.sql_connection.TRN.execute_fetchindex()
        return self._create_lineage_graph_from_edge_list(edges)

    @property
    def descendants(self):
        """Returns the descendants of the artifact

        Returns
        -------
        networkx.DiGraph
            The descendants of the artifact
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT parent_id, artifact_id
                     FROM qiita.artifact_descendants(%s)"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            edges = qdb.sql_connection.TRN.execute_fetchindex()
        return self._create_lineage_graph_from_edge_list(edges)

    @property
    def children(self):
        """Returns the list of children of the artifact

        Returns
        -------
        list of qiita_db.artifact.Artifact
            The children artifacts
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT artifact_id
                     FROM qiita.parent_artifact
                     WHERE parent_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return [Artifact(c_id)
                    for c_id in qdb.sql_connection.TRN.execute_fetchflatten()]

    @property
    def youngest_artifact(self):
        """Returns the youngest artifact of the artifact's lineage

        Returns
        -------
        qiita_db.artifact.Artifact
            The youngest descendant of the artifact's lineage
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT artifact_id
                     FROM qiita.artifact_descendants(%s)
                        JOIN qiita.artifact USING (artifact_id)
                     ORDER BY generated_timestamp DESC
                     LIMIT 1"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            a_id = qdb.sql_connection.TRN.execute_fetchindex()
            # If the current artifact has no children, the previous call will
            # return an empty list, so the youngest artifact in the lineage is
            # the current artifact. On the other hand, if it has descendants,
            # the id of the youngest artifact will be in a_id[0][0]
            result = Artifact(a_id[0][0]) if a_id else self

        return result

    @property
    def prep_templates(self):
        """The prep templates attached to this artifact

        Returns
        -------
        list of qiita_db.metadata_template.PrepTemplate
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT prep_template_id
                     FROM qiita.prep_template
                     WHERE artifact_id IN (
                        SELECT *
                        FROM qiita.find_artifact_roots(%s))"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return [qdb.metadata_template.prep_template.PrepTemplate(pt_id)
                    for pt_id in qdb.sql_connection.TRN.execute_fetchflatten()]

    @property
    def study(self):
        """The study to which the artifact belongs to

        Returns
        -------
        qiita_db.study.Study
            The study that owns the artifact
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT study_id
                     FROM qiita.study_artifact
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.study.Study(qdb.sql_connection.TRN.execute_fetchlast())

    def jobs(self, cmd=None, status=None):
        """Jobs that used this artifact as input

        Parameters
        ----------
        cmd : qiita_db.software.Command, optional
            If provided, only jobs that executed this command will be returned
        status : str, optional
            If provided, only jobs in this status will be returned

        Returns
        -------
        list of qiita_db.processing_job.ProcessingJob
            The list of jobs that used this artifact as input
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT processing_job_id
                     FROM qiita.artifact_processing_job
                        JOIN qiita.processing_job USING (processing_job_id)
                        JOIN qiita.processing_job_status
                            USING (processing_job_status_id)
                     WHERE artifact_id = %s"""
            sql_args = [self.id]

            if cmd:
                sql = "{} AND command_id = %s".format(sql)
                sql_args.append(cmd.id)

            if status:
                sql = "{} AND processing_job_status = %s".format(sql)
                sql_args.append(status)

            qdb.sql_connection.TRN.add(sql, sql_args)
            return [qdb.processing_job.ProcessingJob(jid)
                    for jid in qdb.sql_connection.TRN.execute_fetchflatten()]
