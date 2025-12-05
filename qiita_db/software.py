# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import inspect
import warnings
from configparser import ConfigParser
from copy import deepcopy
from json import dumps, loads

import networkx as nx

import qiita_db as qdb
from qiita_core.qiita_settings import qiita_config


class Command(qdb.base.QiitaObject):
    r"""An executable command available in the system

    Attributes
    ----------
    active
    post_processing_cmd
    analysis_only
    default_parameter_sets
    description
    merging_scheme
    name
    naming_order
    optional_parameters
    outputs
    parameters
    required_parameters
    software
    description
    cli
    parameters_table

    Methods
    -------
    _check_id
    activate

    Class Methods
    -------------
    create
    exists
    get_commands_by_input_type
    get_html_generator
    get_validator

    See Also
    --------
    qiita_db.software.Software
    """

    _table = "software_command"

    @classmethod
    def get_commands_by_input_type(
        cls, artifact_types, active_only=True, exclude_analysis=True, prep_type=None
    ):
        """Returns the commands that can process the given artifact types

        Parameters
        ----------
        artifact_type : list of str
            The artifact types
        active_only : bool, optional
            If True, return only active commands, otherwise return all commands
            Default: True
        exclude_analysis : bool, optional
            If True, return commands that are not part of the analysis pipeline

        Returns
        -------
        generator of qiita_db.software.Command
            The commands that can process the given artifact tyoes
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT DISTINCT command_id
                     FROM qiita.command_parameter
                        JOIN qiita.parameter_artifact_type
                            USING (command_parameter_id)
                        JOIN qiita.artifact_type USING (artifact_type_id)
                        JOIN qiita.software_command USING (command_id)
                     WHERE artifact_type IN %s"""
            if active_only:
                sql += " AND active = True"
            if exclude_analysis:
                sql += " AND is_analysis = False"
            qdb.sql_connection.TRN.add(sql, [tuple(artifact_types)])
            cids = set(qdb.sql_connection.TRN.execute_fetchflatten())

            if prep_type is not None:
                dws = [
                    w
                    for w in qdb.software.DefaultWorkflow.iter()
                    if prep_type in w.data_type
                ]
                if dws:
                    cmds = {
                        n.default_parameter.command.id
                        for w in dws
                        for n in w.graph.nodes
                    }
                    cids = cmds & cids

            return [cls(cid) for cid in cids]

    @classmethod
    def get_html_generator(cls, artifact_type):
        """Returns the command that generete the HTML for the given artifact

        Parameters
        ----------
        artifact_type : str
            The artifact type to search the HTML generator for

        Returns
        -------
        qiita_db.software.Command
            The newly created command

        Raises
        ------
        qdb.exceptions.QiitaDBError when the generete the HTML command can't
        be found
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT command_id
                     FROM qiita.software_command
                        JOIN qiita.software_artifact_type USING (software_id)
                        JOIN qiita.artifact_type USING (artifact_type_id)
                     WHERE artifact_type = %s
                        AND name = 'Generate HTML summary'
                        AND active = true"""
            qdb.sql_connection.TRN.add(sql, [artifact_type])
            try:
                res = qdb.sql_connection.TRN.execute_fetchlast()
            except IndexError:
                raise qdb.exceptions.QiitaDBError(
                    "There is no command to generate the HTML summary for "
                    "artifact type '%s'" % artifact_type
                )

            return cls(res)

    @classmethod
    def get_validator(cls, artifact_type):
        """Returns the command that validates the given artifact

        Parameters
        ----------
        artifact_type : str
            The artifact type to search the Validate for

        Returns
        -------
        qiita_db.software.Command
            The newly created command

        Raises
        ------
        qdb.exceptions.QiitaDBError when the Validate command can't be found
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT command_id
                     FROM qiita.software_command
                        JOIN qiita.software_artifact_type USING (software_id)
                        JOIN qiita.artifact_type USING (artifact_type_id)
                     WHERE artifact_type = %s
                        AND name = 'Validate'
                        AND active = true"""
            qdb.sql_connection.TRN.add(sql, [artifact_type])
            try:
                res = qdb.sql_connection.TRN.execute_fetchlast()
            except IndexError:
                raise qdb.exceptions.QiitaDBError(
                    "There is no command to generate the Validate for "
                    "artifact type '%s'" % artifact_type
                )

            return cls(res)

    def _check_id(self, id_):
        """Check that the provided ID actually exists in the database

        Parameters
        ----------
        id_ : int
            The ID to test

        Notes
        -----
        This function overwrites the base function, as the sql layout doesn't
        follow the same conventions done in the other classes.
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(
                        SELECT *
                        FROM qiita.software_command
                        WHERE command_id = %s)"""
            qdb.sql_connection.TRN.add(sql, [id_])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @classmethod
    def exists(cls, software, name):
        """Checks if the command already exists in the system

        Parameters
        ----------
        qiita_db.software.Software
            The software to which this command belongs to.
        name : str
            The name of the command

        Returns
        -------
        bool
            Whether the command exists in the system or not
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(SELECT *
                                   FROM qiita.software_command
                                   WHERE software_id = %s
                                        AND name = %s)"""
            qdb.sql_connection.TRN.add(sql, [software.id, name])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @classmethod
    def create(
        cls, software, name, description, parameters, outputs=None, analysis_only=False
    ):
        r"""Creates a new command in the system

        The supported types for the parameters are:
            - string: the parameter is a free text input
            - integer: the parameter is an integer
            - float: the parameter is a float
            - artifact: the parameter is an artifact instance, the artifact id
            will be stored
            - reference: the parameter is a reference instance, the reference
            id will be stored
            - choice: the format of this should be `choice:<json-dump-of-list>`
            in which json-dump-of-list is the JSON dump of a list containing
            the acceptable values

        Parameters
        ----------
        software : qiita_db.software.Software
            The software to which this command belongs to.
        name : str
            The name of the command
        description : str
            The description of the command
        parameters : dict
            The description of the parameters that this command received. The
            format is: {parameter_name: (parameter_type, default, name_order,
            check_biom_merge, qiita_optional_parameter (optional))},
            where parameter_name, parameter_type and default are strings,
            name_order is an optional integer value and check_biom_merge is
            an optional boolean value. name_order is used to specify the order
            of the parameter when automatically naming the artifacts.
            check_biom_merge is used when merging artifacts in the analysis
            pipeline. qiita_optional_parameter is an optional bool to "force"
            the parameter to be optional
        outputs : dict, optional
            The description of the outputs that this command generated. The
            format is either {output_name: artifact_type} or
            {output_name: (artifact_type, check_biom_merge)}
        analysis_only : bool, optional
            If true, then the command will only be available on the analysis
            pipeline. Default: False.

        Returns
        -------
        qiita_db.software.Command
            The newly created command

        Raises
        ------
        QiitaDBError
            - If parameters is empty
            - If the parameters dictionary is malformed
            - If one of the parameter types is not supported
            - If the default value of a choice parameter is not listed in
            the available choices
        QiitaDBDuplicateError
            - If the command already exists

        Notes
        -----
        If the default value for a parameter is NULL, then the parameter will
        be required. On the other hand, if it is provided, the parameter will
        be optional and the default value will be used when the user doesn't
        overwrite it.
        """
        # Perform some sanity checks in the parameters dictionary
        if not parameters:
            raise qdb.exceptions.QiitaDBError(
                "Error creating command %s. At least one parameter should "
                "be provided." % name
            )
        sql_param_values = []
        sql_artifact_params = []
        for pname, vals in parameters.items():
            qiita_optional_parameter = False
            if "qiita_optional_parameter" in vals:
                qiita_optional_parameter = True
                vals.remove("qiita_optional_parameter")
            lenvals = len(vals)
            if lenvals == 2:
                ptype, dflt = vals
                name_order = None
                check_biom_merge = False
            elif lenvals == 4:
                ptype, dflt, name_order, check_biom_merge = vals
            else:
                raise qdb.exceptions.QiitaDBError(
                    "Malformed parameters dictionary, the format should be "
                    "either {param_name: [parameter_type, default]} or "
                    "{parameter_name: (parameter_type, default, name_order, "
                    "check_biom_merge)}. Found: %s for parameter name %s"
                    % (vals, pname)
                )

            # Check that the type is one of the supported types
            supported_types = [
                "string",
                "integer",
                "float",
                "reference",
                "boolean",
                "prep_template",
                "analysis",
            ]
            if ptype not in supported_types and not ptype.startswith(
                ("choice", "mchoice", "artifact")
            ):
                supported_types.extend(["choice", "mchoice", "artifact"])
                raise qdb.exceptions.QiitaDBError(
                    "Unsupported parameters type '%s' for parameter %s. "
                    "Supported types are: %s"
                    % (ptype, pname, ", ".join(supported_types))
                )

            if ptype.startswith(("choice", "mchoice")) and dflt is not None:
                choices = set(loads(ptype.split(":")[1]))
                dflt_val = dflt
                if ptype.startswith("choice"):
                    # In the choice case, the dflt value is a single string,
                    # create a list with it the string on it to use the
                    # issuperset call below
                    dflt_val = [dflt_val]
                else:
                    # jsonize the list to store it in the DB
                    dflt = dumps(dflt)
                if not choices.issuperset(dflt_val):
                    raise qdb.exceptions.QiitaDBError(
                        "The default value '%s' for the parameter %s is not "
                        "listed in the available choices: %s"
                        % (dflt, pname, ", ".join(choices))
                    )

            if ptype.startswith("artifact"):
                atypes = loads(ptype.split(":")[1])
                sql_artifact_params.append([pname, "artifact", atypes])
            else:
                # a parameter will be required (not optional) if
                # qiita_optional_parameter is false and there is the default
                # value (dflt) is None
                required = not qiita_optional_parameter and dflt is None
                sql_param_values.append(
                    [pname, ptype, required, dflt, name_order, check_biom_merge]
                )

        with qdb.sql_connection.TRN:
            if cls.exists(software, name):
                raise qdb.exceptions.QiitaDBDuplicateError(
                    "command", "software: %d, name: %s" % (software.id, name)
                )
            # Add the command to the DB
            sql = """INSERT INTO qiita.software_command
                            (name, software_id, description, is_analysis)
                     VALUES (%s, %s, %s, %s)
                     RETURNING command_id"""
            sql_params = [name, software.id, description, analysis_only]
            qdb.sql_connection.TRN.add(sql, sql_params)
            c_id = qdb.sql_connection.TRN.execute_fetchlast()

            # Add the parameters to the DB
            sql = """INSERT INTO qiita.command_parameter
                        (command_id, parameter_name, parameter_type,
                         required, default_value, name_order, check_biom_merge)
                     VALUES (%s, %s, %s, %s, %s, %s, %s)
                     RETURNING command_parameter_id"""
            sql_params = [
                [c_id, pname, p_type, reqd, default, no, chm]
                for pname, p_type, reqd, default, no, chm in sql_param_values
            ]
            qdb.sql_connection.TRN.add(sql, sql_params, many=True)
            qdb.sql_connection.TRN.execute()

            # Add the artifact parameters
            sql_type = """INSERT INTO qiita.parameter_artifact_type
                            (command_parameter_id, artifact_type_id)
                          VALUES (%s, %s)"""
            supported_types = []
            for pname, p_type, atypes in sql_artifact_params:
                sql_params = [c_id, pname, p_type, True, None, None, False]
                qdb.sql_connection.TRN.add(sql, sql_params)
                pid = qdb.sql_connection.TRN.execute_fetchlast()
                sql_params = [
                    [pid, qdb.util.convert_to_id(at, "artifact_type")] for at in atypes
                ]
                qdb.sql_connection.TRN.add(sql_type, sql_params, many=True)
                supported_types.extend([atid for _, atid in sql_params])

            # If the software type is 'artifact definition', there are a couple
            # of extra steps
            if software.type == "artifact definition":
                # If supported types is not empty, link the software with these
                # types
                if supported_types:
                    sql = """INSERT INTO qiita.software_artifact_type
                                    (software_id, artifact_type_id)
                                VALUES (%s, %s)"""
                    sql_params = [[software.id, atid] for atid in supported_types]
                    qdb.sql_connection.TRN.add(sql, sql_params, many=True)
                # If this is the validate command, we need to add the
                # provenance and name parameters. These are used internally,
                # that's why we are adding them here
                if name == "Validate":
                    sql = """INSERT INTO qiita.command_parameter
                                (command_id, parameter_name, parameter_type,
                                 required, default_value)
                             VALUES (%s, 'name', 'string', 'False',
                                     'dflt_name'),
                                    (%s, 'provenance', 'string', 'False', NULL)
                             """
                    qdb.sql_connection.TRN.add(sql, [c_id, c_id])

            # Add the outputs to the command
            if outputs:
                sql_args = []
                for pname, at in outputs.items():
                    if isinstance(at, tuple):
                        sql_args.append(
                            [
                                pname,
                                c_id,
                                qdb.util.convert_to_id(at[0], "artifact_type"),
                                at[1],
                            ]
                        )
                    else:
                        try:
                            at_id = qdb.util.convert_to_id(at, "artifact_type")
                        except qdb.exceptions.QiitaDBLookupError:
                            msg = (
                                f"Error creating {software.name}, {name}, "
                                f"{description} - Unknown artifact_type: "
                                f"{at}"
                            )
                            raise ValueError(msg)
                        sql_args.append([pname, c_id, at_id, False])

                sql = """INSERT INTO qiita.command_output
                            (name, command_id, artifact_type_id,
                             check_biom_merge)
                         VALUES (%s, %s, %s, %s)"""
                qdb.sql_connection.TRN.add(sql, sql_args, many=True)
                qdb.sql_connection.TRN.execute()

        return cls(c_id)

    @property
    def software(self):
        """The software to which this command belongs to

        Returns
        -------
        qiita_db.software.Software
            the software to which this command belongs to
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT software_id
                     FROM qiita.software_command
                     WHERE command_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return Software(qdb.sql_connection.TRN.execute_fetchlast())

    @property
    def name(self):
        """The name of the command

        Returns
        -------
        str
            The name of the command
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT name
                     FROM qiita.software_command
                     WHERE command_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def post_processing_cmd(self):
        """Additional processing commands required for merging

        Returns
        -------
        str
            Returns the additional processing command for merging
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT post_processing_cmd
                     FROM qiita.software_command
                     WHERE command_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])

            cmd = qdb.sql_connection.TRN.execute_fetchlast()
            if cmd:
                # assume correctly formatted json data
                # load data into dictionary; don't return JSON
                return loads(qdb.sql_connection.TRN.execute_fetchlast())

        return None

    @property
    def description(self):
        """The description of the command

        Returns
        -------
        str
            The description of the command
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT description
                     FROM qiita.software_command
                     WHERE command_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def parameters(self):
        """Returns the parameters that the command accepts

        Returns
        -------
        dict
            Dictionary of {parameter_name: [ptype, dflt]}
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT parameter_name, parameter_type, default_value
                     FROM qiita.command_parameter
                     WHERE command_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            res = qdb.sql_connection.TRN.execute_fetchindex()
            return {pname: [ptype, dflt] for pname, ptype, dflt in res}

    @property
    def required_parameters(self):
        """Returns the required parameters that the command accepts

        Returns
        -------
        dict
            Dictionary of {parameter_name: ptype}
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT command_parameter_id, parameter_name,
                            parameter_type, array_agg(
                                artifact_type ORDER BY artifact_type) AS
                            artifact_type
                     FROM qiita.command_parameter
                        LEFT JOIN qiita.parameter_artifact_type
                            USING (command_parameter_id)
                        LEFT JOIN qiita.artifact_type USING (artifact_type_id)
                     WHERE command_id = %s AND required = True
                     GROUP BY command_parameter_id"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            res = qdb.sql_connection.TRN.execute_fetchindex()
            return {pname: (ptype, atype) for _, pname, ptype, atype in res}

    @property
    def optional_parameters(self):
        """Returns the optional parameters that the command accepts

        Returns
        -------
        dict
            Dictionary of {parameter_name: [ptype, default]}
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT parameter_name, parameter_type, default_value
                     FROM qiita.command_parameter
                     WHERE command_id = %s AND required = false"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            res = qdb.sql_connection.TRN.execute_fetchindex()

            # Define a function to load the json storing the default parameters
            # if ptype is multiple choice. When I added it to the for loop as
            # a one liner if, made the code a bit hard to read
            def dflt_fmt(dflt, ptype):
                if ptype.startswith("mchoice"):
                    return loads(dflt)
                return dflt

            return {pname: [ptype, dflt_fmt(dflt, ptype)] for pname, ptype, dflt in res}

    @property
    def default_parameter_sets(self):
        """Returns the list of default parameter sets

        Returns
        -------
        generator
            generator of qiita_db.software.DefaultParameters
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT default_parameter_set_id
                     FROM qiita.default_parameter_set
                     WHERE command_id = %s
                     ORDER BY default_parameter_set_id"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            res = qdb.sql_connection.TRN.execute_fetchflatten()
            for pid in res:
                yield DefaultParameters(pid)

    @property
    def outputs(self):
        """Returns the list of output artifact types

        Returns
        -------
        list of str
            The output artifact types
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT name, artifact_type
                     FROM qiita.command_output
                        JOIN qiita.artifact_type USING (artifact_type_id)
                     WHERE command_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchindex()

    @property
    def active(self):
        """Returns if the command is active or not

        Returns
        -------
        bool
            Whether the command is active or not

        Notes
        -----
        This method differentiates between commands based on analysis_only or
        the software type. The commands that are not for analysis (processing)
        and are from an artifact definition software will return as active
        if they have the same name than a command that is active; this helps
        for situations where the processing plugins are updated but some
        commands didn't change its version.
        """
        with qdb.sql_connection.TRN:
            cmd_type = self.software.type
            if self.analysis_only or cmd_type == "artifact definition":
                sql = """SELECT active
                         FROM qiita.software_command
                         WHERE command_id = %s"""
            else:
                sql = """SELECT EXISTS (
                            SELECT active FROM qiita.software_command
                            WHERE name IN (
                                SELECT name FROM qiita.software_command
                                WHERE command_id = %s) AND active = true)"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    def activate(self):
        """Activates the command"""
        sql = """UPDATE qiita.software_command
                 SET active = %s
                 WHERE command_id = %s"""
        qdb.sql_connection.perform_as_transaction(sql, [True, self.id])

    @property
    def analysis_only(self):
        """Returns if the command is an analysis-only command

        Returns
        -------
        bool
            Whether the command is analysis only or not
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT is_analysis
                     FROM qiita.software_command
                     WHERE command_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def naming_order(self):
        """The ordered list of parameters to use to name the output artifacts

        Returns
        -------
        list of str
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT parameter_name
                     FROM qiita.command_parameter
                     WHERE command_id = %s AND name_order IS NOT NULL
                     ORDER BY name_order"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchflatten()

    @property
    def merging_scheme(self):
        """The values to check when merging the output result

        Returns
        -------
        dict of {'parameters': [list of str],
                 'outputs': [list of str]
                 'ignore_parent_command': bool}
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT parameter_name
                     FROM qiita.command_parameter
                     WHERE command_id = %s AND check_biom_merge = TRUE
                     ORDER BY parameter_name"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            params = qdb.sql_connection.TRN.execute_fetchflatten()
            sql = """SELECT name
                     FROM qiita.command_output
                     WHERE command_id = %s AND check_biom_merge = TRUE
                     ORDER BY name"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            outputs = qdb.sql_connection.TRN.execute_fetchflatten()

            sql = """SELECT ignore_parent_command
                     FROM qiita.software_command
                     WHERE command_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            ipc = qdb.sql_connection.TRN.execute_fetchlast()

            return {
                "parameters": params,
                "outputs": outputs,
                "ignore_parent_command": ipc,
            }

    @property
    def resource_allocation(self):
        """The resource allocation defined in the database for this command

        Returns
        -------
        str
        """

        with qdb.sql_connection.TRN:
            sql = """SELECT allocation FROM
                     qiita.processing_job_resource_allocation
                     WHERE name = %s and
                        job_type = 'RESOURCE_PARAMS_COMMAND'"""
            qdb.sql_connection.TRN.add(sql, [self.name])

            result = qdb.sql_connection.TRN.execute_fetchflatten()

            # if no matches for both type and name were found, query the
            # 'default' value for the type

            if not result:
                sql = """SELECT allocation FROM
                         qiita.processing_job_resource_allocation WHERE
                         name = %s and job_type = 'RESOURCE_PARAMS_COMMAND'"""
                qdb.sql_connection.TRN.add(sql, ["default"])

                result = qdb.sql_connection.TRN.execute_fetchflatten()
                if not result:
                    raise ValueError(
                        "Could not match '%s' to a resource allocation!" % self.name
                    )

        return result[0]

    @property
    def processing_jobs(self):
        """All the processing_jobs that used this command

        Returns
        -------
        list of qiita_db.processing_job.ProcessingJob
            List of jobs that used this command.
        """

        with qdb.sql_connection.TRN:
            sql = """SELECT processing_job_id FROM
                     qiita.processing_job
                     WHERE command_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])

            jids = qdb.sql_connection.TRN.execute_fetchflatten()

        return [qdb.processing_job.ProcessingJob(j) for j in jids]


