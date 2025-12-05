# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from functools import partial
from itertools import chain
from json import dumps
from os.path import join

from qiita_core.qiita_settings import qiita_config, r_client
from qiita_core.util import execute_as_transaction
from qiita_db.artifact import Artifact
from qiita_db.exceptions import QiitaDBError
from qiita_db.logger import LogEntry
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.processing_job import ProcessingJob
from qiita_db.software import Command, Parameters, Software
from qiita_db.user import User
from qiita_db.util import get_artifacts_information, get_mountpoint, get_visibilities
from qiita_pet.handlers.api_proxy.util import check_access, check_fp

PREP_TEMPLATE_KEY_FORMAT = "prep_template_%s"


def artifact_get_req(user_id, artifact_id):
    """Returns all base information about an artifact

    Parameters
    ----------
    user_id : str
        user making the request
    artifact_id : int or str coercable to int
        Atrtifact to get information for

    Returns
    -------
    dict of objects
        A dictionary containing the artifact information
        {'status': status,
         'message': message,
         'artifact': {info key: val, ...}}
    """
    artifact_id = int(artifact_id)
    artifact = Artifact(artifact_id)

    access_error = check_access(artifact.study.id, user_id)
    if access_error:
        return access_error

    can_submit_ebi = artifact.can_be_submitted_to_ebi
    ebi_run_accessions = artifact.ebi_run_accessions if can_submit_ebi else None
    can_submit_vamps = artifact.can_be_submitted_to_vamps
    is_submitted_vamps = artifact.is_submitted_to_vamps if can_submit_vamps else False

    return {
        "id": artifact_id,
        "timestamp": artifact.timestamp,
        "processing_parameters": artifact.processing_parameters,
        "visibility": artifact.visibility,
        "type": artifact.artifact_type,
        "data_type": artifact.data_type,
        "filepaths": artifact.filepaths,
        "parents": [a.id for a in artifact.parents],
        "study": artifact.study.id if artifact.study else None,
        "can_submit_ebi": can_submit_ebi,
        "ebi_run_accessions": ebi_run_accessions,
        "can_submit_vamps": can_submit_vamps,
        "is_submitted_vamps": is_submitted_vamps,
    }


@execute_as_transaction
def artifact_get_prep_req(user_id, artifact_ids):
    """Returns all prep info sample ids for the given artifact_ids

    Parameters
    ----------
    user_id : str
        user making the request
    artifact_ids : list of int
        list of artifact ids

    Returns
    -------
    dict of objects
        A dictionary containing the artifact information
        {'status': status,
         'message': message,
         'data': {artifact_id: [prep info sample ids]}
    """
    samples = {}

    for aid in sorted(artifact_ids):
        artifact = Artifact(aid)
        access_error = check_access(artifact.study.id, user_id)
        if access_error:
            return access_error

        samples[aid] = list(
            chain(*[sorted(pt.keys()) for pt in Artifact(aid).prep_templates])
        )

    return {"status": "success", "msg": "", "data": samples}


@execute_as_transaction
def artifact_get_info(user_id, artifact_ids, only_biom=True):
    """Returns all artifact info for the given artifact_ids

    Parameters
    ----------
    user_id : str
        user making the request
    artifact_ids : list of int
        list of artifact ids
    only_biom : bool
        If true only the biom artifacts are retrieved

    Returns
    -------
    dict of objects
        A dictionary containing the artifact information
        {'status': status,
         'message': message,
         'data': {artifact_id: {biom_info}}
    """
    artifact_info = {}

    artifact_info = get_artifacts_information(artifact_ids, only_biom)

    return {"status": "success", "msg": "", "data": artifact_info}


