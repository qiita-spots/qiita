# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import HTTPError

import qiita_db as qdb
from .oauth2 import OauthBaseHandler, authenticate_oauth


def _get_analysis(a_id):
    """Returns the analysis with the given `a_id` if it exists

    Parameters
    ----------
    a_id : str
        The analysis id

    Returns
    -------
    qiita_db.analysis.Analysis
        The requested analysis

    Raises
    ------
    HTTPError
        If the analysis does not exist, with error code 404
        If there is a problem instantiating the analysis, with error code 500
    """
    try:
        a_id = int(a_id)
        a = qdb.analysis.Analysis(a_id)
    except qdb.exceptions.QiitaDBUnknownIDError:
        raise HTTPError(404)
    except Exception as e:
        raise HTTPError(500, 'Error instantiating analysis %s: %s'
                        % (a_id, str(e)))
    return a


class APIAnalysisMetadataHandler(OauthBaseHandler):
    @authenticate_oauth
    def get(self, analysis_id):
        """Retrieves the analysis metadata

        Parameters
        ----------
        analysis_id : str
            The id of the analysis whose information is being retrieved

        Returns
        -------
        dict
            The contents of the analysis keyed by sample id
        """
        with qdb.sql_connection.TRN:
            a = _get_analysis(analysis_id)
            mf_fp = a.mapping_file
            response = None
            if mf_fp is not None:
                df = qdb.metadata_template.util.load_template_to_dataframe(
                    mf_fp, index='#SampleID')
                response = df.to_dict(orient='index')

        self.write(response)
