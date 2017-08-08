# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import loads

from qiita_db.user import User
from qiita_db.software import Command, Parameters, DefaultParameters
from qiita_db.processing_job import ProcessingWorkflow, ProcessingJob
from qiita_db.exceptions import QiitaDBUnknownIDError


def list_commands_handler_get_req(artifact_types, exclude_analysis):
    """Retrieves the commands that can process the given artifact types

    Parameters
    ----------
    artifact_types : str
        Comma-separated list of artifact types
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
    artifact_types = artifact_types.split(',')
    cmd_info = [
        {'id': cmd.id, 'command': cmd.name, 'output': cmd.outputs}
        for cmd in Command.get_commands_by_input_type(
            artifact_types, exclude_analysis=exclude_analysis)]

    return {'status': 'success',
            'message': '',
            'commands': cmd_info}


def list_options_handler_get_req(command_id):
    """Returns the available default parameters set for the given command

    Parameters
    ----------
    command_id : int
        The command id

    Returns
    -------
    dict of objects
        A dictionary containing the commands information
        {'status': str,
         'message': str,
         'options': list of dicts of {'id: str', 'name': str,
                                      'values': dict of {str: str}}}
    """
    command = Command(command_id)
    options = [{'id': p.id, 'name': p.name, 'values': p.values}
               for p in command.default_parameter_sets]
    return {'status': 'success',
            'message': '',
            'options': options,
            'req_options': command.required_parameters,
            'opt_options': command.optional_parameters}


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
    parameters = Parameters.load(Command(command_id), json_str=params)
    wf = ProcessingWorkflow.from_scratch(User(user_id), parameters)
    # this is safe as we are creating the workflow for the first time and there
    # is only one node. Remember networkx doesn't assure order of nodes
    job = wf.graph.nodes()[0]
    inputs = [a.id for a in job.input_artifacts]
    job_cmd = job.command
    return {'status': 'success',
            'message': '',
            'workflow_id': wf.id,
            'job': {'id': job.id,
                    'inputs': inputs,
                    'label': job_cmd.name,
                    'outputs': job_cmd.outputs}}


def workflow_handler_patch_req(req_op, req_path, req_value=None,
                               req_from=None):
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
    if req_op == 'add':
        req_path = [v for v in req_path.split('/') if v]
        if len(req_path) != 1:
            return {'status': 'error',
                    'message': 'Incorrect path parameter'}
        req_path = req_path[0]
        try:
            wf = ProcessingWorkflow(req_path)
        except QiitaDBUnknownIDError:
            return {'status': 'error',
                    'message': 'Workflow %s does not exist' % req_path}

        req_value = loads(req_value)
        dflt_params = DefaultParameters(req_value['dflt_params'])
        req_params = req_value.get('req_params', None)
        opt_params = req_value.get('opt_params', None)
        connections = {ProcessingJob(k): v
                       for k, v in req_value['connections'].items()}
        job = wf.add(dflt_params, connections=connections,
                     req_params=req_params, opt_params=opt_params)
        job_cmd = job.command
        return {'status': 'success',
                'message': '',
                'job': {'id': job.id,
                        'inputs': req_value['connections'].keys(),
                        'label': job_cmd.name,
                        'outputs': job_cmd.outputs}}
    elif req_op == 'remove':
        req_path = [v for v in req_path.split('/') if v]
        if len(req_path) != 2:
            return {'status': 'error',
                    'message': 'Incorrect path parameter'}
        wf_id = req_path[0]
        job_id = req_path[1]
        wf = ProcessingWorkflow(wf_id)
        job = ProcessingJob(job_id)
        wf.remove(job, cascade=True)
        return {'status': 'success',
                'message': ''}
    else:
        return {'status': 'error',
                'message': 'Operation "%s" not supported. Current supported '
                           'operations: add' % req_op}


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
        return {'status': 'error',
                'message': 'Workflow %s does not exist' % workflow_id}
    wf.submit()
    return {'status': 'success', 'message': ''}


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
    return {'status': 'success',
            'message': '',
            'job_id': job.id,
            'job_status': job.status,
            'job_step': job.step,
            'job_parameters': job.parameters.values}
