# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from qiita_db.software import Command
from qiita_db.artifact import Artifact


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
         'options': TODO}
    """
    command = Command(command_id)
    options = [{'id': p.id, 'name': p.name, 'values': p.values}
               for p in command.default_parameter_sets]
    return {'status': 'success',
            'message': '',
            'options': options}
