# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import qiita_db as qdb
from .oauth2 import OauthBaseHandler, authenticate_oauth
from .util import _get_instance


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
            ST = qdb.metadata_template.sample_template.SampleTemplate
            st = _get_instance(ST, study_id, 'Error instantiating sample info')
            response = {'data': st.to_dataframe().to_dict(orient='index')}

            self.write(response)
