# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import dumps, loads

import qiita_db as qdb


class Command(qdb.base.QiitaObject):
    r"""An executable command available in the system

    Attributes
    ----------
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

        If the default value for a parameter is NULL, then the parameter will
        be required. On the other hand, if it is provided, the parameter will
        be optional and the default value will be used when the user doesn't
        overwrite it.

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
            format is: {parameter_name: (paramter_type, default)},
            where parameter_name, paramter_type and default are strings. If
            default is None,

        Returns
        -------
        qiita_db.software.Command
            The newly created command

        Raises
        ------
        QiitaDBError
            - If the parameters dictionary is malformed
            - If one of the parameter types is not supported
            - If the default value of a choice parameter is not listed in
            the available choices
        QiitaDBDuplicateError
            - If the command already exists
        """
        # Perform some sanity checks in the parameters dictionary
        sql_param_values = []
        for pname, vals in parameters.items():
            if len(vals) != 2:
                raise qdb.exceptions.QiitaDBError(
                    "Malformed parameters dictionary, the format should be "
                    "{param_name: [paramter_type, default]}. Found: "
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
        dict of {parameter_name: [ptype, dflt]}
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
        dict of {parameter_name: ptype}
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
        dict of {parameter_name: [ptype, default]}
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
    def create(cls, name, version, description, publications=None):
        r"""Creates a new software in the system

        Parameters
        ----------
        name : str
            The name of the software
        version : str
            The version of the software
        description : str
            The description of the software
        publications : list of (str, str), optional
            A list with the (DOI, pubmed_id) of the publications attached to
            the software
        """
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.software (name, version, description)
                        VALUES (%s, %s, %s)
                        RETURNING software_id"""
            sql_params = [name, version, description]
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
        kwargs : dict
            The parameters and their values

        Returns
        -------
        bool
            Whether if the parameter set exists in the given command

        Raises
        ------
        qiita_db.exceptions.QiitaDBError
            - If there are missing parameters for the given command
            - If there are extra parameters in `kwargs` than for the given
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
        dict
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
