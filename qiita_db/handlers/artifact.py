# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from collections import defaultdict
from json import dumps, loads

from tornado.web import HTTPError

import qiita_db as qdb
from qiita_core.qiita_settings import r_client

from .oauth2 import OauthBaseHandler, authenticate_oauth


def _get_artifact(a_id):
    """Returns the artifact with the given id if it exists

    Parameters
    ----------
    a_id : str
        The artifact id

    Returns
    -------
    qiita_db.artifact.Artifact
        The requested artifact

    Raises
    ------
    HTTPError
        If the artifact does not exist, with error code 404
        If there is a problem instantiating the artifact, with error code 500
    """
    try:
        a_id = int(a_id)
        artifact = qdb.artifact.Artifact(a_id)
    except qdb.exceptions.QiitaDBUnknownIDError:
        raise HTTPError(404)
    except Exception as e:
        raise HTTPError(
            500, reason="Error instantiating artifact %s: %s" % (a_id, str(e))
        )

    return artifact


class ArtifactHandler(OauthBaseHandler):
    @authenticate_oauth
    def get(self, artifact_id):
        """Retrieves the artifact information

        Parameters
        ----------
        artifact_id : str
            The id of the artifact whose information is being retrieved

        Returns
        -------
        dict
            The artifact information:
            'name': artifact name
            'timestamp': artifact creation timestamp
            'visibility': artifact visibility
            'type': artifact type
            'data_type': artifact data type
            'can_be_submitted_to_ebi': if the artifact can be submitted to ebi
            'ebi_run_accessions': dict with the EBI run accessions attached to
                the artifact
            'can_be_submitted_to_vamps': if the artifact can be submitted to
                vamps
            'is_submitted_to_vamps': whether the artifact has been submitted
                to vamps or not
            'prep_information': list of prep information ids
            'study': the study id
            'processing_parameters': dict with the processing parameters used
                to generate the artifact or None
            'files': dict with the artifact files, keyed by filepath type
            'parents': list of the parents artifact ids
        """
        with qdb.sql_connection.TRN:
            artifact = _get_artifact(artifact_id)
            study = artifact.study
            analysis = artifact.analysis
            response = {
                "name": artifact.name,
                "timestamp": str(artifact.timestamp),
                "visibility": artifact.visibility,
                "type": artifact.artifact_type,
                "data_type": artifact.data_type,
                "can_be_submitted_to_ebi": artifact.can_be_submitted_to_ebi,
                "can_be_submitted_to_vamps": artifact.can_be_submitted_to_vamps,
                "prep_information": [p.id for p in artifact.prep_templates],
                "study": study.id if study else None,
                "analysis": analysis.id if analysis else None,
                "parents": [p.id for p in artifact.parents],
            }
            params = artifact.processing_parameters
            response["processing_parameters"] = (
                params.values if params is not None else None
            )

            response["ebi_run_accessions"] = (
                artifact.ebi_run_accessions
                if response["can_be_submitted_to_ebi"]
                else None
            )
            response["is_submitted_to_vamps"] = (
                artifact.is_submitted_to_vamps
                if response["can_be_submitted_to_vamps"]
                else None
            )

            # Instead of sending a list of files, provide the files as a
            # dictionary keyed by filepath type
            response["files"] = defaultdict(list)
            for x in artifact.filepaths:
                response["files"][x["fp_type"]].append(
                    {"filepath": x["fp"], "size": x["fp_size"]}
                )

        self.write(response)

    @authenticate_oauth
    def patch(self, artifact_id):
        """Patches the artifact information

        Parameter
        ---------
        artifact_id : str
            The id of the artifact whose information is being updated
        """
        req_op = self.get_argument("op")
        req_path = self.get_argument("path")
        req_value = self.get_argument("value")

        if req_op == "add":
            req_path = [v for v in req_path.split("/") if v]
            if len(req_path) != 1 or req_path[0] != "html_summary":
                raise HTTPError(400, reason="Incorrect path parameter value")
            else:
                artifact = _get_artifact(artifact_id)

                try:
                    html_data = loads(req_value)
                    html_fp = html_data["html"]
                    html_dir = html_data["dir"]
                except ValueError:
                    html_fp = req_value
                    html_dir = None

                try:
                    artifact.set_html_summary(html_fp, html_dir)
                except Exception as e:
                    raise HTTPError(500, reason=str(e))
        else:
            raise HTTPError(
                400,
                reason='Operation "%s" not supported. '
                "Current supported operations: add" % req_op,
            )

        self.finish()


class ArtifactAPItestHandler(OauthBaseHandler):
    @authenticate_oauth
    def post(self):
        """Creates a new artifact

        Parameters
        ----------
        filepaths : str
            Json string with a list of filepaths and its types
        type : str
            The artifact type
        prep_template: int
            The id of the template that the new artifact belongs to
        name : str, optional
            The artifact name

        Returns
        -------
        dict
            'artifact': the id of the new artifact

        See Also
        --------
        qiita_db.artifact.Artifact.create
        """
        filepaths = loads(self.get_argument("filepaths"))
        artifact_type = self.get_argument("type")
        prep_template = self.get_argument("prep", None)
        analysis = self.get_argument("analysis", None)
        name = self.get_argument("name", None)
        dtype = self.get_argument("data_type", None)
        parents = self.get_argument("parents", None)
        job_id = self.get_argument("job_id", None)

        if prep_template is not None:
            prep_template = qdb.metadata_template.prep_template.PrepTemplate(
                prep_template
            )
            dtype = None
        if analysis is not None:
            analysis = qdb.analysis.Analysis(analysis)
        if parents is not None:
            # remember that this method is only accessed via the tests so
            # to load an artifact with parents, the easiest it to use
            # the job_id that is being used for testing and passed as a
            # parameter
            parents = [qdb.artifact.Artifact(p) for p in loads(parents)]
            pp = qdb.processing_job.ProcessingJob(job_id).parameters
        else:
            pp = None

        a = qdb.artifact.Artifact.create(
            filepaths,
            artifact_type,
            name=name,
            prep_template=prep_template,
            parents=parents,
            processing_parameters=pp,
            analysis=analysis,
            data_type=dtype,
        )

        self.write({"artifact": a.id})


