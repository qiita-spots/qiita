# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from os.path import join

from .base import QiitaObject
from .exceptions import QiitaDBDuplicateError
from .util import (insert_filepaths, convert_to_id,
                   get_mountpoint)
from .sql_connection import SQLConnectionHandler, Transaction


class Reference(QiitaObject):
    r"""Object to interact with reference sequence databases

    Attributes
    ----------
    sequence_fp
    taxonomy_fp
    tree_fp

    Methods
    -------
    create
    exists

    See Also
    --------
    QiitaObject
    """
    _table = "reference"

    @classmethod
    def create(cls, name, version, seqs_fp, tax_fp=None, tree_fp=None):
        r"""Creates a new reference object with a new id on the storage system

        Parameters
        ----------
        name : str
            The name of the reference database
        version : str
            The version of the reference database
        seqs_fp : str
            The path to the reference sequence file
        tax_fp : str, optional
            The path to the reference taxonomy file
        tree_fp : str, optional
            The path to the reference tree file

        Returns
        -------
        A new instance of `cls` to access to the Reference stored in the DB

        Raises
        ------
        QiitaDBDuplicateError
            If the reference database with name `name` and version `version`
            already exists on the system
        """
        with Transaction("create_ref_%s_%s" % (name, version)) as trans:
            if cls.exists(name, version, trans=trans):
                raise QiitaDBDuplicateError(
                    "Reference", "Name: %s, Version: %s" % (name, version))

            seq_id = insert_filepaths(
                [(seqs_fp, convert_to_id("reference_seqs", "filepath_type"))],
                "%s_%s" % (name, version), "reference", "filepath",
                trans)[0]

            # Check if the database has taxonomy file
            tax_id = None
            if tax_fp:
                fps = [(tax_fp,
                        convert_to_id("reference_tax", "filepath_type"))]
                tax_id = insert_filepaths(fps, "%s_%s" % (name, version),
                                          "reference", "filepath", trans)[0]

            # Check if the database has tree file
            tree_id = None
            if tree_fp:
                fps = [(tree_fp,
                        convert_to_id("reference_tree", "filepath_type"))]
                tree_id = insert_filepaths(fps, "%s_%s" % (name, version),
                                           "reference", "filepath",
                                           trans)[0]

            # Insert the actual object to the db
            sql = """INSERT INTO qiita.{0}
                        (reference_name, reference_version, sequence_filepath,
                            taxonomy_filepath, tree_filepath)
                     VALUES (%s, %s, %s, %s, %s)
                     RETURNING reference_id""".format(cls._table)
            trans.add(sql, [name, version, seq_id, tax_id, tree_id])
            ref_id = trans.execute()[-1][0][0]

            return cls(ref_id, trans=trans)

    @classmethod
    def exists(cls, name, version, trans=None):
        r"""Checks if a given object info is already present on the DB

        Parameters
        ----------
        name : str
            The name of the reference database
        version : str
            The version of the reference database
        trans: Transaction, optional
            Transaction in which this method should be executed

        Raises
        ------
        QiitaDBNotImplementedError
            If the method is not overwritten by a subclass
        """
        trans = trans if trans is not None else Transaction(
            "exists_ref_%s_%s" % (name, version))

        with trans:
            sql = """SELECT EXISTS(
                        SELECT * FROM qiita.{0}
                        WHERE reference_name=%s
                            AND reference_version=%s)""".format(cls._table)
            trans.add(sql, [name, version])
            return trans.execute()[-1][0][0]

    def name(self, trans=None):
        """Return the name of the reference

        Parameters
        ----------
        trans: Transaction
            Transaction in which this method should be executed
        """
        trans = trans if trans is not None else Transaction("ref_name_%s"
                                                            % self._id)
        with trans:
            sql = """SELECT reference_name FROM qiita.{0}
                     WHERE reference_id = %s""".format(self._table)
            trans.add(sql, [self._id])
            return trans.execute()[-1][0][0]

    def version(self, trans=None):
        """Return the name of the reference

        Parameters
        ----------
        trans: Transaction
            Transaction in which this method should be executed
        """
        trans = trans if trans is not None else Transaction("ref_name_%s"
                                                            % self._id)
        with trans:
            sql = """SELECT reference_version FROM qiita.{0}
                     WHERE reference_id = %s""".format(self._table)
            trans.add(sql, [self._id])
            return trans.execute()[-1][0][0]

    def sequence_fp(self, trans=None):
        """Return the name of the reference

        Parameters
        ----------
        trans: Transaction
            Transaction in which this method should be executed
        """
        trans = trans if trans is not None else Transaction("ref_name_%s"
                                                            % self._id)
        with trans:
            sql = """SELECT f.filepath
                     FROM qiita.filepath f
                     JOIN qiita.{0} r ON r.sequence_filepath=f.filepath_id
                     WHERE r.reference_id=%s""".format(self._table)
            trans.add(sql, [self._id])
            rel_path = trans.execute()[-1][0][0]
            _, basefp = get_mountpoint('reference', trans=trans)[0]
            return join(basefp, rel_path)

    def taxonomy_fp(self, trans=None):
        """Return the name of the reference

        Parameters
        ----------
        trans: Transaction
            Transaction in which this method should be executed
        """
        trans = trans if trans is not None else Transaction("ref_name_%s"
                                                            % self._id)
        with trans:
            sql = """SELECT f.filepath
                     FROM qiita.filepath f
                     JOIN qiita.{0} r ON r.taxonomy_filepath=f.filepath_id
                     WHERE r.reference_id=%s""".format(self._table)
            trans.add(sql, [self._id])
            rel_path = trans.execute()[-1][0][0]
            _, basefp = get_mountpoint('reference', trans=trans)[0]
            return join(basefp, rel_path)

    def tree_fp(self, trans=None):
        """Return the name of the reference

        Parameters
        ----------
        trans: Transaction
            Transaction in which this method should be executed
        """
        trans = trans if trans is not None else Transaction("ref_name_%s"
                                                            % self._id)
        with trans:
            sql = """SELECT f.filepath
                     FROM qiita.filepath f
                     JOIN qiita.{0} r ON r.tree_filepath=f.filepath_id
                     WHERE r.reference_id=%s""".format(self._table)
            trans.add(sql, [self._id])
            rel_path = trans.execute()[-1][0][0]
            _, basefp = get_mountpoint('reference', trans=trans)[0]
            return join(basefp, rel_path)
