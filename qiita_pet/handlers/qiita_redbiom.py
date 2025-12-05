# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from collections import defaultdict

import redbiom._requests
import redbiom.admin
import redbiom.fetch
import redbiom.search
import redbiom.summarize
import redbiom.util
from requests import ConnectionError
from requests.exceptions import HTTPError as rHTTPError
from tornado.gen import Task, coroutine
from tornado.web import HTTPError

from qiita_core.util import execute_as_transaction
from qiita_db.util import generate_study_list_without_artifacts

from .base_handlers import BaseHandler


class RedbiomPublicSearch(BaseHandler):
    @execute_as_transaction
    def get(self, search):
        # making sure that if someone from a portal forces entry to this URI
        # we go to the main portal
        try:
            timestamps = redbiom.admin.get_timestamps()
        except rHTTPError:
            timestamps = []

        if timestamps:
            latest_release = timestamps[0]
        else:
            latest_release = "Not reported"
        if self.request.uri != "/redbiom/":
            self.redirect("/redbiom/")
        self.render("redbiom.html", latest_release=latest_release)

    def _redbiom_metadata_search(self, query, contexts):
        study_artifacts = defaultdict(lambda: defaultdict(list))
        message = ""
        try:
            redbiom_samples = redbiom.search.metadata_full(query, False)
        except ValueError:
            message = (
                'Not a valid search: "%s", your query is too small '
                "(too few letters), try a longer query" % query
            )
        except Exception:
            message = (
                'The query ("%s") did not work and may be malformed. Please '
                "check the search help for more information on the queries." % query
            )
        if not message and redbiom_samples:
            study_artifacts = defaultdict(lambda: defaultdict(list))
            for ctx in contexts:
                # redbiom.fetch.data_from_samples returns a biom, which we
                # will ignore, and a dict: {sample_id_in_table: original_id}
                try:
                    # if redbiom can't find a valid sample in the context it
                    # will raise a ValueError: max() arg is an empty sequence
                    _, data = redbiom.fetch.data_from_samples(ctx, redbiom_samples)
                except ValueError:
                    continue
                for idx in data.keys():
                    sample_id, aid = idx.rsplit(".", 1)
                    sid = sample_id.split(".", 1)[0]
                    study_artifacts[sid][aid].append(sample_id)

        return message, study_artifacts

    def _redbiom_feature_search(self, query, contexts):
        study_artifacts = defaultdict(lambda: defaultdict(list))
        query = [f for f in query.split(" ")]
        for ctx in contexts:
            for idx in redbiom.util.ids_from(query, False, "feature", ctx):
                aid, sample_id = idx.split("_", 1)
                sid = sample_id.split(".", 1)[0]
                study_artifacts[sid][aid].append(sample_id)

        return "", study_artifacts

    def _redbiom_taxon_search(self, query, contexts):
        study_artifacts = defaultdict(lambda: defaultdict(list))
        for ctx in contexts:
            # find the features with those taxonomies and then search
            # those features in the samples
            features = redbiom.fetch.taxon_descendents(ctx, query)
            # from empirical evidence we saw that when we return more than 600
            # features we'll reach issue #2312 so avoiding saturating the
            # workers and raise this error quickly
            if len(features) > 600:
                raise HTTPError(504)
            for idx in redbiom.util.ids_from(features, False, "feature", ctx):
                aid, sample_id = idx.split("_", 1)
                sid = sample_id.split(".", 1)[0]
                study_artifacts[sid][aid].append(sample_id)

        return "", study_artifacts

    @execute_as_transaction
    def _redbiom_search(self, query, search_on, callback):
        search_f = {
            "metadata": self._redbiom_metadata_search,
            "feature": self._redbiom_feature_search,
            "taxon": self._redbiom_taxon_search,
        }

        message = ""
        results = []

        try:
            df = redbiom.summarize.contexts()
        except ConnectionError:
            message = "Redbiom is down - contact admin, thanks!"
        else:
            contexts = df.ContextName.values
            if search_on in search_f:
                message, study_artifacts = search_f[search_on](query, contexts)
                if not message:
                    studies = study_artifacts.keys()
                    if studies:
                        results = generate_study_list_without_artifacts(studies)
                        # inserting the artifact_biom_ids to the results
                        for i in range(len(results)):
                            results[i]["artifact_biom_ids"] = study_artifacts[
                                str(results[i]["study_id"])
                            ]
                    else:
                        message = "No samples were found! Try again ..."
            else:
                message = (
                    "Incorrect search by: you can use metadata, "
                    "features or taxon and you passed: %s" % search_on
                )

        callback((results, message))

    @coroutine
    @execute_as_transaction
    def post(self, search):
        search = self.get_argument("search")
        search_on = self.get_argument("search_on")

        data, msg = yield Task(self._redbiom_search, search, search_on)

        self.write({"status": "success", "message": msg, "data": data})
