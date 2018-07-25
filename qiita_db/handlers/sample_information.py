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


def _get_sample_info(sid):
    """Returns the sample information with the given `sid` if it exists

    Parameters
    ----------
    sid : str
        The sample information id

    Returns
    -------
    qiita_db.metadata_template.sample_template.SampleTemplate
        The requested sample template

    Raises
    ------
    HTTPError
        If the sample information does not exist, with error code 404
        If there is a problem instantiating, with error code 500
    """
    try:
        sid = int(sid)
        st = qdb.metadata_template.sample_template.SampleTemplate(sid)
    except qdb.exceptions.QiitaDBUnknownIDError:
        raise HTTPError(404)
    except Exception as e:
        raise HTTPError(500, reason='Error instantiating sample information '
                        '%s: %s' % (sid, str(e)))

    return st


class SampleInfoDBHandler(OauthBaseHandler):
    @authenticate_oauth
    def get(self, study_id):
        """Retrieves the sample information content

        Parameters
        ----------
        study_id: str
            The id of the study whose sample information is being retrieved

        Returns
        -------
        dict
            The contents of the sample information keyed by sample id
        """
        with qdb.sql_connection.TRN:
            st = _get_sample_info(study_id)
            response = {'data': st.to_dataframe().to_dict(orient='index')}

            self.write(response)