class Software(qdb.base.QiitaObject):
    r"""A software package available in the system

    Attributes
    ----------
    name
    version
    description
    commands
    publications
    environment_name
    start_script

    Methods
    -------
    add_publications
    create

    See Also
    --------
    qiita_db.software.Command
    """

    _table = "software"

    @classmethod
    def iter(cls, active=True):
        """Iterates over all active software

        Parameters
        ----------
        active : bool, optional
            If True will only return active software

        Returns
        -------
        list of qiita_db.software.Software
            The software objects
        """
        sql = """SELECT software_id
                 FROM qiita.software {0}
                 ORDER BY software_id""".format("WHERE active = True" if active else "")
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add(sql)
            for s_id in qdb.sql_connection.TRN.execute_fetchflatten():
                yield cls(s_id)

    @classmethod
    def deactivate_all(cls):
        """Deactivates all the plugins in the system"""
        with qdb.sql_connection.TRN:
            sql = "UPDATE qiita.software SET active = False"
            qdb.sql_connection.TRN.add(sql)
            sql = "UPDATE qiita.software_command SET active = False"
            qdb.sql_connection.TRN.add(sql)
            qdb.sql_connection.TRN.execute()

    @classmethod
    def from_file(cls, fp, update=False):
        """Installs/updates a plugin from a plugin configuration file

        Parameters
        ----------
        fp : str
            Path to the plugin configuration file
        update : bool, optional
            If true, update the values in the database with the current values
            in the config file. Otherwise, use stored values and warn if config
            file contents and database contents do not match

        Returns
        -------
        qiita_db.software.Software
            The software object for the contents of `fp`

        Raises
        ------
        qiita_db.exceptions.QiitaDBOperationNotPermittedError
            If the plugin type in the DB and in the config file doesn't match
            If the (client_id, client_secret) pair in the DB and in the config
            file doesn't match
        """
        config = ConfigParser()
        with open(fp, newline=None) as conf_file:
            config.read_file(conf_file)

        name = config.get("main", "NAME")
        version = config.get("main", "VERSION")
        description = config.get("main", "DESCRIPTION")
        env_script = config.get("main", "ENVIRONMENT_SCRIPT")
        start_script = config.get("main", "START_SCRIPT")
        software_type = config.get("main", "PLUGIN_TYPE")
        publications = config.get("main", "PUBLICATIONS")
        publications = loads(publications) if publications else []
        client_id = config.get("oauth2", "CLIENT_ID")
        client_secret = config.get("oauth2", "CLIENT_SECRET")

        if cls.exists(name, version):
            # This plugin already exists, check that all the values are the
            # same and return the existing plugin
            with qdb.sql_connection.TRN:
                sql = """SELECT software_id
                         FROM qiita.software
                         WHERE name = %s AND version = %s"""
                qdb.sql_connection.TRN.add(sql, [name, version])
                instance = cls(qdb.sql_connection.TRN.execute_fetchlast())

                warning_values = []
                sql_update = """UPDATE qiita.software
                                SET {0} = %s
                                WHERE software_id = %s"""

                values = [description, env_script, start_script]
                attrs = ["description", "environment_script", "start_script"]
                for value, attr in zip(values, attrs):
                    if value != instance.__getattribute__(attr):
                        if update:
                            qdb.sql_connection.TRN.add(
                                sql_update.format(attr), [value, instance.id]
                            )
                        else:
                            warning_values.append(attr)

                # Having a different plugin type should be an error,
                # independently if the user is trying to update plugins or not
                if software_type != instance.type:
                    raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                        'The plugin type of the plugin "%s" version %s does '
                        "not match the one in the system" % (name, version)
                    )

                if publications != instance.publications:
                    if update:
                        instance.add_publications(publications)
                    else:
                        warning_values.append("publications")

                if (
                    client_id != instance.client_id
                    or client_secret != instance.client_secret
                ):
                    if update:
                        sql = """INSERT INTO qiita.oauth_identifiers
                                    (client_id, client_secret)
                                 SELECT %s, %s
                                 WHERE NOT EXISTS(SELECT *
                                                  FROM qiita.oauth_identifiers
                                                  WHERE client_id = %s
                                                    AND client_secret = %s)"""
                        qdb.sql_connection.TRN.add(
                            sql, [client_id, client_secret, client_id, client_secret]
                        )
                        sql = """UPDATE qiita.oauth_software
                                    SET client_id = %s
                                    WHERE software_id = %s"""
                        qdb.sql_connection.TRN.add(sql, [client_id, instance.id])
                    else:
                        raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                            "The (client_id, client_secret) pair of the "
                            'plugin "%s" version "%s" does not match the one '
                            "in the system" % (name, version)
                        )

                if warning_values:
                    warnings.warn(
                        'Plugin "%s" version "%s" config file does not match '
                        "with stored information. Check the config file or "
                        'run "qiita plugin update" to update the plugin '
                        "information. Offending values: %s"
                        % (name, version, ", ".join(sorted(warning_values))),
                        qdb.exceptions.QiitaDBWarning,
                    )
                qdb.sql_connection.TRN.execute()
        else:
            # This is a new plugin, create it
            instance = cls.create(
                name,
                version,
                description,
                env_script,
                start_script,
                software_type,
                publications=publications,
                client_id=client_id,
                client_secret=client_secret,
            )

        return instance

    @classmethod
    def exists(cls, name, version):
        """Returns whether the plugin (name, version) already exists

        Parameters
        ----------
        name : str
            The name of the plugin
        version : str
            The version of the plugin
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(
                        SELECT * FROM qiita.software
                        WHERE name = %s AND version = %s)"""
            qdb.sql_connection.TRN.add(sql, [name, version])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @classmethod
    def create(
        cls,
        name,
        version,
        description,
        environment_script,
        start_script,
        software_type,
        publications=None,
        client_id=None,
        client_secret=None,
    ):
        r"""Creates a new software in the system

        Parameters
        ----------
        name : str
            The name of the software
        version : str
            The version of the software
        description : str
            The description of the software
        environment_script : str
            The script used to start the environment in which the plugin runs
        start_script : str
            The script used to start the plugin
        software_type : str
            The type of the software
        publications : list of (str, str), optional
            A list with the (DOI, pubmed_id) of the publications attached to
            the software
        client_id : str, optional
            The client_id of the software. Default: randomly generated
        client_secret : str, optional
            The client_secret of the software. Default: randomly generated

        Raises
        ------
        qiita_db.exceptions.QiitaDBError
            If one of client_id or client_secret is provided but not both
        """
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.software
                            (name, version, description, environment_script,
                             start_script, software_type_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING software_id"""
            type_id = qdb.util.convert_to_id(software_type, "software_type")
            sql_params = [
                name,
                version,
                description,
                environment_script,
                start_script,
                type_id,
            ]
            qdb.sql_connection.TRN.add(sql, sql_params)
            s_id = qdb.sql_connection.TRN.execute_fetchlast()

            instance = cls(s_id)

            if publications:
                instance.add_publications(publications)

            id_is_none = client_id is None
            secret_is_none = client_secret is None

            if id_is_none and secret_is_none:
                # Both are none, generate new ones
                client_id = qdb.util.create_rand_string(50, punct=False)
                client_secret = qdb.util.create_rand_string(255, punct=False)
            elif id_is_none ^ secret_is_none:
                # One has been provided but not the other, raise an error
                raise qdb.exceptions.QiitaDBError(
                    'Plugin "%s" version "%s" cannot be created, please '
                    "provide both client_id and client_secret or none of them"
                    % (name, version)
                )

            # At this point both client_id and client_secret are defined
            sql = """INSERT INTO qiita.oauth_identifiers
                        (client_id, client_secret)
                     SELECT %s, %s
                     WHERE NOT EXISTS(SELECT *
                                      FROM qiita.oauth_identifiers
                                      WHERE client_id = %s
                                        AND client_secret = %s)"""
            qdb.sql_connection.TRN.add(
                sql, [client_id, client_secret, client_id, client_secret]
            )
            sql = """INSERT INTO qiita.oauth_software (software_id, client_id)
                     VALUES (%s, %s)"""
            qdb.sql_connection.TRN.add(sql, [s_id, client_id])

        return instance

    @classmethod
    def from_name_and_version(cls, name, version):
        """Returns the software object with the given name and version

        Parameters
        ----------
        name: str
            The software name
        version : str
            The software version

        Returns
        -------
        qiita_db.software.Software
            The software with the given name and version

        Raises
        ------
        qiita_db.exceptions.QiitaDBUnknownIDError
            If no software with the given name and version exists
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT software_id
                     FROM qiita.software
                     WHERE name = %s AND version = %s"""
            qdb.sql_connection.TRN.add(sql, [name, version])
            res = qdb.sql_connection.TRN.execute_fetchindex()
            if not res:
                raise qdb.exceptions.QiitaDBUnknownIDError(
                    "%s %s" % (name, version), cls._table
                )
            return cls(res[0][0])

    @property
    def name(self):
        """The name of the software

        Returns
        -------
        str
            The name of the software
        """
        with qdb.sql_connection.TRN:
            sql = "SELECT name FROM qiita.software WHERE software_id = %s"
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def version(self):
        """The version of the software

        Returns
        -------
        str
            The version of the software
        """
        with qdb.sql_connection.TRN:
            sql = "SELECT version FROM qiita.software WHERE software_id = %s"
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def description(self):
        """The description of the software

        Returns
        -------
        str
            The software description
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT description
                     FROM qiita.software
                     WHERE software_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def commands(self):
        """The list of commands attached to this software

        Returns
        -------
        list of qiita_db.software.Command
            The commands attached to this software package
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT command_id
                     FROM qiita.software_command
                     WHERE software_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return [
                Command(cid) for cid in qdb.sql_connection.TRN.execute_fetchflatten()
            ]

    def get_command(self, cmd_name):
        """Returns the command with the given name in the software

        Parameters
        ----------
        cmd_name: str
            The command with the given name

        Returns
        -------
        qiita_db.software.Command
            The command with the given name in this software
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT command_id
                     FROM qiita.software_command
                     WHERE software_id =%s AND name=%s"""
            qdb.sql_connection.TRN.add(sql, [self.id, cmd_name])
            res = qdb.sql_connection.TRN.execute_fetchindex()
            if not res:
                raise qdb.exceptions.QiitaDBUnknownIDError(cmd_name, "software_command")
            return Command(res[0][0])

    @property
    def publications(self):
        """The publications attached to the software

        Returns
        -------
        list of (str, str)
            The list of DOI and pubmed_id attached to the publication
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT p.doi, p.pubmed_id
                        FROM qiita.publication p
                            JOIN qiita.software_publication sp
                                ON p.doi = sp.publication_doi
                        WHERE sp.software_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchindex()

    def add_publications(self, publications):
        """Add publications to the software

        Parameters
        ----------
        publications : list of 2-tuples of str
            A list with the (DOI, pubmed_id) of the publications to be attached
            to the software

        Notes
        -----
        For more information about pubmed id, visit
        https://www.nlm.nih.gov/bsd/disted/pubmedtutorial/020_830.html
        """
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.publication (doi, pubmed_id)
                        SELECT %s, %s
                        WHERE NOT EXISTS(SELECT *
                                         FROM qiita.publication
                                         WHERE doi = %s)"""
            args = [[doi, pid, doi] for doi, pid in publications]
            qdb.sql_connection.TRN.add(sql, args, many=True)

            sql = """INSERT INTO qiita.software_publication
                            (software_id, publication_doi)
                        SELECT %s, %s
                        WHERE NOT EXISTS(SELECT *
                                         FROM qiita.software_publication
                                         WHERE software_id = %s AND
                                               publication_doi = %s)"""
            sql_params = [[self.id, doi, self.id, doi] for doi, _ in publications]
            qdb.sql_connection.TRN.add(sql, sql_params, many=True)
            qdb.sql_connection.TRN.execute()

    @property
    def environment_script(self):
        """The script used to start the plugin environment

        Returns
        -------
        str
            The script used to start the environment
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT environment_script
                     FROM qiita.software
                     WHERE software_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def start_script(self):
        """The script used to start the plugin

        Returns
        -------
        str
            The plugin's start script
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT start_script
                     FROM qiita.software
                     WHERE software_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def type(self):
        """Returns the type of the software

        Returns
        -------
        str
            The type of the software
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT software_type
                     FROM qiita.software_type
                        JOIN qiita.software USING (software_type_id)
                     WHERE software_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def deprecated(self):
        """Returns if the software is deprecated or not

        Returns
        -------
        bool
            Whether the software is deprecated or not
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT deprecated
                     FROM qiita.software
                     WHERE software_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @deprecated.setter
    def deprecated(self, deprecate):
        """Changes deprecated of the software

        Parameters
        ----------
        deprecate : bool
            New software deprecate value
        """
        sql = """UPDATE qiita.software SET deprecated = %s
                 WHERE software_id = %s"""
        qdb.sql_connection.perform_as_transaction(sql, [deprecate, self._id])

    @property
    def active(self):
        """Returns if the software is active or not

        Returns
        -------
        bool
            Whether the software is active or not
        """
        with qdb.sql_connection.TRN:
            sql = "SELECT active FROM qiita.software WHERE software_id = %s"
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    def activate(self):
        """Activates the plugin"""
        sql = """UPDATE qiita.software
                 SET active = %s
                 WHERE software_id = %s"""
        qdb.sql_connection.perform_as_transaction(sql, [True, self.id])

    @property
    def client_id(self):
        """Returns the client id of the plugin

        Returns
        -------
        str
            The client id of the software
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT client_id
                     FROM qiita.oauth_software
                     WHERE software_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def client_secret(self):
        """Returns the client secret of the plugin

        Returns
        -------
        str
            The client secrect of the plugin
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT client_secret
                     FROM qiita.oauth_software
                        JOIN qiita.oauth_identifiers USING (client_id)
                     WHERE software_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    def register_commands(self):
        """Registers the software commands"""
        url = "%s%s" % (qiita_config.base_url, qiita_config.portal_dir)
        cmd = '%s; %s "%s" "register" "ignored"' % (
            self.environment_script,
            self.start_script,
            url,
        )

        # it can be assumed that any command beginning with 'source'
        # is calling 'source', an internal command of 'bash' and hence
        # should be executed from bash, instead of sh.
        # TODO: confirm that exit_code propagates from bash to sh to
        # rv.
        if cmd.startswith("source"):
            cmd = "bash -c '%s'" % cmd

        p_out, p_err, rv = qdb.processing_job._system_call(cmd)

        if rv != 0:
            s = "cmd: %s\nexit status: %d\n" % (cmd, rv)
            s += "stdout: %s\nstderr: %s\n" % (p_out, p_err)

            raise ValueError(s)


class DefaultParameters(qdb.base.QiitaObject):
    """Models a default set of parameters of a command

    Attributes
    ----------
    name
    values

    Methods
    -------
    exists
    create
    iter
    to_str
    to_file

    See Also
    --------
    qiita_db.software.Command
    """

    _table = "default_parameter_set"

    @classmethod
    def exists(cls, command, **kwargs):
        r"""Check if a parameter set already exists

        Parameters
        ----------
        command : qiita_db.software.Command
            The command to which the parameter set belongs to
        kwargs : dict of {str: str}
            The parameters and their values

        Returns
        -------
        bool
            Whether if the parameter set exists in the given command

        Raises
        ------
        qiita_db.exceptions.QiitaDBError
            - If there are missing parameters for the given command
            - If `kwargs` contains parameters not originally defined in the
            command
        """
        with qdb.sql_connection.TRN:
            command_params = set(command.optional_parameters)
            user_params = set(kwargs)

            missing_in_user = command_params - user_params
            extra_in_user = user_params - command_params

            if missing_in_user or extra_in_user:
                raise qdb.exceptions.QiitaDBError(
                    "The given set of parameters do not match the ones for "
                    "the command.\nMissing parameters: %s\n"
                    "Extra parameters: %s\n"
                    % (", ".join(missing_in_user), ", ".join(extra_in_user))
                )

            sql = """SELECT parameter_set
                     FROM qiita.default_parameter_set
                     WHERE command_id = %s"""
            qdb.sql_connection.TRN.add(sql, [command.id])
            for p_set in qdb.sql_connection.TRN.execute_fetchflatten():
                if p_set == kwargs:
                    return True

            return False

    @classmethod
    def create(cls, param_set_name, command, **kwargs):
        r"""Create a new parameter set for the given command

        Parameters
        ----------
        param_set_name: str
            The name of the new parameter set
        command : qiita_db.software.Command
            The command to add the new parameter set
        kwargs : dict
            The parameters and their values

        Returns
        -------
        qiita_db.software.Parameters
            The new parameter set instance

        Raises
        ------
        qiita_db.exceptions.QiitaDBError
            - If there are missing parameters for the given command
            - If there are extra parameters in `kwargs` than for the given
              command
        qdb.exceptions.QiitaDBDuplicateError
            - If the parameter set already exists
        """
        with qdb.sql_connection.TRN:
            # setting to default values all parameters not in the user_params
            cmd_params = command.optional_parameters
            missing_in_user = {
                k: cmd_params[k][1] for k in (set(cmd_params) - set(kwargs))
            }
            if missing_in_user:
                kwargs.update(missing_in_user)

            # If the columns in kwargs and command do not match, cls.exists
            # will raise the error for us
            if cls.exists(command, **kwargs):
                raise qdb.exceptions.QiitaDBDuplicateError(
                    cls._table, "Values: %s" % kwargs
                )

            sql = """INSERT INTO qiita.default_parameter_set
                        (command_id, parameter_set_name, parameter_set)
                     VALUES (%s, %s, %s)
                     RETURNING default_parameter_set_id"""
            sql_args = [command.id, param_set_name, dumps(kwargs)]
            qdb.sql_connection.TRN.add(sql, sql_args)

            return cls(qdb.sql_connection.TRN.execute_fetchlast())

    @property
    def name(self):
        """The name of the parameter set

        Returns
        -------
        str
            The name of the parameter set
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT parameter_set_name
                     FROM qiita.default_parameter_set
                     WHERE default_parameter_set_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def values(self):
        """The values of the parameter set

        Returns
        -------
        dict of {str: object}
            Dictionary with the parameters values keyed by parameter name
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT parameter_set
                     FROM qiita.default_parameter_set
                     WHERE default_parameter_set_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def command(self):
        """The command that this parameter set belongs to

        Returns
        -------
        qiita_db.software.Command
            The command that this parameter set belongs to
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT command_id
                     FROM qiita.default_parameter_set
                     WHERE default_parameter_set_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return Command(qdb.sql_connection.TRN.execute_fetchlast())


class Parameters(object):
    """Represents an instance of parameters used to process an artifact

    Raises
    ------
    qiita_db.exceptions.QiitaDBOperationNotPermittedError
        If trying to instantiate this class directly. In order to instantiate
        this class, the classmethods `load` or `from_default_params` should
        be used.
    """

    def __eq__(self, other):
        """Equality based on the parameter values and the command"""
        if type(self) is not type(other):
            return False
        if self.command != other.command:
            return False
        if self.values != other.values:
            return False
        return True

    @classmethod
    def load(cls, command, json_str=None, values_dict=None):
        """Load the parameters set form a json str or from a dict of values

        Parameters
        ----------
        command : qiita_db.software.Command
            The command to which the parameter set belongs to
        json_str : str, optional
            The json string encoding the parameters
        values_dict : dict of {str: object}, optional
            The dictionary with the parameter values

        Returns
        -------
        qiita_db.software.Parameters
            The loaded parameter set

        Raises
        ------
        qiita_db.exceptions.QiitaDBError
            - If `json_str` and `values` are both provided
            - If neither `json_str` or `values` are provided
            - If `json_str` or `values` do not encode a parameter set of
            the provided command.

        Notes
        -----
        The parameters `json_str` and `values_dict` are mutually exclusive,
        only one of them should be provided at a time. However, one of them
        should always be provided.
        """
        if json_str is None and values_dict is None:
            raise qdb.exceptions.QiitaDBError(
                "Either `json_str` or `values_dict` should be provided."
            )
        elif json_str is not None and values_dict is not None:
            raise qdb.exceptions.QiitaDBError(
                "Either `json_str` or `values_dict` should be provided, but not both"
            )
        elif json_str is not None:
            parameters = loads(json_str)

            error_msg = (
                "The provided JSON string doesn't encode a "
                "parameter set for command '%s (ID: %s)'" % (command.name, command.id)
            )
        else:
            if not isinstance(values_dict, dict):
                raise qdb.exceptions.QiitaDBError(
                    "The provided value_dict is %s (i.e. not None) but also "
                    "not a dictionary for command %s" % (values_dict, command.id)
                )
            parameters = deepcopy(values_dict)
            error_msg = (
                "The provided values dictionary doesn't encode a "
                "parameter set for command %s" % command.id
            )

        # setting to default values all parameters not in the user_params
        cmd_params = command.optional_parameters
        missing_in_user = {
            k: cmd_params[k][1] for k in (set(cmd_params) - set(parameters))
        }
        if missing_in_user:
            parameters.update(missing_in_user)

        with qdb.sql_connection.TRN:
            cmd_reqd_params = command.required_parameters
            cmd_opt_params = command.optional_parameters

            values = {}
            for key in cmd_reqd_params:
                try:
                    values[key] = parameters.pop(key)
                except KeyError:
                    raise qdb.exceptions.QiitaDBError(
                        "%s. Missing required parameter: %s" % (error_msg, key)
                    )

            for key in cmd_opt_params:
                try:
                    values[key] = parameters.pop(key)
                except KeyError:
                    raise qdb.exceptions.QiitaDBError(
                        "%s. Missing optional parameter: %s" % (error_msg, key)
                    )

            if parameters:
                error_msg += f"--- {cmd_reqd_params} --- {cmd_opt_params}"
                raise qdb.exceptions.QiitaDBError(
                    "%s. Extra parameters: %s"
                    % (error_msg, ", ".join(parameters.keys()))
                )

            return cls(values, command)

    @classmethod
    def from_default_params(cls, dflt_params, req_params, opt_params=None):
        """Creates the parameter set from a `dflt_params` set

        Parameters
        ----------
        dflt_params : qiita_db.software.DefaultParameters
            The DefaultParameters object in which this instance is based on
        req_params : dict of {str: object}
            The required parameters values, keyed by parameter name
        opt_params : dict of {str: object}, optional
            The optional parameters to change from the default set, keyed by
            parameter name. Default: None, use the values in `dflt_params`

        Raises
        ------
        QiitaDBError
            - If there are missing requried parameters
            - If there is an unknown required ot optional parameter
        """
        with qdb.sql_connection.TRN:
            command = dflt_params.command
            cmd_req_params = command.required_parameters
            cmd_opt_params = command.optional_parameters

            missing_reqd = set(cmd_req_params) - set(req_params)
            extra_reqd = set(req_params) - set(cmd_req_params)
            if missing_reqd or extra_reqd:
                raise qdb.exceptions.QiitaDBError(
                    "Provided required parameters not expected.\n"
                    "Missing required parameters: %s\n"
                    "Extra required parameters: %s\n"
                    % (", ".join(missing_reqd), ", ".join(extra_reqd))
                )

            if opt_params:
                extra_opts = set(opt_params) - set(cmd_opt_params)
                if extra_opts:
                    raise qdb.exceptions.QiitaDBError(
                        "Extra optional parameters provded: %s" % ", ".join(extra_opts)
                    )

            values = dflt_params.values
            values.update(req_params)

            if opt_params:
                values.update(opt_params)

            return cls(values, command)

    def __init__(self, values, command):
        # Time for some python magic! The __init__ function should not be used
        # outside of this module, users should always be using one of the above
        # classmethods to instantiate the object. Lets test that it is the case
        # First, we are going to get the current frame (i.e. this __init__)
        # function and the caller to the __init__
        current_frame = inspect.currentframe()
        caller_frame = current_frame.f_back
        # The file names where the function is defined is stored in the
        # f_code.co_filename attribute, and in this case it has to be the same
        # for both of them. Also, we are restricing that the name of the caller
        # should be either `load` or `from_default_params`, which are the two
        # classmethods defined above
        current_file = current_frame.f_code.co_filename
        caller_file = caller_frame.f_code.co_filename
        caller_name = caller_frame.f_code.co_name
        if current_file != caller_file or caller_name not in [
            "load",
            "from_default_params",
        ]:
            raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                "qiita_db.software.Parameters can't be instantiated directly. "
                "Please use one of the classmethods: `load` or "
                "`from_default_params`"
            )

        self._values = values
        self._command = command

    @property
    def command(self):
        """The command to which this parameter set belongs to

        Returns
        -------
        qiita_db.software.Command
            The command to which this parameter set belongs to
        """
        return self._command

    @property
    def values(self):
        """The values of the parameters

        Returns
        -------
        dict of {str: object}
            The parameter values keyed by parameter name
        """
        return self._values

    def dump(self):
        """Return the values in the parameter as JSON

        Returns
        -------
        str
            The parameter values as a JSON string
        """
        return dumps(self._values, sort_keys=True)


