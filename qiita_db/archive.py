# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division

import qiita_db as qdb


class Archive(qdb.base.QiitaObject):
    r"""Extra information for any features stored in a BIOM Artifact

    Methods
    -------
    insert_from_biom

    See Also
    --------
    qiita_db.QiitaObject
    """

    @classmethod
    def insert_from_artifact(cls, artifact, features):
        r"""Inserts new features to the database based on a given artifact

        Parameters
        ----------
        artifact : qiita_db.artifact.Artifact
            The artifact from which the features were generated
        features : dict {str: str}
            A dictionary of the features and the values to be stored

        Raises
        ------
            ValueError
                If the Artifact type is not BIOM
                If the artifact doesn't have a biom filepath
        """
        with qdb.sql_connection.TRN:
            atype = artifact.artifact_type
            if atype != 'BIOM':
                raise ValueError(
                    "To archive artifact must be BIOM but %s" % atype)

            bfps = [fp for _, fp, fpt in artifact.filepaths if fpt == 'biom']
            if not bfps:
                raise ValueError("The artifact has no biom files")

            # [0] as it returns a list
            ms = qdb.util.get_artifacts_information(
                [artifact.id])[0]['algorithm']
            sql = """INSERT INTO qiita.archive_merging_scheme
                        (archive_merging_scheme)
                     SELECT %s WHERE NOT EXISTS (
                        SELECT 1 FROM qiita.archive_merging_scheme
                        WHERE archive_merging_scheme = %s)"""
            qdb.sql_connection.TRN.add(sql, [ms, ms])
            sql = """SELECT archive_merging_scheme_id
                     FROM qiita.archive_merging_scheme
                     WHERE archive_merging_scheme = %s"""
            qdb.sql_connection.TRN.add(sql, [ms])
            amsi = qdb.sql_connection.TRN.execute_fetchlast()

            vals = [[amsi, _id, val] for _id, val in features.items()]
            qdb.sql_connection.TRN.add(
                "SELECT archive_upsert(%s, %s, %s)", vals, many=True)
            qdb.sql_connection.TRN.execute()

    @classmethod
    def retrieve_feature_values(cls, archive_merging_scheme=None):
        r"""Retrieves all features/values from the archive

        Parameters
        ----------
        archive_merging_scheme : optional, str
            The name of the archive_merging_scheme to retrieve

        Notes
        -----
            If archive_merging_scheme is None it will return all
            feature values
        """
        with qdb.sql_connection.TRN:
            extra = ("" if archive_merging_scheme is None
                     else "WHERE archive_merging_scheme = '%s'" %
                     archive_merging_scheme)
            sql = """SELECT archive_merging_scheme, archive_feature,
                        archive_feature_value
                     FROM qiita.archive_feature_value
                     LEFT JOIN qiita.archive_merging_scheme
                        USING (archive_merging_scheme_id) {0}
                     ORDER BY archive_merging_scheme, archive_feature
                  """.format(extra)
            qdb.sql_connection.TRN.add(sql)
            return qdb.sql_connection.TRN.execute_fetchindex()
