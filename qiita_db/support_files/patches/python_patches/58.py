# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import loads, dumps

from qiita_core.qiita_settings import r_client
from qiita_db.sql_connection import TRN
from qiita_db.software import Software, Command, Parameters
from qiita_db.processing_job import ProcessingJob
from qiita_db.study import Study
from qiita_db.exceptions import (QiitaDBUnknownIDError, QiitaDBError,
                                 QiitaDBDuplicateError)
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.util import convert_to_id


def create_command(software, name, description, parameters, outputs=None,
                   analysis_only=False):
    r"""Replicates the Command.create code at the time the patch was written"""
    # Perform some sanity checks in the parameters dictionary
    if not parameters:
        raise QiitaDBError(
            "Error creating command %s. At least one parameter should "
            "be provided." % name)
    sql_param_values = []
    sql_artifact_params = []
    for pname, vals in parameters.items():
        if len(vals) != 2:
            raise QiitaDBError(
                "Malformed parameters dictionary, the format should be "
                "{param_name: [parameter_type, default]}. Found: "
                "%s for parameter name %s" % (vals, pname))

        ptype, dflt = vals
        # Check that the type is one of the supported types
        supported_types = ['string', 'integer', 'float', 'reference',
                           'boolean', 'prep_template', 'analysis']
        if ptype not in supported_types and not ptype.startswith(
                ('choice', 'mchoice', 'artifact')):
            supported_types.extend(['choice', 'mchoice', 'artifact'])
            raise QiitaDBError(
                "Unsupported parameters type '%s' for parameter %s. "
                "Supported types are: %s"
                % (ptype, pname, ', '.join(supported_types)))

        if ptype.startswith(('choice', 'mchoice')) and dflt is not None:
            choices = set(loads(ptype.split(':')[1]))
            dflt_val = dflt
            if ptype.startswith('choice'):
                # In the choice case, the dflt value is a single string,
                # create a list with it the string on it to use the
                # issuperset call below
                dflt_val = [dflt_val]
            else:
                # jsonize the list to store it in the DB
                dflt = dumps(dflt)
            if not choices.issuperset(dflt_val):
                raise QiitaDBError(
                    "The default value '%s' for the parameter %s is not "
                    "listed in the available choices: %s"
                    % (dflt, pname, ', '.join(choices)))

        if ptype.startswith('artifact'):
            atypes = loads(ptype.split(':')[1])
            sql_artifact_params.append(
                [pname, 'artifact', atypes])
        else:
            if dflt is not None:
                sql_param_values.append([pname, ptype, False, dflt])
            else:
                sql_param_values.append([pname, ptype, True, None])

    with TRN:
        sql = """SELECT EXISTS(SELECT *
                               FROM qiita.software_command
                               WHERE software_id = %s AND name = %s)"""
        TRN.add(sql, [software.id, name])
        if TRN.execute_fetchlast():
            raise QiitaDBDuplicateError(
                "command", "software: %d, name: %s"
                           % (software.id, name))
        # Add the command to the DB
        sql = """INSERT INTO qiita.software_command
                        (name, software_id, description, is_analysis)
                 VALUES (%s, %s, %s, %s)
                 RETURNING command_id"""
        sql_params = [name, software.id, description, analysis_only]
        TRN.add(sql, sql_params)
        c_id = TRN.execute_fetchlast()

        # Add the parameters to the DB
        sql = """INSERT INTO qiita.command_parameter
                    (command_id, parameter_name, parameter_type, required,
                     default_value)
                 VALUES (%s, %s, %s, %s, %s)
                 RETURNING command_parameter_id"""
        sql_params = [[c_id, pname, p_type, reqd, default]
                      for pname, p_type, reqd, default in sql_param_values]
        TRN.add(sql, sql_params, many=True)
        TRN.execute()

        # Add the artifact parameters
        sql_type = """INSERT INTO qiita.parameter_artifact_type
                        (command_parameter_id, artifact_type_id)
                      VALUES (%s, %s)"""
        supported_types = []
        for pname, p_type, atypes in sql_artifact_params:
            sql_params = [c_id, pname, p_type, True, None]
            TRN.add(sql, sql_params)
            pid = TRN.execute_fetchlast()
            sql_params = [[pid, convert_to_id(at, 'artifact_type')]
                          for at in atypes]
            TRN.add(sql_type, sql_params, many=True)
            supported_types.extend([atid for _, atid in sql_params])

        # If the software type is 'artifact definition', there are a couple
        # of extra steps
        if software.type == 'artifact definition':
            # If supported types is not empty, link the software with these
            # types
            if supported_types:
                sql = """INSERT INTO qiita.software_artifact_type
                                (software_id, artifact_type_id)
                            VALUES (%s, %s)"""
                sql_params = [[software.id, atid]
                              for atid in supported_types]
                TRN.add(sql, sql_params, many=True)
            # If this is the validate command, we need to add the
            # provenance and name parameters. These are used internally,
            # that's why we are adding them here
            if name == 'Validate':
                sql = """INSERT INTO qiita.command_parameter
                            (command_id, parameter_name, parameter_type,
                             required, default_value)
                         VALUES (%s, 'name', 'string', 'False',
                                 'dflt_name'),
                                (%s, 'provenance', 'string', 'False', NULL)
                         """
                TRN.add(sql, [c_id, c_id])

        # Add the outputs to the command
        if outputs:
            sql = """INSERT INTO qiita.command_output
                        (name, command_id, artifact_type_id)
                     VALUES (%s, %s, %s)"""
            sql_args = [[pname, c_id, convert_to_id(at, 'artifact_type')]
                        for pname, at in outputs.items()]
            TRN.add(sql, sql_args, many=True)
            TRN.execute()

    return Command(c_id)


