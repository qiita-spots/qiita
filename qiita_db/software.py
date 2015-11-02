# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from .base import QiitaObject
from .sql_connection import TRN
from .exceptions import (QiitaDBDuplicateError, QiitaDBError,
                         QiitaDBUnknownIDError)
from .util import get_table_cols, get_table_cols_w_type


class Command(QiitaObject):
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
        with TRN:
            sql = """SELECT EXISTS(
                        SELECT *
                        FROM qiita.software_command
                        WHERE command_id = %s)"""
            TRN.add(sql, [id_])
            return TRN.execute_fetchlast()

    @classmethod
    def create(cls, software, name, description, cli_cmd, parameters_table):
        r"""Creates a new command in the system

        Parameters
        ----------
        software : qiita_db.software.Software
            The software to which this command belongs to.
        name : str
            The name of the command
        description : str
            The description of the command
        cli_cmd : str
            The CLI used to call this command
        parameters_table : str
            The name of the table in which the parameters of the commands are
            stored

        Returns
        -------
        qiita_db.software.Command
            The newly created command
        """
        with TRN:
            sql = """INSERT INTO qiita.software_command
                            (name, software_id, description, cli_cmd,
                             parameters_table)
                     VALUES (%s, %s, %s, %s, %s)
                     RETURNING command_id"""
            sql_params = [name, software.id, description, cli_cmd,
                          parameters_table]
            TRN.add(sql, sql_params)
            c_id = TRN.execute_fetchlast()

        return cls(c_id)

    @property
    def name(self):
        """The name of the command

        Returns
        -------
        str
            The name of the command
        """
        with TRN:
            sql = """SELECT name
                     FROM qiita.software_command
                     WHERE command_id = %s"""
            TRN.add(sql, [self.id])
            return TRN.execute_fetchlast()

    @property
    def description(self):
        """The description of the command

        Returns
        -------
        str
            The description of the command
        """
        with TRN:
            sql = """SELECT description
                     FROM qiita.software_command
                     WHERE command_id = %s"""
            TRN.add(sql, [self.id])
            return TRN.execute_fetchlast()

    @property
    def cli(self):
        """The CLI used to call the command

        Returns
        -------
        str
            The CLI used to call the command
        """
        with TRN:
            sql = """SELECT cli_cmd
                     FROM qiita.software_command
                     WHERE command_id = %s"""
            TRN.add(sql, [self.id])
            return TRN.execute_fetchlast()

    @property
    def parameters_table(self):
        """The table in which the parameters of th e command are stored

        Returns
        -------
        str
            The name of the table
        """
        with TRN:
            sql = """SELECT parameters_table
                     FROM qiita.software_command
                     WHERE command_id = %s"""
            TRN.add(sql, [self.id])
            return TRN.execute_fetchlast()


class Software(QiitaObject):
    r"""A software available in the system

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
        publications : list of 2-tuples of str
            A list with the (DOI, pubmed_id) of the publications attached to
            the software
        """
        with TRN:
            sql = """INSERT INTO qiita.software (name, version, description)
                        VALUES (%s, %s, %s)
                        RETURNING software_id"""
            sql_params = [name, version, description]
            TRN.add(sql, sql_params)
            s_id = TRN.execute_fetchlast()

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
        with TRN:
            sql = "SELECT name FROM qiita.software WHERE software_id = %s"
            TRN.add(sql, [self.id])
            return TRN.execute_fetchlast()

    @property
    def version(self):
        """The version of the software

        Returns
        -------
        str
            The version of the software
        """
        with TRN:
            sql = "SELECT version FROM qiita.software WHERE software_id = %s"
            TRN.add(sql, [self.id])
            return TRN.execute_fetchlast()

    @property
    def description(self):
        """The description of the software

        Returns
        -------
        str
            The software description
        """
        with TRN:
            sql = """SELECT description
                     FROM qiita.software
                     WHERE software_id = %s"""
            TRN.add(sql, [self.id])
            return TRN.execute_fetchlast()

    @property
    def commands(self):
        """The list of commands attached to this software

        Returns
        -------
        list of int
            The command identifiers
        """
        with TRN:
            sql = """SELECT command_id
                     FROM qiita.software_command
                     WHERE software_id = %s"""
            TRN.add(sql, [self.id])
            return TRN.execute_fetchflatten()

    @property
    def publications(self):
        """The publications attached to the software

        Returns
        -------
        list of 2-tuples of str
            The list of DOI and pubmed_id attached to the publication
        """
        with TRN:
            sql = """SELECT p.doi, p.pubmed_id
                        FROM qiita.publication p
                            JOIN qiita.software_publication sp
                                ON p.doi = sp.publication_doi
                        WHERE sp.software_id = %s"""
            TRN.add(sql, [self.id])
            return TRN.execute_fetchindex()

    def add_publications(self, publications):
        """Add publications to the software

        Parameters
        ----------
        publications : list of 2-tuples of str
            A list with the (DOI, pubmed_id) of the publications to be attached
            to the software
        """
        with TRN:
            sql = """INSERT INTO qiita.publication (doi, pubmed_id)
                        VALUES (%s, %s)"""
            TRN.add(sql, publications, many=True)

            sql = """INSERT INTO qiita.software_publication
                            (software_id, publication_doi)
                        VALUES (%s, %s)"""
            sql_params = [[self.id, doi] for doi, _ in publications]
            TRN.add(sql, sql_params, many=True)
            TRN.execute()


