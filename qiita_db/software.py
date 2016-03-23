# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import dumps, loads
from copy import deepcopy
import inspect

import networkx as nx

import qiita_db as qdb


class Command(qdb.base.QiitaObject):
    r"""An executable command available in the system

    Attributes
    ----------
    software
    name
    description
    cli
    parameters_table

    Methods
    -------
    create

    See Also
    --------
    qiita_db.software.Software
    """
    _table = "software_command"

    @classmethod
    def get_commands_by_input_type(cls, artifact_types):
        """Returns the commands that can process the given artifact types

        Parameters
        ----------
        artifact_type : list of str
            The artifact types

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
                     WHERE artifact_type IN %s"""
            qdb.sql_connection.TRN.add(sql, [tuple(artifact_types)])
            for c_id in qdb.sql_connection.TRN.execute_fetchflatten():
                yield cls(c_id)

    @classmethod
    def get_html_generator(cls, artifact_type):
        """Returns the command that genearete the HTML for the given artifact

        Parameters
        ----------
        artifact : str
            The artifact type to search the HTML generator for

        Returns
        -------
        qiita_db.software.Command
            The newly created command

        Raises
        ------
        qdb.exceptions.QiitaDBError
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT command_id
                     FROM qiita.software_command
                        JOIN qiita.software_artifact_type USING (software_id)
                        JOIN qiita.artifact_type USING (artifact_type_id)
                     WHERE artifact_type = %s
                        AND name = 'Generate HTML summary'"""
            qdb.sql_connection.TRN.add(sql, [artifact_type])
            try:
                res = qdb.sql_connection.TRN.execute_fetchlast()
            except IndexError:
                raise qdb.exceptions.QiitaDBError(
                    "There is no command to generate the HTML summary for "
                    "artifact type '%s'" % artifact_type)

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
    def create(cls, software, name, description, parameters):
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
            format is: {parameter_name: (parameter_type, default)},
            where parameter_name, parameter_type and default are strings. If
            default is None.

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
                "be provided." % name)
        sql_param_values = []
        for pname, vals in parameters.items():
            if len(vals) != 2:
                raise qdb.exceptions.QiitaDBError(
                    "Malformed parameters dictionary, the format should be "
                    "{param_name: [parameter_type, default]}. Found: "
                    "%s for parameter name %s" % (vals, pname))

            ptype, dflt = vals
            # Check that the type is one of the supported types
            supported_types = ['string', 'integer', 'float', 'artifact',
                               'reference']
            if ptype not in supported_types and not ptype.startswith('choice'):
                supported_types.append('choice')
                raise qdb.exceptions.QiitaDBError(
                    "Unsupported parameters type '%s' for parameter %s. "
                    "Supported types are: %s"
                    % (ptype, pname, ', '.join(supported_types)))

            if ptype.startswith('choice') and dflt is not None:
                choices = loads(ptype.split(':')[1])
                if dflt not in choices:
                    raise qdb.exceptions.QiitaDBError(
                        "The default value '%s' for the parameter %s is not "
                        "listed in the available choices: %s"
                        % (dflt, pname, ', '.join(choices)))

            if dflt is not None:
                sql_param_values.append([pname, ptype, False, dflt])
            else:
                sql_param_values.append([pname, ptype, True, None])

        with qdb.sql_connection.TRN:
            if cls.exists(software, name):
                raise qdb.exceptions.QiitaDBDuplicateError(
                    "command", "software: %d, name: %s"
                               % (software.id, name))
            # Add the command to the DB
            sql = """INSERT INTO qiita.software_command
                            (name, software_id, description)
                     VALUES (%s, %s, %s)
                     RETURNING command_id"""
            sql_params = [name, software.id, description]
            qdb.sql_connection.TRN.add(sql, sql_params)
            c_id = qdb.sql_connection.TRN.execute_fetchlast()

            # Add the parameters to the DB
            sql = """INSERT INTO qiita.command_parameter
                        (command_id, parameter_name, parameter_type, required,
                         default_value)
                     VALUES (%s, %s, %s, %s, %s)"""
            sql_params = [[c_id, pname, p_type, reqd, default]
                          for pname, p_type, reqd, default in sql_param_values]
            qdb.sql_connection.TRN.add(sql, sql_params, many=True)
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
            sql = """SELECT parameter_name, parameter_type
                     FROM qiita.command_parameter
                     WHERE command_id = %s AND required = true"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            res = qdb.sql_connection.TRN.execute_fetchindex()
            return {pname: ptype for pname, ptype in res}

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
            return {pname: [ptype, dflt] for pname, ptype, dflt in res}

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
    def create(cls, name, version, description, environment_script,
               start_script, software_type, publications=None):
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
        """
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.software
                            (name, version, description, environment_script,
                             start_script, software_type_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING software_id"""
            type_id = qdb.util.convert_to_id(software_type, "software_type")
            sql_params = [name, version, description, environment_script,
                          start_script, type_id]
            qdb.sql_connection.TRN.add(sql, sql_params)
            s_id = qdb.sql_connection.TRN.execute_fetchlast()

            instance = cls(s_id)

            if publications:
                instance.add_publications(publications)

        return instance

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
            return [Command(cid)
                    for cid in qdb.sql_connection.TRN.execute_fetchflatten()]

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
                        VALUES (%s, %s)"""
            qdb.sql_connection.TRN.add(sql, publications, many=True)

            sql = """INSERT INTO qiita.software_publication
                            (software_id, publication_doi)
                        VALUES (%s, %s)"""
            sql_params = [[self.id, doi] for doi, _ in publications]
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
    def default_workflows(self):
        """Returns the default workflows attached to the current software

        Returns
        -------
        generator of qiita_db.software.DefaultWorkflow
            The defaultworkflows attached to the software
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT default_workflow_id
                     FROM qiita.default_workflow
                     WHERE software_id = %s
                     ORDER BY default_workflow_id"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            for wf_id in qdb.sql_connection.TRN.execute_fetchflatten():
                yield DefaultWorkflow(wf_id)

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
    _table = 'default_parameter_set'

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
                    % (', '.join(missing_in_user), ', '.join(extra_in_user)))

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
            # If the columns in kwargs and command do not match, cls.exists
            # will raise the error for us
            if cls.exists(command, **kwargs):
                raise qdb.exceptions.QiitaDBDuplicateError(
                    cls._table, "Values: %s" % kwargs)

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
        if type(self) != type(other):
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
                "Either `json_str` or `values_dict` should be provided.")
        elif json_str is not None and values_dict is not None:
            raise qdb.exceptions.QiitaDBError(
                "Either `json_str` or `values_dict` should be provided, "
                "but not both")
        elif json_str is not None:
            parameters = loads(json_str)
            error_msg = ("The provided JSON string doesn't encode a "
                         "parameter set for command %s" % command.id)
        else:
            parameters = deepcopy(values_dict)
            error_msg = ("The provided values dictionary doesn't encode a "
                         "parameter set for command %s" % command.id)

        with qdb.sql_connection.TRN:
            cmd_reqd_params = command.required_parameters
            cmd_opt_params = command.optional_parameters

            values = {}
            for key in cmd_reqd_params:
                try:
                    values[key] = parameters.pop(key)
                except KeyError:
                    raise qdb.exceptions.QiitaDBError(
                        "%s. Missing required parameter: %s"
                        % (error_msg, key))

            for key in cmd_opt_params:
                try:
                    values[key] = parameters.pop(key)
                except KeyError:
                    raise qdb.exceptions.QiitaDBError(
                        "%s. Missing optional parameter: %s"
                        % (error_msg, key))

            if parameters:
                raise qdb.exceptions.QiitaDBError(
                    "%s. Extra parameters: %s"
                    % (error_msg, ', '.join(parameters.keys())))

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
                    % (', '.join(missing_reqd), ', '.join(extra_reqd)))

            if opt_params:
                extra_opts = set(opt_params) - set(cmd_opt_params)
                if extra_opts:
                    raise qdb.exceptions.QiitaDBError(
                        "Extra optional parameters provded: %s"
                        % ', '.join(extra_opts))

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
        if current_file != caller_file or \
                caller_name not in ['load', 'from_default_params']:
            raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                "qiita_db.software.Parameters can't be instantiated directly. "
                "Please use one of the classmethods: `load` or "
                "`from_default_params`")

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
    def command(self):
        """The command to execute in this node

        Returns
        -------
        qiita_db.software.Command
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT command_id
                     FROM qiita.default_workflow_node
                     WHERE default_workflow_node_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            cmd_id = qdb.sql_connection.TRN.execute_fetchlast()
            return qdb.software.Command(cmd_id)

    @property
    def parameters(self):
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
            sql = """SELECT name, parameter_name
                     FROM qiita.default_workflow_edge_connections c
                        JOIN qiita.command_output o
                            ON c.parent_output_id = o.command_output_id
                        JOIN qiita.command_parameter p
                            ON c.child_input_id = p.command_parameter_id
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

    @property
    def name(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT name
                     FROM qiita.default_workflow
                     WHERE default_workflow_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

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
                     WHERE default_workflow_id = %s"""
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
                     WHERE default_workflow_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            db_edges = qdb.sql_connection.TRN.execute_fetchindex()

            for edge_id, p_id, c_id in db_edges:
                e = DefaultWorkflowEdge(edge_id)
                g.add_edge(nodes[p_id], nodes[c_id], connections=e)
        return g
