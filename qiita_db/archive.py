# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
import qiita_db as qdb


class Archive(qdb.base.QiitaObject):
    r"""Extra information for any features stored in a BIOM Artifact

    Methods
    -------
    insert_from_artifact
    get_merging_scheme_from_job
    retrieve_feature_values
    insert_features

    See Also
    --------
    qiita_db.QiitaObject
    """

    @classmethod
    def merging_schemes(cls):
        r"""Returns the available merging schemes

        Returns
        -------
        Iterator
            Iterator over the sample ids

        See Also
        --------
        keys
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT archive_merging_scheme_id, archive_merging_scheme
                     FROM qiita.archive_merging_scheme"""
            qdb.sql_connection.TRN.add(sql)
            return dict(qdb.sql_connection.TRN.execute_fetchindex())

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
                "SELECT archive_upsert(%s, %s, %s)", vals, many=True
            )
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
            if atype != "BIOM":
                raise ValueError("To archive artifact must be BIOM but %s" % atype)

            bfps = [x["fp"] for x in artifact.filepaths if x["fp_type"] == "biom"]
            if not bfps:
                raise ValueError("The artifact has no biom files")

            # [0] as it returns a list
            ms = qdb.util.get_artifacts_information([artifact.id])[0]["algorithm"]

            cls._inserting_main_steps(ms, features)

    @classmethod
    def get_merging_scheme_from_job(cls, job):
        r"""Inserts new features to the database based on a given job

        Parameters
        ----------
        job : qiita_db.processing_job.ProcessingJob
            The Qiita process job_id generating the artifact holding the
            features to be retrieved or stored.

        Raises
        ------
            ValueError
                If the Artifact type is not BIOM
                If the artifact doesn't have a biom filepath
        """
        with qdb.sql_connection.TRN:
            acmd = job.command
            parent = job.input_artifacts[0]
            parent_pparameters = parent.processing_parameters
            phms = None
            if parent_pparameters is None:
                parent_cmd_name = None
                parent_parameters = None
                parent_merging_scheme = None
            else:
                pcmd = parent_pparameters.command
                parent_cmd_name = pcmd.name
                parent_parameters = parent_pparameters.values
                parent_merging_scheme = pcmd.merging_scheme
                if not parent_merging_scheme["ignore_parent_command"]:
                    gp = parent.parents[0]
                    gp_params = gp.processing_parameters
                    if gp_params is not None:
                        gp_cmd = gp_params.command
                        phms = qdb.util.human_merging_scheme(
                            parent_cmd_name,
                            parent_merging_scheme,
                            gp_cmd.name,
                            gp_cmd.merging_scheme,
                            parent_parameters,
                            [],
                            gp_params.values,
                        )

            hms = qdb.util.human_merging_scheme(
                acmd.name,
                acmd.merging_scheme,
                parent_cmd_name,
                parent_merging_scheme,
                job.parameters.values,
                [],
                parent_parameters,
            )

            if phms is not None:
                hms = qdb.util.merge_overlapping_strings(hms, phms)

            return hms

    @classmethod
    def retrieve_feature_values(cls, archive_merging_scheme=None, features=None):
        r"""Retrieves all features/values from the archive

        Parameters
        ----------
        archive_merging_scheme : optional, str
            The name of the archive_merging_scheme to retrieve
        features : list of str, optional
            List of features to retrieve information from the archive

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
                # depending on the method calling test retrieve_feature_values
                # the features elements can be string or bytes; making sure
                # everything is string for SQL
                vals.append(
                    tuple(
                        [
                            f.decode("ascii") if isinstance(f, bytes) else f
                            for f in features
                        ]
                    )
                )

            sql = """SELECT archive_feature, archive_feature_value
                     FROM qiita.archive_feature_value
                     LEFT JOIN qiita.archive_merging_scheme
                        USING (archive_merging_scheme_id) {0}
                     ORDER BY archive_merging_scheme, archive_feature"""

            if extras:
                sql = sql.format("WHERE " + " AND ".join(extras))
                qdb.sql_connection.TRN.add(sql, vals)
            else:
                qdb.sql_connection.TRN.add(sql.format(""))

            return dict(qdb.sql_connection.TRN.execute_fetchindex())

    @classmethod
    def insert_features(cls, merging_scheme, features):
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
        cls._inserting_main_steps(merging_scheme, features)

        inserted = cls.retrieve_feature_values(
            archive_merging_scheme=merging_scheme, features=features.keys()
        )

        return inserted
