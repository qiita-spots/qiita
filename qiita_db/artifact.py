# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
from datetime import datetime

from .base import QiitaObject
from .sql_connection import TRN
from .exceptions import QiitaDBArtifactCreationError
from .util import convert_to_id, insert_filepaths


class Artifact(QiitaObject):
    r"""A piece of data that different commands can be applied on

    Attributes
    ----------
    timestamp
    processing_parameters
    visibility
    artifact_type
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
    def create(cls, filepaths, artifact_type, timestamp=None,
               prep_template=None, parents=None, processing_parameters=None,
               can_be_submitted_to_ebi=False, can_be_submitted_to_vamps=False):
        r"""Creates a new artifact on the storage system

        Parameters
        ----------
        filepaths : iterable of tuples (str, int)
            A list of 2-tuples in which the first element is the artifact
            file path and the second one is the file path type id
        artifact_type : str
            The type of the artifact
        timestamp : datetime, optional
            The timestamp in which the artifact was generated. If not provided,
            the current system time (`datetime.now()`) will be used.
        prep_template : qiita_db.metadata_template.PrepTemplate, optional
            If the artifact is being uploaded by the user, the prep template
            to which the artifact should be linked to. If not provided,
            `parents` should be provided.
        parents : iterable of qiita_db.artifact.Artifact, optional
            The list of artifacts from which the new artifact has been
            generated. If not provided, `prep_template` should be provided.
        processeing_parameters : qiita_db.parameter.Parameter, optional
            The processing parameters used to generate the new artifact
            from `parents`. It is required if `parents` is provided. It should
            not be provided if `prep_template` is provided.
        can_be_submitted_to_ebi : bool, optional
            Whether the new artifact can be submitted to EBI or not. Default:
            `False`.
        can_be_submitted_to_vamps : bool, optional
            Whether the new artifact can be submitted to VAMPS or not. Default:
            `False`.

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
        """
        # We need at least one file
        if not filepaths:
            raise QiitaDBArtifactCreationError(
                "at least one filepath is required.")

        # Parents or prep template must be provided, but not both
        if parents and prep_template:
            raise QiitaDBArtifactCreationError(
                "parents or prep_template should be provided but not both")
        elif not (parents or prep_template):
            raise QiitaDBArtifactCreationError(
                "at least parents or prep_template must be provided")

        # If parents is provided, processing parameters should also be provided
        if parents and not processing_parameters:
            raise QiitaDBArtifactCreationError(
                "if parents is provided, processing_parameters should also be"
                "provided.")

        # If prep_template is provided, processing_parameters should not be
        # provided
        if prep_template and processing_parameters:
            raise QiitaDBArtifactCreationError(
                "if prep_template is provided, processing_parameters should "
                "not be provided.")

        if timestamp is None:
            timestamp = datetime.now()

        with TRN:
            visibility_id = convert_to_id("sandbox", "visibility")
            artifact_type_id = convert_to_id("sandbox", "artifact_type")

            if parents:
                # Check that all parents belong to the same study
                studies = {p.study for p in parents}
                if len(studies) > 1:
                    raise QiitaDBArtifactCreationError(
                        "parents from multiple studies provided: %s"
                        % ', '.join(studies))
                study_id = studies[0]

                # Create the artifact
                sql = """INSERT INTO qiita.artifact
                            (generated_timestamp, command_id,
                             command_parameters_id, visibility_id,
                             artifact_type_id, can_be_submitted_to_ebi,
                             can_be_submitted_to_vamps, submitted_to_vamps)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                         RETURNING artifact_id"""
                sql_args = [timestamp, processing_parameters.command.id,
                            processing_parameters.id, visibility_id,
                            artifact_type_id, can_be_submitted_to_ebi,
                            can_be_submitted_to_vamps, False]
                TRN.add(sql, sql_args)
                a_id = TRN.execute_fetchlast()

                # Associate the artifact with its parents
                sql = """INSERT INTO qiita.parent_artifact
                            (artifact_id, parent_id)
                         VALUES (%s, %s)"""
                sql_args = [(a_id, p.id) for p in parents]
                TRN.add(sql, sql_args, many=True)

                instance = cls(a_id)
            else:
                # Create the artifact
                sql = """INSERT INTO qiita.artifact
                            (generated_timestamp, visibility_id,
                             artifact_type_id, can_be_submitted_to_ebi,
                             can_be_submitted_to_vamps, submitted_to_vamps)
                         VALUES (%s, %s, %s, %s, %s, %s)
                         RETURNING artifact_id"""
                sql_args = [timestamp, visibility_id, artifact_type_id,
                            can_be_submitted_to_ebi, can_be_submitted_to_vamps,
                            False]
                TRN.add(sql, sql_args)
                a_id = TRN.execute_fetchlast()

                # Associate the artifact with the prep template
                instance = cls(a_id)
                prep_template.artifact = instance
                study_id = prep_template.study_id

            # Associate the artifact with the study
            sql = """INSERT INTO qiita.study_artifact (study_id, artifact_id)
                     VALUES (%s, %s)"""
            sql_args = [study_id, a_id]
            TRN.add(sql, sql_args)

            # Associate the artifact with its filepaths
            fp_ids = insert_filepaths(filepaths, a_id, cls._table, "filepath")
            sql = """INSERT INTO qiita.artifact_filepath
                        (artifact_id, filepath_id)
                     VALUES (%s, %s)"""
            sql_args = [[a_id, fp_id] for fp_id in fp_ids]
            TRN.add(sql, sql_args)
            TRN.execute()

        return instance

    @classmethod
    def delete(cls, artifact_id):
        r""""""
        pass

    @property
    def timestamp(self):
        pass

    @property
    def processing_parameters(self):
        pass

    @property
    def visibility(self):
        pass

    @property
    def artifact_type(self):
        pass

    @property
    def can_be_submitted_to_ebi(self):
        pass

    @property
    def can_be_submitted_to_vamps(self):
        pass

    @property
    def is_submitted_to_vamps(self):
        pass

    @property
    def filepaths(self):
        pass

    @property
    def parents(self):
        pass

    @property
    def prep_template(self):
        pass

    @property
    def ebi_run_accessions(self):
        pass

    @property
    def study(self):
        pass
