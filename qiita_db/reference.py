# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from os.path import join

import qiita_db as qdb


class Reference(qdb.base.QiitaObject):
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
        with qdb.sql_connection.TRN:
            if cls.exists(name, version):
                raise qdb.exceptions.QiitaDBDuplicateError(
                    "Reference", "Name: %s, Version: %s" % (name, version))

            fps = [(seqs_fp,
                    qdb.util.convert_to_id("reference_seqs", "filepath_type"))]
            seq_id = qdb.util.insert_filepaths(
                fps, "%s_%s" % (name, version), "reference", "filepath")[0]

            # Check if the database has taxonomy file
            tax_id = None
            if tax_fp:
                fps = [
                    (tax_fp,
                     qdb.util.convert_to_id("reference_tax", "filepath_type"))]
                tax_id = qdb.util.insert_filepaths(
                    fps, "%s_%s" % (name, version), "reference", "filepath")[0]

            # Check if the database has tree file
            tree_id = None
            if tree_fp:
                fps = [
                    (tree_fp,
                     qdb.util.convert_to_id("reference_tree", "filepath_type"))
                    ]
                tree_id = qdb.util.insert_filepaths(
                    fps, "%s_%s" % (name, version), "reference", "filepath")[0]

            # Insert the actual object to the db
            sql = """INSERT INTO qiita.{0}
                        (reference_name, reference_version, sequence_filepath,
                         taxonomy_filepath, tree_filepath)
                     VALUES (%s, %s, %s, %s, %s)
                     RETURNING reference_id""".format(cls._table)
            qdb.sql_connection.TRN.add(
                sql, [name, version, seq_id, tax_id, tree_id])
            id_ = qdb.sql_connection.TRN.execute_fetchlast()

            return cls(id_)

    @classmethod
    def exists(cls, name, version):
        r"""Checks if a given object info is already present on the DB

        Parameters
        ----------
        name : str
            The name of the reference database
        version : str
            The version of the reference database

        Raises
        ------
        QiitaDBNotImplementedError
            If the method is not overwritten by a subclass
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(
                        SELECT * FROM qiita.{0}
                        WHERE reference_name=%s
                            AND reference_version=%s)""".format(cls._table)
            qdb.sql_connection.TRN.add(sql, [name, version])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def name(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT reference_name FROM qiita.{0}
                     WHERE reference_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def version(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT reference_version FROM qiita.{0}
                     WHERE reference_id = %s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def sequence_fp(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT f.filepath
                     FROM qiita.filepath f
                        JOIN qiita.{0} r ON r.sequence_filepath=f.filepath_id
                     WHERE r.reference_id=%s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            rel_path = qdb.sql_connection.TRN.execute_fetchlast()
            _, basefp = qdb.util.get_mountpoint('reference')[0]
            return join(basefp, rel_path)

    @property
    def taxonomy_fp(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT f.filepath
                     FROM qiita.filepath f
                        JOIN qiita.{0} r ON r.taxonomy_filepath=f.filepath_id
                     WHERE r.reference_id=%s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            rel_path = qdb.sql_connection.TRN.execute_fetchlast()
            _, basefp = qdb.util.get_mountpoint('reference')[0]
            return join(basefp, rel_path)

    @property
    def tree_fp(self):
        with qdb.sql_connection.TRN:
            sql = """SELECT f.filepath
                     FROM qiita.filepath f
                        JOIN qiita.{0} r ON r.tree_filepath=f.filepath_id
                     WHERE r.reference_id=%s""".format(self._table)
            qdb.sql_connection.TRN.add(sql, [self._id])
            try:
                rel_path = qdb.sql_connection.TRN.execute_fetchlast()
            except IndexError:
                # the tree doesn't exist
                rel_path = ''
            _, basefp = qdb.util.get_mountpoint('reference')[0]
            return join(basefp, rel_path)
