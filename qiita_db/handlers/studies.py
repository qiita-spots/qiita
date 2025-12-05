# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import HTTPError

from qiita_db.sql_connection import TRN

from .oauth2 import OauthBaseHandler, authenticate_oauth


def _generate_study_list_for_api(visibility, only_biom=True):
    """Get general study information

    Parameters
    ----------
    visibility : string
        The visibility to get studies

    Returns
    -------
    list of dict
        The list of studies and their information
    """
    artifact_type = ""
    if only_biom:
        artifact_type = "AND artifact_type = 'BIOM'"

    sql = f"""
        SELECT study_id, array_agg(DISTINCT artifact_id) FROM qiita.study
            INNER JOIN qiita.study_artifact USING (study_id)
            INNER JOIN qiita.artifact USING (artifact_id)
            INNER JOIN qiita.artifact_type USING (artifact_type_id)
            INNER JOIN qiita.visibility USING (visibility_id)
        WHERE visibility = %s
        {artifact_type}
        GROUP BY study_id
    """
    with TRN:
        TRN.add(sql, [visibility])
        return dict(TRN.execute_fetchindex())


class APIStudiesListing(OauthBaseHandler):
    @authenticate_oauth
    def get(self, visibility):
        """Retrieves the studies and their BIOM artifacts in visibility

        Parameters
        ----------
        visibility : str {'public', 'sandbox'}
            The visibility of the studies and artifacts requested

        Returns
        -------
        see qiita_db.util.generate_study_list
        """
        if visibility not in {"public", "private"}:
            raise HTTPError(
                403, reason="You can only request public or private studies"
            )

        response = {"data": _generate_study_list_for_api(visibility=visibility)}
        self.write(response)
