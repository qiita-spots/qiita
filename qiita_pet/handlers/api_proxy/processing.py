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
from qiita_db.artifact import Artifact
from qiita_db.processing_job import ProcessingWorkflow


def process_artifact_handler_get_req(artifact_id):
    """Returns the information for the process artifact handler

    Parameters
    ----------
    artifact_id : int
        The artifact to be processed

    Returns
    -------
    dict of str
        A dictionary containing the artifact information
        {'status': str,
         'message': str,
         'name': str,
         'type': str}
    """
    artifact = Artifact(artifact_id)

    return {'status': 'success',
            'message': '',
            'name': artifact.name,
            'type': artifact.artifact_type}


def list_commands_handler_get_req(artifact_types):
    """Retrieves the commands that can process the given artifat types

    Parameters
    ----------
    artifact_types : str
        Comma-separated list of artifact types

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
        for cmd in Command.get_commands_by_input_type(artifact_types)]

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
            'req_options': command.required_parameters}


def workflow_handler_post_req(user_id, dflt_params_id, req_params):
    """Creates a new workflow in the system

    Parameters
    ----------
    user_id : str
        The user creating the workflow
    dflt_params_id : int
        The default parameters to use for the first command of the workflow
    req_params : str
        JSON representations of the required parameters for the first
        command of the workflow

    Returns
    -------
    dict of objects
        A dictionary containing the commands information
        {'status': str,
         'message': str,
         'workflow_id': int}
    """
    dflt_params = DefaultParameters(dflt_params_id)
    req_params = loads(req_params)
    parameters = Parameters.from_default_params(dflt_params, req_params)
    wf = ProcessingWorkflow.from_scratch(User(user_id), parameters)
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