class ArtifactTypeHandler(OauthBaseHandler):
    @authenticate_oauth
    def get(self):
        """Returns the artifact types and their local mountpoint location

        Returns
        -------
        dict
            'artifact_type': local mountpoint
        """
        atypes = dict()
        for atype in qdb.util.get_artifact_types():
            mountpoints = qdb.util.get_mountpoint(atype)
            if mountpoints:
                # [0][1]: get latest/active and the actual location
                atypes[atype] = mountpoints[0][1]
        # add the upload location
        atypes["uploads"] = qdb.util.get_mountpoint("uploads")[0][1]

        self.write(atypes)

    @authenticate_oauth
    def post(self):
        """Creates a new artifact type

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
        is_user_uploadable : bool
            Whether the artifact type can be raw: direct upload to qiita
        filepath_types : list of (str, bool)
            The list filepath types that the new artifact type supports, and
            if they're required or not in an artifact instance of this type
        """
        a_type = self.get_argument("type_name")
        a_desc = self.get_argument("description")
        ebi = self.get_argument("can_be_submitted_to_ebi")
        vamps = self.get_argument("can_be_submitted_to_vamps")
        raw = self.get_argument("is_user_uploadable")
        fp_types = loads(self.get_argument("filepath_types"))

        try:
            qdb.artifact.Artifact.create_type(a_type, a_desc, ebi, vamps, raw, fp_types)
        except qdb.exceptions.QiitaDBDuplicateError:
            # Ignoring this error as we want this endpoint in the rest api
            # to be idempotent.
            self.set_status(200, reason="Artifact type already exists")

        self.finish()


class APIArtifactHandler(OauthBaseHandler):
    @authenticate_oauth
    def post(self):
        user_email = self.get_argument("user_email")
        job_id = self.get_argument("job_id", None)
        prep_id = self.get_argument("prep_id", None)
        atype = self.get_argument("artifact_type")
        aname = self.get_argument("command_artifact_name", "Name")
        files = self.get_argument("files")
        add_default_workflow = self.get_argument("add_default_workflow", False)

        if job_id is None and prep_id is None:
            raise HTTPError(400, reason="You need to specify a job_id or a prep_id")
        if job_id is not None and prep_id is not None:
            raise HTTPError(
                400, reason="You need to specify only a job_id or a prep_id"
            )

        user = qdb.user.User(user_email)
        values = {
            "files": files,
            "artifact_type": atype,
            "name": aname,
            # leaving here in case we need to add a way to add an artifact
            # directly to an analysis, for more information see
            # ProcessingJob._complete_artifact_transformation
            "analysis": None,
        }
        PJ = qdb.processing_job.ProcessingJob
        if job_id is not None:
            TN = qdb.sql_connection.TRN
            job = PJ(job_id)
            with TN:
                sql = """SELECT command_output_id
                         FROM qiita.command_output
                         WHERE name = %s AND command_id = %s"""
                TN.add(sql, [aname, job.command.id])
                results = TN.execute_fetchflatten()
                if len(results) < 1:
                    raise HTTPError(
                        400, "The command_artifact_name does not exist in the command"
                    )
                cmd_out_id = results[0]
            provenance = {
                "job": job_id,
                "cmd_out_id": cmd_out_id,
                # direct_creation is a flag to avoid having to wait
                # for the complete job to create the new artifact,
                # which is normally ran during regular processing.
                # Skipping is fine because we are adding an artifact
                # to an existing job outside of regular processing
                "direct_creation": True,
                "name": aname,
            }
            values["provenance"] = dumps(provenance)
            # inherint the first prep info file from the first input artifact
            prep_id = job.input_artifacts[0].prep_templates[0].id
        else:
            prep_id = int(prep_id)

        values["template"] = prep_id
        cmd = qdb.software.Command.get_validator(atype)
        params = qdb.software.Parameters.load(cmd, values_dict=values)
        if add_default_workflow or add_default_workflow == "True":
            pwk = qdb.processing_job.ProcessingWorkflow.from_scratch(
                user, params, name=f"ProcessingWorkflow for {prep_id}"
            )
            # the new job is the first job in the workflow
            new_job = list(pwk.graph.nodes())[0]
            # adding default pipeline to the preparation
            pt = qdb.metadata_template.prep_template.PrepTemplate(prep_id)
            pt.add_default_workflow(user, pwk)
            pwk.submit()
        else:
            new_job = PJ.create(user, params, True)
            new_job.submit()

        r_client.set(
            "prep_template_%d" % prep_id,
            dumps({"job_id": new_job.id, "is_qiita_job": True}),
        )

        self.finish({"job_id": new_job.id})
