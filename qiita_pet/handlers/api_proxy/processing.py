# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from collections import defaultdict
from json import dumps, loads

from qiita_db.artifact import Artifact
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.processing_job import ProcessingJob, ProcessingWorkflow
from qiita_db.software import Command, DefaultParameters, Parameters
from qiita_db.user import User


def list_commands_handler_get_req(id, exclude_analysis):
    """Retrieves the commands that can process the given artifact types

    Parameters
    ----------
    id : string
        id, it can be the integer or the name of the artifact:network-root
    exclude_analysis : bool
        If True, return commands that are not part of the analysis pipeline

    Returns
    -------
    dict of objects
        A dictionary containing the commands information
        {'status': str,
         'message': str,
         'commands': list of dicts of {'id': int,
                                       'command': str,
                                       'output': list of [str, str]}}
    """
    if id.isdigit():
        commands = Artifact(id).get_commands
    else:
        pieces = id.split(":")
        if len(pieces) == 1:
            aid = pieces[0]
            root = ""
        else:
            aid = pieces[0]
            root = pieces[1]
        prep_type = None
        if root.isdigit():
            artifact = Artifact(root)
            if artifact.analysis is None:
                prep_type = artifact.prep_templates[0].data_type

        commands = Command.get_commands_by_input_type(
            [aid], exclude_analysis=exclude_analysis, prep_type=prep_type
        )

    cmd_info = [
        {"id": cmd.id, "command": cmd.name, "output": cmd.outputs} for cmd in commands
    ]

    return {"status": "success", "message": "", "commands": cmd_info}


def list_options_handler_get_req(command_id, artifact_id=None):
    """Returns the available default parameters set for the given command

    Parameters
    ----------
    command_id : int
        The command id
    artifact_id : int, optional
        The artifact id so to limit options based on how it has already been
        processed

    Returns
    -------
    dict of objects
        A dictionary containing the commands information
        {'status': str,
         'message': str,
         'options': list of dicts of {'id: str',
                                      'name': str,
                                      'values': dict of {str: str}},
         'req_options': dict,
         'opt_options': dict,
         'extra_artifacts': dict}
    """

    def _helper_process_params(params):
        return dumps({k: str(v).lower() for k, v in params.items()}, sort_keys=True)

    command = Command(command_id)
    rparamers = []
    extra_atypes = []
    analysis = None
    for name, (type, atype) in command.required_parameters.items():
        rparamers.append(name)
        # [0] cause there is only one element
        extra_atypes.append(atype[0])

    eparams = []
    extra_artifacts = defaultdict(list)
    if artifact_id is not None:
        artifact = Artifact(artifact_id)
        analysis = artifact.analysis
        for job in artifact.jobs(cmd=command):
            jstatus = job.status
            outputs = job.outputs if job.status == "success" else None
            # this ignore any jobs that weren't successful or are in
            # construction, or the results have been deleted [outputs == {}]
            if jstatus not in {"success", "in_construction"} or outputs == {}:
                continue
            params = job.parameters.values.copy()
            for k in rparamers:
                del params[k]
            eparams.append(_helper_process_params(params))

        # removing this artifact from extra_atypes
        if artifact.artifact_type in extra_atypes:
            extra_atypes.remove(artifact.artifact_type)

        pts = artifact.prep_templates
        if pts:
            for aa in pts[0].artifact.descendants.nodes():
                atype = aa.artifact_type
                if artifact_id != aa.id and atype in extra_atypes:
                    extra_artifacts[atype].append((aa.id, aa.name))

    if analysis is not None:
        analysis_artifacts = analysis.artifacts
        for aa in analysis_artifacts:
            atype = aa.artifact_type
            if artifact_id != aa.id and atype in extra_atypes:
                extra_artifacts[atype].append((aa.id, aa.name))

    options = [
        {"id": p.id, "name": p.name, "values": p.values}
        for p in command.default_parameter_sets
        if _helper_process_params(p.values) not in eparams
    ]
    return {
        "status": "success",
        "message": "",
        "options": options,
        "req_options": command.required_parameters,
        "opt_options": command.optional_parameters,
        "extra_artifacts": extra_artifacts,
    }


def workflow_handler_post_req(user_id, command_id, params):
    """Creates a new workflow in the system

    Parameters
    ----------
    user_id : str
        The user creating the workflow
    command_id : int
        The first command to execute in the workflow
    params : str
        JSON representations of the parameters for the first command of
        the workflow

    Returns
    -------
    dict of objects
        A dictionary containing the commands information
        {'status': str,
         'message': str,
         'workflow_id': int}
    """
    status = "success"
    message = ""
    try:
        parameters = Parameters.load(Command(command_id), json_str=params)
    except Exception as exc:
        wf = None
        wf_id = None
        job_info = None
        status = "error"
        message = str(exc)

    if status == "success":
        try:
            wf = ProcessingWorkflow.from_scratch(User(user_id), parameters)
        except Exception as exc:
            wf = None
            wf_id = None
            job_info = None
            status = "error"
            message = str(exc)

    if wf is not None:
        # this is safe as we are creating the workflow for the first time
        # and there is only one node. Remember networkx doesn't assure order
        # of nodes
        job = list(wf.graph.nodes())[0]
        inputs = [a.id for a in job.input_artifacts]
        job_cmd = job.command
        wf_id = wf.id
        job_info = {
            "id": job.id,
            "inputs": inputs,
            "label": job_cmd.name,
            "outputs": job_cmd.outputs,
        }

    return {"status": status, "message": message, "workflow_id": wf_id, "job": job_info}


