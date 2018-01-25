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
from os import remove, makedirs
from os.path import isfile, exists, relpath
from shutil import rmtree
from functools import partial
from collections import namedtuple

import networkx as nx

import qiita_db as qdb

from qiita_core.qiita_settings import qiita_config


TypeNode = namedtuple('TypeNode', ['id', 'job_id', 'name', 'type'])


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
            [[artifact_type, description, can_be_submitted_to_ebi,
              can_be_submitted_to_vamps, can_be_raw], ...]
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT artifact_type, description,
                            can_be_submitted_to_ebi,
                            can_be_submitted_to_vamps, can_be_raw
                     FROM qiita.artifact_type
                     ORDER BY artifact_type"""
            qdb.sql_connection.TRN.add(sql)
            return qdb.sql_connection.TRN.execute_fetchindex()

    @staticmethod
    def create_type(name, description, can_be_submitted_to_ebi,
                    can_be_submitted_to_vamps, can_be_raw, filepath_types):
        """Creates a new artifact type in the system

        Parameters
        ----------
        name : str
            The artifact type name
        description : str
            The artifact type description
        can_be_submitted_to_ebi : bool
            Whether the artifact type can be submitted to EBI or not
        can_be_submitted_to_vamps : bool
            Whether the artifact type can be submitted to VAMPS or not
        can_be_raw : bool
            Whether the artifact type can be raw: upload directly to qiita
        filepath_types : list of (str, bool)
            The list filepath types that the new artifact type supports, and
            if they're required or not in an artifact instance of this type

        Raises
        ------
        qiita_db.exceptions.QiitaDBDuplicateError
            If an artifact type with the same name already exists
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(
                        SELECT *
                        FROM qiita.artifact_type
                        WHERE artifact_type=%s)"""
            qdb.sql_connection.TRN.add(sql, [name])
            if qdb.sql_connection.TRN.execute_fetchlast():
                raise qdb.exceptions.QiitaDBDuplicateError(
                    'artifact type', 'name: %s' % name)
            sql = """INSERT INTO qiita.artifact_type
                        (artifact_type, description, can_be_submitted_to_ebi,
                         can_be_submitted_to_vamps, can_be_raw)
                     VALUES (%s, %s, %s, %s, %s)
                     RETURNING artifact_type_id"""
            qdb.sql_connection.TRN.add(
                sql, [name, description, can_be_submitted_to_ebi,
                      can_be_submitted_to_vamps, can_be_raw])
            at_id = qdb.sql_connection.TRN.execute_fetchlast()
            sql = """INSERT INTO qiita.artifact_type_filepath_type
                        (artifact_type_id, filepath_type_id, required)
                     VALUES (%s, %s, %s)"""
            sql_args = [
                [at_id, qdb.util.convert_to_id(fpt, 'filepath_type'), req]
                for fpt, req in filepath_types]
            qdb.sql_connection.TRN.add(sql, sql_args, many=True)

            # When creating a type is expected that a new mountpoint is created
            # for that type, note that we are going to check if there is an
            # extra path for the mountpoint, which is useful for the test
            # environment
            qc = qiita_config
            mp = relpath(qc.working_dir, qc.base_data_dir).replace(
                'working_dir', '')
            mp = mp + name if mp != '/' and mp != '' else name
            sql = """INSERT INTO qiita.data_directory
                        (data_type, mountpoint, subdirectory, active)
                        VALUES (%s, %s, %s, %s)"""
            qdb.sql_connection.TRN.add(sql, [name, mp, True, True])

            # We are intersted in the dirpath
            dp = qdb.util.get_mountpoint(name)[0][1]
            if not exists(dp):
                makedirs(dp)

            qdb.sql_connection.TRN.execute()

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
                filepaths, a_id, atype, copy=True)
            sql = """INSERT INTO qiita.artifact_filepath
                        (artifact_id, filepath_id)
                     VALUES (%s, %s)"""
            sql_args = [[a_id, fp_id] for fp_id in fp_ids]
            qdb.sql_connection.TRN.add(sql, sql_args, many=True)
            qdb.sql_connection.TRN.execute()

        return instance

    @classmethod
    def create(cls, filepaths, artifact_type, name=None, prep_template=None,
               parents=None, processing_parameters=None, move_files=True,
               analysis=None, data_type=None):
        r"""Creates a new artifact in the system

        The parameters depend on how the artifact was generated:
            - If the artifact was uploaded by the user, the parameter
            `prep_template` should be provided and the parameters `parents`,
            `processing_parameters` and `analysis` should not be provided.
            - If the artifact was generated by processing one or more
            artifacts, the parameters `parents` and `processing_parameters`
            should be provided and the parameters `prep_template` and
            `analysis` should not be provided.
            - If the artifact is the initial artifact of the analysis, the
            parameters `analysis` and `data_type` should be provided and the
            parameters `prep_template`, `parents` and `processing_parameters`
            should not be provided.

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
            `parents` or `analysis` should be provided.
        parents : iterable of qiita_db.artifact.Artifact, optional
            The list of artifacts from which the new artifact has been
            generated. If not provided, `prep_template` or `analysis`
            should be provided.
        processing_parameters : qiita_db.software.Parameters, optional
            The processing parameters used to generate the new artifact
            from `parents`. It is required if `parents` is provided. It should
            not be provided if `processing_parameters` is not provided.
        move_files : bool, optional
            If False the files will not be moved but copied
        analysis : qiita_db.analysis.Analysis, optional
            If the artifact is the inital artifact of an analysis, the analysis
            to which the artifact belongs to. If not provided, `prep_template`
            or `parents` should be provided.
        data_type : str
            The data_type of the artifact in the `analysis`. It is required if
            `analysis` is provided. It should not be provided if `analysis` is
            not provided.

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
        The visibility of the artifact is set by default to `sandbox` if
        prep_template is passed but if parents is passed we will inherit the
        most closed visibility.
        The timestamp of the artifact is set by default to `datetime.now()`.
        The value of `submitted_to_vamps` is set by default to `False`.
        """
        # We need at least one file
        if not filepaths:
            raise qdb.exceptions.QiitaDBArtifactCreationError(
                "at least one filepath is required.")

        # Check that the combination of parameters is correct
        counts = (int(bool(parents or processing_parameters)) +
                  int(prep_template is not None) +
                  int(bool(analysis or data_type)))
        if counts != 1:
            # More than one parameter has been provided
            raise qdb.exceptions.QiitaDBArtifactCreationError(
                "One and only one of parents, prep template or analysis must "
                "be provided")
        elif bool(parents) != bool(processing_parameters):
            # When provided, parents and processing parameters both should be
            # provided (this is effectively doing an XOR)
            raise qdb.exceptions.QiitaDBArtifactCreationError(
                "When provided, both parents and processing parameters should "
                "be provided")
        elif bool(analysis) != bool(data_type):
            # When provided, analysis and data_type both should be
            # provided (this is effectively doing an XOR)
            raise qdb.exceptions.QiitaDBArtifactCreationError(
                "When provided, both analysis and data_type should "
                "be provided")

        # There are three different ways of creating an Artifact, but all of
        # them execute a set of common operations. Declare functions to avoid
        # code duplication. These functions should not be used outside of the
        # create function, hence declaring them here
        def _common_creation_steps(atype, cmd_id, data_type, cmd_parameters):
            gen_timestamp = datetime.now()
            visibility_id = qdb.util.convert_to_id("sandbox", "visibility")
            atype_id = qdb.util.convert_to_id(atype, "artifact_type")
            dtype_id = qdb.util.convert_to_id(data_type, "data_type")
            # Create the artifact row in the artifact table
            sql = """INSERT INTO qiita.artifact
                        (generated_timestamp, command_id, data_type_id,
                         command_parameters, visibility_id,
                         artifact_type_id, submitted_to_vamps)
                     VALUES (%s, %s, %s, %s, %s, %s, %s)
                     RETURNING artifact_id"""
            sql_args = [gen_timestamp, cmd_id, dtype_id,
                        cmd_parameters, visibility_id, atype_id, False]
            qdb.sql_connection.TRN.add(sql, sql_args)
            a_id = qdb.sql_connection.TRN.execute_fetchlast()
            qdb.sql_connection.TRN.execute()

            return cls(a_id)

        def _associate_with_study(instance, study_id):
            # Associate the artifact with the study
            sql = """INSERT INTO qiita.study_artifact
                        (study_id, artifact_id)
                     VALUES (%s, %s)"""
            sql_args = [study_id, instance.id]
            qdb.sql_connection.TRN.add(sql, sql_args)
            qdb.sql_connection.TRN.execute()

        def _associate_with_analysis(instance, analysis_id):
            # Associate the artifact with the analysis
            sql = """INSERT INTO qiita.analysis_artifact
                        (analysis_id, artifact_id)
                     VALUES (%s, %s)"""
            sql_args = [analysis_id, instance.id]
            qdb.sql_connection.TRN.add(sql, sql_args)
            qdb.sql_connection.TRN.execute()

        with qdb.sql_connection.TRN:
            if parents:
                dtypes = {p.data_type for p in parents}
                # If an artifact has parents, it can be either from the
                # processing pipeline or the analysis pipeline. Decide which
                # one here
                studies = {p.study for p in parents}
                analyses = {p.analysis for p in parents}
                studies.discard(None)
                analyses.discard(None)
                studies = {s.id for s in studies}
                analyses = {a.id for a in analyses}

                # The first 2 cases should never happen, but it doesn't hurt
                # to check them
                len_studies = len(studies)
                len_analyses = len(analyses)
                if len_studies > 0 and len_analyses > 0:
                    raise qdb.exceptions.QiitaDBArtifactCreationError(
                        "All the parents from an artifact should be either "
                        "from the analysis pipeline or all from the processing"
                        " pipeline")
                elif len_studies > 1 or len_studies > 1:
                    raise qdb.exceptions.QiitaDBArtifactCreationError(
                        "Parents from multiple studies/analyses provided. "
                        "Analyses: %s. Studies: %s."
                        % (', '.join(analyses), ', '.join(studies)))
                elif len_studies == 1:
                    # This artifact is part of the processing pipeline
                    study_id = studies.pop()
                    # In the processing pipeline, artifacts can have only
                    # one dtype
                    if len(dtypes) > 1:
                        raise qdb.exceptions.QiitaDBArtifactCreationError(
                            "parents have multiple data types: %s"
                            % ", ".join(dtypes))

                    instance = _common_creation_steps(
                        artifact_type, processing_parameters.command.id,
                        dtypes.pop(), processing_parameters.dump())

                    _associate_with_study(instance, study_id)
                else:
                    # This artifact is part of the analysis pipeline
                    analysis_id = analyses.pop()
                    # In the processing pipeline, artifact parents can have
                    # more than one data type
                    data_type = ("Multiomic"
                                 if len(dtypes) > 1 else dtypes.pop())
                    instance = _common_creation_steps(
                        artifact_type, processing_parameters.command.id,
                        data_type, processing_parameters.dump())
                    _associate_with_analysis(instance, analysis_id)

                # Associate the artifact with its parents
                sql = """INSERT INTO qiita.parent_artifact
                            (artifact_id, parent_id)
                         VALUES (%s, %s)"""
                sql_args = [(instance.id, p.id) for p in parents]
                qdb.sql_connection.TRN.add(sql, sql_args, many=True)

                # inheriting visibility
                visibilities = {a.visibility for a in instance.parents}
                # set based on the "lowest" visibility
                if 'sandbox' in visibilities:
                    instance.visibility = 'sandbox'
                elif 'private' in visibilities:
                    instance.visibility = 'private'
                else:
                    instance.visibility = 'public'

            elif prep_template:
                # This artifact is uploaded by the user in the
                # processing pipeline
                instance = _common_creation_steps(
                    artifact_type, None, prep_template.data_type(), None)
                # Associate the artifact with the prep template
                prep_template.artifact = instance
                # Associate the artifact with the study
                _associate_with_study(instance, prep_template.study_id)
            else:
                # This artifact is an initial artifact of an analysis
                instance = _common_creation_steps(
                    artifact_type, None, data_type, None)
                # Associate the artifact with the analysis
                analysis.add_artifact(instance)

            # Associate the artifact with its filepaths
            fp_ids = qdb.util.insert_filepaths(
                filepaths, instance.id, artifact_type,
                move_files=move_files, copy=(not move_files))
            sql = """INSERT INTO qiita.artifact_filepath
                        (artifact_id, filepath_id)
                     VALUES (%s, %s)"""
            sql_args = [[instance.id, fp_id] for fp_id in fp_ids]
            qdb.sql_connection.TRN.add(sql, sql_args, many=True)

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
            sql = """SELECT processing_job_id
                     FROM qiita.artifact_processing_job
                         JOIN qiita.processing_job USING (processing_job_id)
                         JOIN qiita.processing_job_status
                             USING (processing_job_status_id)
                     WHERE artifact_id = %s
                         AND processing_job_status IN (
                             'queued', 'running', 'waiting')"""
            qdb.sql_connection.TRN.add(sql, [artifact_id])
            jobs = qdb.sql_connection.TRN.execute_fetchflatten()
            if jobs:
                # if the artifact has active jobs we need to raise an error
                # but we also need to check that if it's only 1 job, that the
                # job is not the delete_artifact actual job
                raise_error = True
                job_name = qdb.processing_job.ProcessingJob(
                    jobs[0]).command.name
                if len(jobs) == 1 and job_name == 'delete_artifact':
                    raise_error = False
                if raise_error:
                    raise qdb.exceptions.QiitaDBArtifactDeletionError(
                        artifact_id, "there is a queued/running job that "
                        "uses this artifact")

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

            # Delete the entry from the artifact_output_processing_job table
            sql = """DELETE FROM qiita.artifact_output_processing_job
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [artifact_id])

            # Detach the artifact from its filepaths
            sql = """DELETE FROM qiita.artifact_filepath
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [artifact_id])

            # If the artifact doesn't have parents and study is not None (is an
            # analysis), we move the files to the uploads folder. We also need
            # to nullify the column in the prep template table
            if not instance.parents and study is not None:
                qdb.util.move_filepaths_to_upload_folder(
                    study.id, filepaths)

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

            # Detach the artifact from the analysis_artifact table
            sql = "DELETE FROM qiita.analysis_artifact WHERE artifact_id = %s"
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

        Notes
        -----
        The visibility of an artifact is propagated to its ancestors, but it
        only applies when the new visibility is more open than before.
        """
        with qdb.sql_connection.TRN:
            # In order to correctly propagate the visibility we need to find
            # the root of this artifact and then propagate to all the artifacts
            sql = "SELECT * FROM qiita.find_artifact_roots(%s)"
            qdb.sql_connection.TRN.add(sql, [self.id])
            root_id = qdb.sql_connection.TRN.execute_fetchlast()
            root = qdb.artifact.Artifact(root_id)
            # these are the ids of all the children from the root
            ids = [a.id for a in root.descendants.nodes()]

            sql = """UPDATE qiita.artifact
                     SET visibility_id = %s
                     WHERE artifact_id IN %s"""
            vis_id = qdb.util.convert_to_id(value, "visibility")
            qdb.sql_connection.TRN.add(sql, [vis_id, tuple(ids)])
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

    def set_html_summary(self, html_fp, support_dir=None):
        """Sets the HTML summary of the artifact

        Parameters
        ----------
        html_fp : str
            Path to the new HTML summary
        support_dir : str
            Path to the directory containing any support files needed by
            the HTML file
        """
        with qdb.sql_connection.TRN:
            if self.html_summary_fp:
                # Delete the current HTML summary
                to_delete_ids = []
                to_delete_fps = []
                for fp_id, fp, fp_type in self.filepaths:
                    if fp_type in ('html_summary', 'html_summary_dir'):
                        to_delete_ids.append([fp_id])
                        to_delete_fps.append(fp)
                # From the artifact_filepath table
                sql = """DELETE FROM qiita.artifact_filepath
                         WHERE filepath_id = %s"""
                qdb.sql_connection.TRN.add(sql, to_delete_ids, many=True)
                # From the filepath table
                sql = "DELETE FROM qiita.filepath WHERE filepath_id=%s"
                qdb.sql_connection.TRN.add(sql, to_delete_ids, many=True)
                # And from the filesystem only after the transaction is
                # successfully completed (after commit)

                def path_cleaner(fp):
                    if isfile(fp):
                        remove(fp)
                    else:
                        rmtree(fp)
                qdb.sql_connection.TRN.add_post_commit_func(
                    partial(map, path_cleaner, to_delete_fps))

            # Add the new HTML summary
            filepaths = [(html_fp, 'html_summary')]
            if support_dir is not None:
                filepaths.append((support_dir, 'html_summary_dir'))
            fp_ids = qdb.util.insert_filepaths(
                filepaths, self.id, self.artifact_type)
            sql = """INSERT INTO qiita.artifact_filepath
                        (artifact_id, filepath_id)
                     VALUES (%s, %s)"""
            sql_args = [[self.id, id_] for id_ in fp_ids]
            qdb.sql_connection.TRN.add(sql, sql_args, many=True)
            qdb.sql_connection.TRN.execute()

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
    def descendants_with_jobs(self):
        """Returns the descendants of the artifact with their jobs

        Returns
        -------
        networkx.DiGraph
            The descendants of the artifact
        """
        def _add_edge(edges, src, dest):
            """Aux function to add the edge (src, dest) to edges"""
            edge = (src, dest)
            if edge not in edges:
                edges.add(edge)

        with qdb.sql_connection.TRN:
            sql = """SELECT processing_job_id, input_id, output_id
                     FROM qiita.artifact_descendants_with_jobs(%s)"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            sql_edges = qdb.sql_connection.TRN.execute_fetchindex()

            lineage = nx.DiGraph()
            edges = set()
            nodes = {}
            if sql_edges:
                for jid, pid, cid in sql_edges:
                    if jid not in nodes:
                        nodes[jid] = ('job',
                                      qdb.processing_job.ProcessingJob(jid))
                    if pid not in nodes:
                        nodes[pid] = ('artifact', qdb.artifact.Artifact(pid))
                    if cid not in nodes:
                        nodes[cid] = ('artifact', qdb.artifact.Artifact(cid))
                    edges.add((nodes[pid], nodes[jid]))
                    edges.add((nodes[jid], nodes[cid]))
            else:
                nodes[self.id] = ('artifact', self)
                lineage.add_node(nodes[self.id])

            # The code above returns all the jobs that have been successfully
            # executed. We need to add all the jobs that are in all the other
            # status. Approach: Loop over all the artifacts and add all the
            # jobs that have been attached to them.
            visited = set()
            queue = nodes.keys()
            while queue:
                current = queue.pop(0)
                if current not in visited:
                    visited.add(current)
                    n_type, n_obj = nodes[current]
                    if n_type == 'artifact':
                        # Add all the jobs to the queue
                        for job in n_obj.jobs():
                            queue.append(job.id)
                            if job.id not in nodes:
                                nodes[job.id] = ('job', job)

                    elif n_type == 'job':
                        # Ignore the generate summary jobs
                        if n_obj.command.name == 'Generate HTML summary':
                            continue
                        jstatus = n_obj.status
                        # If the job is in success we don't need to do anything
                        # else since it would've been added by the code above
                        if jstatus != 'success':
                            # Connect the job with his input artifacts, the
                            # input artifacts may or may not exist yet, so we
                            # need to check both the input_artifacts and the
                            # pending properties
                            for in_art in n_obj.input_artifacts:
                                _add_edge(edges, nodes[in_art.id],
                                          nodes[n_obj.id])

                            pending = n_obj.pending
                            for pred_id in pending:
                                for pname in pending[pred_id]:
                                    in_node_id = '%s:%s' % (
                                        pred_id, pending[pred_id][pname])
                                    _add_edge(edges, nodes[in_node_id],
                                              nodes[n_obj.id])

                            if jstatus != 'error':
                                # If the job is not errored, we can add the
                                # future outputs and the children jobs to
                                # the graph.

                                # Add all the job outputs as new nodes
                                for o_name, o_type in n_obj.command.outputs:
                                    node_id = '%s:%s' % (n_obj.id, o_name)
                                    node = TypeNode(
                                        id=node_id, job_id=n_obj.id,
                                        name=o_name, type=o_type)
                                    queue.append(node_id)
                                    if node_id not in nodes:
                                        nodes[node_id] = ('type', node)

                                # Add all his children jobs to the queue
                                for cjob in n_obj.children:
                                    queue.append(cjob.id)
                                    if cjob.id not in nodes:
                                        nodes[cjob.id] = ('job', cjob)
                    elif n_type == 'type':
                        # Connect this 'future artifact' with the job that will
                        # generate it
                        _add_edge(edges, nodes[n_obj.job_id], nodes[current])
                    else:
                        raise ValueError('Unrecognized type: %s' % n_type)

        # Add all edges to the lineage graph - adding the edges creates the
        # nodes in networkx
        for source, dest in edges:
            lineage.add_edge(source, dest)

        return lineage

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
        qiita_db.study.Study or None
            The study that owns the artifact, if any
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT study_id
                     FROM qiita.study_artifact
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            res = qdb.sql_connection.TRN.execute_fetchindex()
            return qdb.study.Study(res[0][0]) if res else None

    @property
    def analysis(self):
        """The analysis to which the artifact belongs to

        Returns
        -------
        qiita_db.analysis.Analysis or None
            The analysis that owns the artifact, if any
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT analysis_id
                     FROM qiita.analysis_artifact
                     WHERE artifact_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            res = qdb.sql_connection.TRN.execute_fetchindex()
            return qdb.analysis.Analysis(res[0][0]) if res else None

    def jobs(self, cmd=None, status=None, show_hidden=False):
        """Jobs that used this artifact as input

        Parameters
        ----------
        cmd : qiita_db.software.Command, optional
            If provided, only jobs that executed this command will be returned
        status : str, optional
            If provided, only jobs in this status will be returned
        show_hidden : bool, optional
            If true, return also the "hidden" jobs

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

            if not show_hidden:
                sql = "{} AND hidden = %s".format(sql)
                sql_args.append(False)

            qdb.sql_connection.TRN.add(sql, sql_args)
            return [qdb.processing_job.ProcessingJob(jid)
                    for jid in qdb.sql_connection.TRN.execute_fetchflatten()]
