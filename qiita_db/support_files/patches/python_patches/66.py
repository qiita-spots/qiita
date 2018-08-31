# August 6, 2018
# Create parameters for the ssh/scp remote file upload commands


from json import loads, dumps

from qiita_db.sql_connection import TRN
from qiita_db.software import Software, Command
from qiita_db.exceptions import (QiitaDBError, QiitaDBDuplicateError)
from qiita_db.util import convert_to_id


# Copied from patch 58.py. Couldn't import due to how patching system works
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


with TRN:
    qiita_plugin = Software.from_name_and_version('Qiita', 'alpha')

    # Create the 'list_remote_files' command
    parameters = {'url': ['string', None],
                  'private_key': ['string', None]}
    create_command(qiita_plugin, "list_remote_files",
                   "retrieves list of valid study files from remote dir",
                   parameters)

    # Create the 'download_remote_files' command
    parameters = {'url': ['string', None],
                  'destination': ['string', None],
                  'private_key': ['string', None]}
    create_command(qiita_plugin, "download_remote_files",
                   "downloads valid study files from remote dir", parameters)