def workflow_handler_patch_req(req_op, req_path, req_value=None, req_from=None):
    """Patches a workflow

    Parameters
    ----------
    req_op : str
        The operation to perform on the workflow
    req_path : str
        Path parameter with the workflow to patch
    req_value : str, optional
        The value that needs to be modified
    req_from : str, optional
        The original path of the element

    Returns
    -------
    dict of {str: str}
        A dictionary of the form: {'status': str, 'message': str} in which
        status is the status of the request ('error' or 'success') and message
        is a human readable string with the error message in case that status
        is 'error'.
    """
    if req_op == "add":
        req_path = [v for v in req_path.split("/") if v]
        if len(req_path) != 1:
            return {"status": "error", "message": "Incorrect path parameter"}
        req_path = req_path[0]
        try:
            wf = ProcessingWorkflow(req_path)
        except QiitaDBUnknownIDError:
            return {
                "status": "error",
                "message": "Workflow %s does not exist" % req_path,
            }

        req_value = loads(req_value)
        dflt_params = DefaultParameters(req_value["dflt_params"])
        req_params = req_value.get("req_params", None)
        opt_params = req_value.get("opt_params", None)
        connections = {ProcessingJob(k): v for k, v in req_value["connections"].items()}
        job = wf.add(
            dflt_params,
            connections=connections,
            req_params=req_params,
            opt_params=opt_params,
        )
        job_cmd = job.command
        return {
            "status": "success",
            "message": "",
            "job": {
                "id": job.id,
                "inputs": list(req_value["connections"].keys()),
                "label": job_cmd.name,
                "outputs": job_cmd.outputs,
            },
        }
    elif req_op == "remove":
        req_path = [v for v in req_path.split("/") if v]
        if len(req_path) != 2:
            return {"status": "error", "message": "Incorrect path parameter"}
        wf_id = req_path[0]
        job_id = req_path[1]
        wf = ProcessingWorkflow(wf_id)
        job = ProcessingJob(job_id)
        wf.remove(job, cascade=True)
        return {"status": "success", "message": ""}
    else:
        return {
            "status": "error",
            "message": 'Operation "%s" not supported. Current supported '
            "operations: add" % req_op,
        }


def workflow_run_post_req(workflow_id):
    """Submits the workflow for execution

    Parameters
    ----------
    workflow_id : str
        The workflow id

    Returns
    -------
    dict of {str: str}
        A dictionary of the form: {'status': str, 'message': str} in which
        status is the status of the request ('error' or 'success') and message
        is a human readable string with the error message in case that status
        is 'error'.
    """
    try:
        wf = ProcessingWorkflow(workflow_id)
    except QiitaDBUnknownIDError:
        return {
            "status": "error",
            "message": "Workflow %s does not exist" % workflow_id,
        }
    wf.submit()
    return {"status": "success", "message": ""}


def job_ajax_get_req(job_id):
    """Returns the job information

    Parameters
    ----------
    job_id : str
        The job id

    Returns
    -------
    dict of objects
        A dictionary containing the job information
        {'status': str,
         'message': str,
         'job_id': str,
         'job_status': str,
         'job_step': str,
         'job_parameters': dict of {str: str}}
    """
    job = ProcessingJob(job_id)
    cmd = job.command
    sw = cmd.software
    job_status = job.status
    job_error = job.log.msg if job.log is not None else None
    return {
        "status": "success",
        "message": "",
        "job_id": job.id,
        "job_external_id": job.external_id,
        "job_status": job_status,
        "job_step": job.step,
        "job_parameters": job.parameters.values,
        "job_error": job_error,
        "command": cmd.name,
        "command_description": cmd.description,
        "software": sw.name,
        "software_version": sw.version,
    }


def job_ajax_patch_req(req_op, req_path, req_value=None, req_from=None):
    """Patches a job

    Parameters
    ----------
    req_op : str
        The operation to perform on the job
    req_path : str
        Path parameter with the job to patch
    req_value : str, optional
        The value that needs to be modified
    req_from : str, optional
        The original path of the element

    Returns
    -------
    dict of {str: str}
        A dictionary of the form: {'status': str, 'message': str} in which
        status is the status of the request ('error' or 'success') and message
        is a human readable string with the error message in case that status
        is 'error'.
    """
    if req_op == "remove":
        req_path = [v for v in req_path.split("/") if v]
        if len(req_path) != 1:
            return {
                "status": "error",
                "message": "Incorrect path parameter: missing job id",
            }

        # We have ensured that we only have one element on req_path
        job_id = req_path[0]
        try:
            job = ProcessingJob(job_id)
        except QiitaDBUnknownIDError:
            return {
                "status": "error",
                "message": "Incorrect path parameter: "
                "%s is not a recognized job id" % job_id,
            }
        except Exception as e:
            e = str(e)
            if "invalid input syntax for uuid" in e:
                return {
                    "status": "error",
                    "message": "Incorrect path parameter: "
                    "%s is not a recognized job id" % job_id,
                }
            else:
                return {
                    "status": "error",
                    "message": "An error occured while accessing the job: %s" % e,
                }

        job_status = job.status

        if job_status == "in_construction":
            # A job that is in construction is in a workflow. Use the methods
            # defined for workflows to keep everything consistent. This message
            # should never be presented to the user, but rather to the
            # developer if it makes a mistake during changes in the interface
            return {
                "status": "error",
                "message": "Can't delete job %s. It is 'in_construction' "
                "status. Please use /study/process/workflow/" % job_id,
            }
        elif job_status == "error":
            # When the job is in error status, we just need to hide it
            job.hide()
            return {"status": "success", "message": ""}
        else:
            # In any other state, we currently fail. Adding the else here
            # because it can be useful to have it for fixing issue #2307
            return {
                "status": "error",
                "message": 'Only jobs in "error" status can be deleted.',
            }
    else:
        return {
            "status": "error",
            "message": 'Operation "%s" not supported. Current supported '
            "operations: remove" % req_op,
        }