class DefaultWorkflowNode(qdb.base.QiitaObject):
    r"""Represents a node in a default software workflow

    Attributes
    ----------
    command
    parameters
    """

    _table = "default_workflow_node"

    @property
    def default_parameter(self):
        """The default parameter set to use in this node

        Returns
        -------
        qiita_db.software.DefaultParameters
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT default_parameter_set_id
                     FROM qiita.default_workflow_node
                     WHERE default_workflow_node_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            params_id = qdb.sql_connection.TRN.execute_fetchlast()
            return qdb.software.DefaultParameters(params_id)


class DefaultWorkflowEdge(qdb.base.QiitaObject):
    r"""Represents an edge in a default software workflow

    Attributes
    ----------
    connections
    """

    _table = "default_workflow_edge"

    @property
    def connections(self):
        """Retrieve how the commands are connected using this edge

        Returns
        -------
        list of [str, str]
            The list of pairs of output parameter name and input parameter name
            used to connect the output of the source command to the input of
            the destination command.
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT name, parameter_name, artifact_type
                     FROM qiita.default_workflow_edge_connections c
                        JOIN qiita.command_output o
                            ON c.parent_output_id = o.command_output_id
                        JOIN qiita.command_parameter p
                            ON c.child_input_id = p.command_parameter_id
                        LEFT JOIN qiita.artifact_type USING (artifact_type_id)
                     WHERE default_workflow_edge_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchindex()