@execute_as_transaction
def artifact_post_req(
    user_id, filepaths, artifact_type, name, prep_template_id, artifact_id=None
):
    """Creates the initial artifact for the prep template

    Parameters
    ----------
    user_id : str
        User adding the atrifact
    filepaths : dict of str
        Comma-separated list of files to attach to the artifact,
        keyed by file type
    artifact_type : str
        The type of the artifact
    name : str
        Name to give the artifact
    prep_template_id : int or str castable to int
        Prep template to attach the artifact to
    artifact_id : int or str castable to int, optional
        The id of the imported artifact

    Returns
    -------
    dict of objects
        A dictionary containing the new artifact ID
        {'status': status,
         'message': message,
         'artifact': id}
    """
    prep_template_id = int(prep_template_id)
    prep = PrepTemplate(prep_template_id)
    study_id = prep.study_id

    # First check if the user has access to the study
    access_error = check_access(study_id, user_id)
    if access_error:
        return access_error

    user = User(user_id)

    if artifact_id:
        # if the artifact id has been provided, import the artifact
        qiita_plugin = Software.from_name_and_version("Qiita", "alpha")
        cmd = qiita_plugin.get_command("copy_artifact")
        params = Parameters.load(
            cmd, values_dict={"artifact": artifact_id, "prep_template": prep.id}
        )
        job = ProcessingJob.create(user, params, True)
    else:
        uploads_path = get_mountpoint("uploads")[0][1]
        path_builder = partial(join, uploads_path, str(study_id))
        cleaned_filepaths = {}

        for ftype, file_list in filepaths.items():
            # JavaScript sends us this list as a comma-separated list
            for fp in file_list.split(","):
                # JavaScript will send this value as an empty string if the
                # list of files was empty. In such case, the split will
                # generate a single element containing the empty string. Check
                # for that case here and, if fp is not the empty string,
                # proceed to check if the file exists
                if fp:
                    # Check if filepath being passed exists for study
                    full_fp = path_builder(fp)
                    exists = check_fp(study_id, full_fp)
                    if exists["status"] != "success":
                        return {
                            "status": "error",
                            "message": "File does not exist: %s" % fp,
                        }
                    if ftype not in cleaned_filepaths:
                        cleaned_filepaths[ftype] = []
                    cleaned_filepaths[ftype].append(full_fp)

        # This should never happen, but it doesn't hurt to actually have
        # a explicit check, in case there is something odd with the JS
        if not cleaned_filepaths:
            return {
                "status": "error",
                "message": "Can't create artifact, no files provided.",
            }

        # This try/except will catch the case when the plugins are not
        # activated so there is no Validate for the given artifact_type
        try:
            command = Command.get_validator(artifact_type)
        except QiitaDBError as e:
            return {"status": "error", "message": str(e)}
        job = ProcessingJob.create(
            user,
            Parameters.load(
                command,
                values_dict={
                    "template": prep_template_id,
                    "files": dumps(cleaned_filepaths),
                    "artifact_type": artifact_type,
                    "name": name,
                    "analysis": None,
                },
            ),
            True,
        )

    # Submit the job
    job.submit()

    r_client.set(
        PREP_TEMPLATE_KEY_FORMAT % prep.id,
        dumps({"job_id": job.id, "is_qiita_job": True}),
    )

    return {"status": "success", "message": ""}


def artifact_types_get_req():
    """Gets artifact types and descriptions available

    Returns
    -------
    dict of objects
        {'status': status,
         'message': message,
         'types': [[str, str], ...]}
        types holds type and description of the artifact type, in the form
        [[artifact_type, description], ...]
    """
    return {"status": "success", "message": "", "types": Artifact.types()}


def artifact_graph_get_req(artifact_id, direction, user_id):
    """Creates graphs of ancestor or descendant artifacts from given one

    Parameters
    ----------
    artifact_id : int
        Artifact ID to get graph for
    direction : {'ancestors', 'descendants'}
        What direction to get the graph in

    Returns
    -------
    dict of lists of tuples
        A dictionary containing the edge list representation of the graph,
        and the node labels. Formatted as:
        {'status': status,
         'message': message,
         'edge_list': [(0, 1), (0, 2)...],
         'node_labels': [(0, 'label0'), (1, 'label1'), ...]}

    Notes
    -----
    Nodes are identified by the corresponding Artifact ID.
    """
    access_error = check_access(Artifact(artifact_id).study.id, user_id)
    if access_error:
        return access_error

    if direction == "descendants":
        G = Artifact(int(artifact_id)).descendants
    elif direction == "ancestors":
        G = Artifact(int(artifact_id)).ancestors
    else:
        return {"status": "error", "message": "Unknown directon %s" % direction}

    node_labels = [(n.id, " - ".join([n.name, n.artifact_type])) for n in G.nodes()]
    return {
        "edge_list": [(n.id, m.id) for n, m in G.edges()],
        "node_labels": node_labels,
        "status": "success",
        "message": "",
    }


def artifact_status_put_req(artifact_id, user_id, visibility):
    """Set the status of the artifact given

    Parameters
    ----------
    artifact_id : int
        Artifact being acted on
    user_id : str
        The user requesting the action
    visibility : {'sandbox', 'awaiting_approval', 'private', 'public'}
        What to change the visibility to

    Returns
    -------
    dict
        Status of action, in the form {'status': status, 'message': msg}
        status: status of the action, either success or error
        message: Human readable message for status
    """
    if visibility not in get_visibilities():
        return {
            "status": "error",
            "message": "Unknown visibility value: %s" % visibility,
        }

    pd = Artifact(int(artifact_id))
    sid = pd.study.id
    access_error = check_access(sid, user_id)
    if access_error:
        return access_error
    user = User(str(user_id))
    status = "success"
    msg = "Artifact visibility changed to %s" % visibility
    # Set the approval to private if needs approval and admin
    if visibility == "private":
        if not qiita_config.require_approval:
            pd.visibility = "private"
        # Set the approval to private if approval not required
        elif user.level == "admin":
            pd.visibility = "private"
        # Trying to set approval without admin privileges
        else:
            status = "error"
            msg = "User does not have permissions to approve change"
    else:
        pd.visibility = visibility

    LogEntry.create(
        "Warning",
        "%s changed artifact %s (study %d) to %s"
        % (user_id, artifact_id, sid, visibility),
    )

    return {"status": status, "message": msg}
