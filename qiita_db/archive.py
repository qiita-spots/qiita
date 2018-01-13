# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division

import qiita_db as qdb


class Archive(object):
    r"""Extra information for any features stored in a BIOM Artifact

    Methods
    -------
    insert_from_biom
    insert_from_artifact
    insert_features

    See Also
    --------
    qiita_db.QiitaObject
    """

    @classmethod
    def _inserting_main_steps(cls, ms, features):
        with qdb.sql_connection.TRN:
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

            cls._inserting_main_steps(ms, features)

    @classmethod
    def get_merging_scheme_from_job(cls, job):
        r"""Inserts new features to the database based on a given job

        Parameters
        ----------
        job : qiita_db.artifact.Artifact
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
            acmd = job.command
            ms = acmd.merging_scheme

            # 1. cleaning aparams - the parameters of the main artifact/job
            temp = acmd.optional_parameters.copy()
            temp.update(acmd.required_parameters)
            # list: cause it can be tuple or lists
            # [0]: the first value is the parameter type
            tparams = job.parameters.values
            aparams = ','.join(
                ['%s: %s' % (k, tparams[k]) for k, v in temp.items()
                 if list(v)[0] != 'artifact' and k in ms['parameters']])
            # in theory we could check here for the filepath merging but
            # as the files haven't been creted we don't have this info.
            # Additionally, based on the current funtionality, this is not
            # important as normally the difference between files is just
            # an additional filtering step
            if aparams:
                cname = "%s (%s)" % (acmd.name, aparams)
            else:
                cname = acmd.name

            # 2. cleaning pparams - the parameters of the parent artifact
            # [0] getting the atributes from the first parent
            ppp = job.input_artifacts[0].processing_parameters
            pcmd = None if ppp is None else ppp.command
            palgorithm = 'N/A'
            if pcmd is not None:
                pms = pcmd.merging_scheme
                palgorithm = pcmd.name
                if pms['parameters']:
                    ppms = pms['parameters']
                    op = pcmd.optional_parameters.copy()
                    op.update(pcmd.required_parameters)
                    pparams = ','.join(
                        ['%s: %s' % (k, ppms[k]) for k, v in op.items()
                         if list(v)[0] != 'artifact' and k in ppms])
                    params = ','.join(
                        ['%s: %s' % (k, pparams[k]) for k in ppms])
                    palgorithm = "%s (%s)" % (palgorithm, params)
            algorithm = '%s | %s' % (cname, palgorithm)

            return algorithm

    @classmethod
    def retrieve_feature_values(cls, archive_merging_scheme=None,
                                features=None):
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
            extras = []
            vals = []
            if archive_merging_scheme is not None:
                extras.append("""archive_merging_scheme = %s""")
                vals.append(archive_merging_scheme)
            if features is not None:
                extras.append("""archive_feature IN %s""")
                vals.append(tuple(features))

            sql = """SELECT archive_feature, archive_feature_value
                     FROM qiita.archive_feature_value
                     LEFT JOIN qiita.archive_merging_scheme
                        USING (archive_merging_scheme_id) {0}
                     ORDER BY archive_merging_scheme, archive_feature"""

            if extras:
                sql = sql.format('WHERE ' + ' AND '.join(extras))
                qdb.sql_connection.TRN.add(sql, vals)
            else:
                qdb.sql_connection.TRN.add(sql.format(''))

            return {k: v for k, v in
                    qdb.sql_connection.TRN.execute_fetchindex()}

    def insert_features(self, merging_scheme, features):
        r"""Inserts new features to the database based on a given artifact

        Parameters
        ----------
        merging_scheme : str
            The merging scheme to store these features
        features : dict {str: str}
            A dictionary of the features and the values to be stored

        Returns
        -------
        dict, feature: value
            The inserted new values
        """
        self._inserting_main_steps(merging_scheme, features)

        inserted = self.retrieve_feature_values(
            archive_merging_scheme=merging_scheme, features=features.keys())

        return inserted
