# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from .oauth2 import OauthBaseHandler, authenticate_oauth
from qiita_db.processing_job import ProcessingJob
from qiita_db.archive import Archive
from json import loads


class APIArchiveObservations(OauthBaseHandler):
    @authenticate_oauth
    def post(self):
        """Retrieves the archiving information

        Returns
        -------
        dict
            The contents of the analysis keyed by sample id

        Notes
        -----
            Argument "path" must be the Qiita job_id which is used to infer
            the merging scheme.
            Argument "features" is a list of feature identifier,
            e.g. Deblur sequences.

            Feature identifiers not found in the archive won't be included in
            the return dictionary.
        """
        job_id = self.get_argument('job_id')
        features = self.request.arguments['features']

        ms = Archive.get_merging_scheme_from_job(ProcessingJob(job_id))
        response = Archive.retrieve_feature_values(
            archive_merging_scheme=ms, features=features)

        self.write(response)

    @authenticate_oauth
    def patch(self):
        """Updates / stores feature information in the archive.

        Notes
        -----
            Argument "path" must be the Qiita job_id which is used to infer
            the merging scheme.
            Argument "value" is a json string, i.e. result of a json.dump(obj)
            of a dictionary, keyed with feature identifiers.
        """
        req_path = self.get_argument('path')
        req_value = self.get_argument('value')

        ms = Archive.get_merging_scheme_from_job(ProcessingJob(req_path))

        archive = Archive()
        self.write(archive.insert_features(ms, loads(req_value)))