class Parameters(object):
    """Models a specific set of parameters of a command

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

    def __init__(self, id_, command):
        """Initializes the object

        Parameters
        ----------
        id_: int
            The parameter set identifier
        command : qiita_db.software.Command
            The command to which the parameter is requested

        Raises
        ------
        QiitaDBUnknownIDError
            If `id_` does not correspond to a parameter set for the given
            command
        """
        with TRN:
            self._table = command.parameters_table
            self.id = id_
            sql = """SELECT EXISTS(
                        SELECT *
                        FROM qiita.{0}
                        WHERE parameters_id = %s)""".format(self.table)
            TRN.add(sql, [self.id])
            if not TRN.execute_fetchlast():
                raise QiitaDBUnknownIDError(self.id, self._table)

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
        """
        with TRN:
            table = command.parameters_table
            cls._check_columns(table, **kwargs)

            db_cols = set(get_table_cols(table))
            db_cols.remove("param_set_name")
            db_cols.remove("parameters_id")
            missing = db_cols.difference(kwargs)

            if missing:
                raise QiitaDBError(
                    "Missing parameters for command %s: %s"
                    % (command.name, ', '.join(missing)))

            extra = set(kwargs).difference(db_cols)
            if extra:
                raise QiitaDBError(
                    "Extra parameters for command %s: %s"
                    % (command.name, ', '.join(extra)))

            cols = ["{} = %s".format(col) for col in kwargs]
            sql = "SELECT EXISTS(SELECT * FROM qiita.{0} WHERE {1})".format(
                table, ' AND '.join(cols))
            TRN.add(sql, kwargs.values())
            return TRN.execute_fetchlast()

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
        """
        with TRN:
            if cls.exists(command, **kwargs):
                raise QiitaDBDuplicateError(command.parameters_table,
                                            "Values: %s" % kwargs)

            vals = kwargs.values()
            vals.insert(0, param_set_name)

            sql = """INSERT INTO qiita.{0} (param_set_name, {1})
                     VALUES (%s, {2})
                     RETURNING parameters_id""".format(
                command.parameters_table,
                ', '.join(kwargs),
                ', '.join(['%s'] * len(kwargs)))
            TRN.add(sql, vals)

            return cls(TRN.execute_fetchlast(), command)

    @classmethod
    def iter(cls, command):
        """Iterates over all parameter set of the given command

        Returns
        -------
        generator
            Yields a parameter instance
        """
        with TRN:
            sql = """SELECT parameters_id
                     FROM qiita.{0}
                     ORDER BY parameters_id""".format(
                command.parameters_table)
            TRN.add(sql)
            for result in TRN.execute_fetchflatten():
                yield cls(result, command)

    @property
    def name(self):
        """The name of the parameter set

        Returns
        -------
        str
            The name of the parameter set
        """
        with TRN:
            sql = """SELECT param_set_name
                     FROM qiita.{0}
                     WHERE parameters_id = %s""".format(self._table)
            TRN.add(sql, [self.id])
            return TRN.execute_fetchlast()

    @property
    def values(self):
        """The values of the parameter set

        Returns
        -------
        dict
            Dictionary with the parameters values keyed by parameter name
        """
        with TRN:
            sql = "SELECT * FROM qiita.{0} WHERE parameters_id = %s".format(
                self._table)
            TRN.add(sql, [self.id])
            # There should be only one row
            result = dict(TRN.execute_fetchindex()[0])
            del result["parameters_id"]
            del result["param_set_name"]
            return result

    def to_str(self):
        """Generates a string with the parameter values

        Returns
        -------
        str
            The string with all the parameters
        """
        with TRN:
            table_cols = get_table_cols_w_type(self._table)
            table_cols.remove(['parameters_id', 'bigint'])
            table_cols.remove(['param_set_name', 'varchar'])

            values = self.values

            result = []
            for p_name, p_type in sorted(table_cols):
                if p_type == 'boolean':
                    if values[p_name]:
                        result.append("--%s" % p_name)
                else:
                    result.append("--%s %s" % (p_name, values[p_name]))

            return " ".join(result)
