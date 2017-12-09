# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from .oauth2 import OauthBaseHandler, authenticate_oauth


class APIArchiveObservations(OauthBaseHandler):
    @authenticate_oauth
    def post(self):
        """Retrieves the archiving information

        Returns
        -------
        dict
            The contents of the analysis keyed by sample id
        """
        # job_id = self.get_argument('job_id')
        features = self.request.arguments['features']

        # TODO: search on artifact
        response = {v: [] for v in features}

        self.write(response)