def correct_redis_data(key, cmd, values_dict, user):
    """Corrects the data stored in the redis DB

    Parameters
    ----------
    key: str
        The redis key to fix
    cmd : qiita_db.software.Command
        Command to use to create the processing job
    values_dict : dict
        Dictionary used to instantiate the parameters of the command
    user : qiita_db.user. User
        The user that will own the job
    """
    info = r_client.get(key)
    if info:
        info = loads(info)
        if info['job_id'] is not None:
            if 'is_qiita_job' in info:
                if info['is_qiita_job']:
                    try:
                        job = ProcessingJob(info['job_id'])
                        payload = {'job_id': info['job_id'],
                                   'alert_type': info['status'],
                                   'alert_msg': info['alert_msg']}
                        r_client.set(key, dumps(payload))
                    except (QiitaDBUnknownIDError, KeyError):
                        # We shomehow lost the information of this job
                        # Simply delete the key
                        r_client.delete(key)
                else:
                    # These jobs don't contain any information on the live
                    # dump. We can safely delete the key
                    r_client.delete(key)
            else:
                # These jobs don't contain any information on the live
                # dump. We can safely delete the key
                r_client.delete(key)
        else:
            # Job is null, we have the information here
            if info['status'] == 'success':
                # In the success case no information is stored. We can
                # safely delete the key
                r_client.delete(key)
            elif info['status'] == 'warning':
                # In case of warning the key message stores the warning
                # message. We need to create a new job, mark it as
                # successful and store the error message as expected by
                # the new structure
                params = Parameters.load(cmd, values_dict=values_dict)
                job = ProcessingJob.create(user, params)
                job._set_status('success')
                payload = {'job_id': job.id,
                           'alert_type': 'warning',
                           'alert_msg': info['message']}
                r_client.set(key, dumps(payload))
            else:
                # The status is error. The key message stores the error
                # message. We need to create a new job and mark it as
                # failed with the given error message
                params = Parameters.load(cmd, values_dict=values_dict)
                job = ProcessingJob.create(user, params)
                job._set_error(info['message'])
                payload = {'job_id': job.id}
                r_client.set(key, dumps(payload))
    else:
        # The key doesn't contain any information. Delete the key
        r_client.delete(key)