class DefaultWorkflow(qdb.base.QiitaObject):
    r"""Represents a software's default workflow

    A default workflow is defined by a Directed Acyclic Graph (DAG) in which
    the nodes represent the commands to be executed with the default parameter
    set to use and the edges represent the command precedence, including
    which outputs of the source command are provided as input to the
    destination command.
    """

    _table = "default_workflow"

    @classmethod
    def iter(cls, active=True):
        """Iterates over all active DefaultWorkflow

        Parameters
        ----------
        active : bool, optional
            If True will only return active software

        Returns
        -------
        list of qiita_db.software.DefaultWorkflow
            The DefaultWorkflow objects
        """
        sql = """SELECT default_workflow_id
                 FROM qiita.default_workflow {0}
                 ORDER BY default_workflow_id""".format(
            "WHERE active = True" if active else ""
        )
        with qdb.sql_connection.TRN:
            qdb.sql_connection.TRN.add(sql)
            for s_id in qdb.sql_connection.TRN.execute_fetchflatten():
                yield cls(s_id)

    @property
    def active(self):
        """Retrieves active status of the default workflow

        Returns
        -------
        active : bool
            active value
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT active
                     FROM qiita.default_workflow
                     WHERE default_workflow_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @active.setter
    def active(self, active):
        """Changes active status of the default workflow

        Parameters
        ----------
        active : bool
            New active value
        """
        sql = """UPDATE qiita.default_workflow SET active = %s
                 WHERE default_workflow_id = %s"""
        qdb.sql_connection.perform_as_transaction(sql, [active, self._id])

    @property
    def name(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT name
                     FROM qiita.default_workflow
                     WHERE default_workflow_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def description(self):
        """Retrieves the description of the default workflow

        Returns
        -------
        str
            description value
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT description
                     FROM qiita.default_workflow
                     WHERE default_workflow_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @description.setter
    def description(self, description):
        """Changes the description of the default workflow

        Parameters
        ----------
        description : str
            New description value
        """
        sql = """UPDATE qiita.default_workflow SET description = %s
                 WHERE default_workflow_id = %s"""
        qdb.sql_connection.perform_as_transaction(sql, [description, self._id])

    @property
    def data_type(self):
        """Retrieves all the data_types accepted by the default workflow

        Returns
        ----------
        list of str
            The data types
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT data_type
                     FROM qiita.default_workflow_data_type
                     LEFT JOIN qiita.data_type USING (data_type_id)
                     WHERE default_workflow_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchflatten()

    @property
    def artifact_type(self):
        """Retrieves artifact_type that the workflow can be applied to

        Returns
        ----------
        str
            The name of the artifact type this workflow can be applied to
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT artifact_type
                     FROM qiita.artifact_type
                     LEFT JOIN qiita.default_workflow USING (artifact_type_id)
                     WHERE default_workflow_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchflatten()[0]

    @property
    def graph(self):
        """Returns the graph that represents the workflow

        Returns
        -------
        networkx.DiGraph
            The graph representing the default workflow.
        """
        g = nx.DiGraph()
        with qdb.sql_connection.TRN:
            # Retrieve all graph workflow nodes
            sql = """SELECT default_workflow_node_id
                     FROM qiita.default_workflow_node
                     WHERE default_workflow_id = %s
                     ORDER BY default_workflow_node_id"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            db_nodes = qdb.sql_connection.TRN.execute_fetchflatten()

            nodes = {n_id: DefaultWorkflowNode(n_id) for n_id in db_nodes}

            # Retrieve all graph edges
            sql = """SELECT DISTINCT default_workflow_edge_id, parent_id,
                                     child_id
                     FROM qiita.default_workflow_edge e
                        JOIN qiita.default_workflow_node n
                            ON e.parent_id = n.default_workflow_node_id
                            OR e.child_id = n.default_workflow_node_id
                     WHERE default_workflow_id = %s
                     ORDER BY default_workflow_edge_id"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            db_edges = qdb.sql_connection.TRN.execute_fetchindex()

            # let's track what nodes are actually being used so if they do not
            # have an edge we still return them as part of the graph
            used_nodes = nodes.copy()
            for edge_id, p_id, c_id in db_edges:
                e = DefaultWorkflowEdge(edge_id)
                g.add_edge(nodes[p_id], nodes[c_id], connections=e)
                if p_id in used_nodes:
                    del used_nodes[p_id]
                if c_id in used_nodes:
                    del used_nodes[c_id]
            # adding the missing nodes
            for ms in used_nodes:
                g.add_node(nodes[ms])

        return g

    @property
    def parameters(self):
        """Retrieves the parameters that the workflow can be applied to

        Returns
        ----------
        dict, dict
            The dictionary of valid key: value pairs given by the sample or
            the preparation info file
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT parameters
                     FROM qiita.default_workflow
                     WHERE default_workflow_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchflatten()[0]

    @parameters.setter
    def parameters(self, values):
        """Sets the parameters that the workflow can be applied to

        Parameters
        ----------
        dict : {'sample': dict, 'prep': dict}
            dict of dict with the key: value pairs for the 'sample' and 'prep'
            info files

        Raises
        ------
        ValueError
            if the passed parameter is not a properly formated dict
        """
        if not isinstance(values, dict) or set(values.keys()) != set(
            ["prep", "sample"]
        ):
            raise ValueError(
                "Improper format for values, should be {'sample': dict, 'prep': dict} "
            )
        with qdb.sql_connection.TRN:
            sql = """UPDATE qiita.default_workflow
                     SET parameters = %s
                     WHERE default_workflow_id = %s"""
            qdb.sql_connection.perform_as_transaction(sql, [dumps(values), self._id])