with TRN:
    # Retrieve the Qiita plugin
    qiita_plugin = Software.from_name_and_version('Qiita', 'alpha')

    # Create the submit command for VAMPS command
    parameters = {'artifact': ['integer', None]}
    create_command(qiita_plugin, "submit_to_VAMPS",
                   "submits an artifact to VAMPS", parameters)

    # Create the copy artifact command
    parameters = {'artifact': ['integer', None],
                  'prep_template': ['prep_template', None]}
    create_command(qiita_plugin, "copy_artifact",
                   "Creates a copy of an artifact", parameters)

    # Create the submit command for EBI command
    parameters = {'artifact': ['integer', None],
                  'submission_type': ['choice:["ADD", "MODIFY"]', 'ADD']}
    create_command(qiita_plugin, "submit_to_EBI",
                   "submits an artifact to EBI", parameters)

    # Create the submit command for delete_artifact
    parameters = {'artifact': ['integer', None]}
    create_command(qiita_plugin, "delete_artifact",
                   "Delete an artifact", parameters)

    # Create the submit command for create a sample template
    parameters = {
        'fp': ['string', None], 'study_id': ['integer', None],
        'is_mapping_file': ['boolean', True], 'data_type': ['string', None]}
    create_command(qiita_plugin, "create_sample_template",
                   "Create a sample template", parameters)

    # Create the update sample template command
    parameters = {'study': ['integer', None], 'template_fp': ['string', None]}
    st_cmd = create_command(qiita_plugin, "update_sample_template",
                            "Updates the sample template", parameters)

    # Create the delete study command
    parameters = {'study': ['integer', None]}
    create_command(qiita_plugin, "delete_study",
                   "Deletes a full study", parameters)

    # Create the delete sample template command
    parameters = {'study': ['integer', None]}
    create_command(qiita_plugin, "delete_sample_template",
                   "Deletes a sample template", parameters)

    # Create the update prep template command
    parameters = {'prep_template': ['integer', None],
                  'template_fp': ['string', None]}
    pt_cmd = create_command(qiita_plugin, "update_prep_template",
                            "Updates the prep template", parameters)

    # Create the delete sample or column command
    parameters = {
        'obj_class': ['choice:["SampleTemplate", "PrepTemplate"]', None],
        'obj_id': ['integer', None],
        'sample_or_col': ['choice:["samples", "columns"]', None],
        'name': ['string', None]}
    create_command(qiita_plugin, "delete_sample_or_column",
                   "Deletes a sample or a columns from the metadata",
                   parameters)

    # Create the command to complete a job
    parameters = {'job_id': ['string', None], 'payload': ['string', None]}
    create_command(qiita_plugin, "complete_job", "Completes a given job",
                   parameters)

    # Assumptions on the structure of the data in the redis database has
    # changed, we need to fix to avoid failures
    # Get all the sample template keys
    for key in r_client.keys('sample_template_[0-9]*'):
        try:
            study = Study(int(key.split('_')[-1]))
            user = study.owner
        except QiitaDBUnknownIDError:
            # This means that the study no longer exists - delete the key
            # and continue
            r_client.delete(key)
            continue
        values_dict = {'study': study.id, 'template_fp': 'ignored-patch58'}
        correct_redis_data(key, st_cmd, values_dict, user)

    # Get all the prep template keys
    for key in r_client.keys('prep_template_[0-9]*'):
        try:
            pt = PrepTemplate(int(key.split('_')[-1]))
            user = Study(pt.study_id).owner
        except QiitaDBUnknownIDError:
            # This means that the prep template no longer exists - delete the
            # key and continue
            r_client.delete(key)
            continue
        values_dict = {'prep_template': pt.id,
                       'template_fp': 'ignored-patch58'}
        correct_redis_data(key, pt_cmd, values_dict, user)
