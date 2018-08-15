# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from requests import ConnectionError
from future.utils import viewitems
from collections import defaultdict
import redbiom.summarize
import redbiom.search
import redbiom._requests
import redbiom.util
import redbiom.fetch
from tornado.gen import coroutine, Task

from qiita_core.util import execute_as_transaction
from qiita_db.util import generate_study_list_without_artifacts
from qiita_db.study import Study

from .base_handlers import BaseHandler


class RedbiomPublicSearch(BaseHandler):
    @execute_as_transaction
    def get(self, search):
        self.render('redbiom.html')

    def _redbiom_metadata_search(self, query, contexts):
        study_artifacts = defaultdict(list)
        message = ''
        try:
            samples = redbiom.search.metadata_full(query, False)
        except ValueError:
            message = (
                'Not a valid search: "%s", your query is too small '
                '(too few letters), try a longer query' % query)
        except Exception:
            message = (
                'The query ("%s") did not work and may be malformed. Please '
                'check the search help for more information on the queries.'
                % query)
        if not message:
            study_samples = defaultdict(list)
            for s in samples:
                study_samples[s.split('.', 1)[0]].append(s)
            for sid, samps in viewitems(study_samples):
                study_artifacts[sid] = {
                    a.id: samps for a in Study(sid).artifacts(
                        artifact_type='BIOM')}

        return message, study_artifacts

    def _redbiom_feature_search(self, query, contexts):
        study_artifacts = defaultdict(lambda: defaultdict(list))
        query = [f for f in query.split(' ')]
        for ctx in contexts:
            for idx in redbiom.util.ids_from(query, True, 'feature', ctx):
                aid, sample_id = idx.split('_', 1)
                sid = sample_id.split('.', 1)[0]
                study_artifacts[sid][aid].append(sample_id)

        return '', study_artifacts

    def _redbiom_taxon_search(self, query, contexts):
        study_artifacts = defaultdict(lambda: defaultdict(list))
        for ctx in contexts:
            # find the features with those taxonomies and then search
            # those features in the samples
            features = redbiom.fetch.taxon_descendents(ctx, query)
            for idx in redbiom.util.ids_from(features, True, 'feature',
                                             ctx):
                aid, sample_id = idx.split('_', 1)
                sid = sample_id.split('.', 1)[0]
                study_artifacts[sid][aid].append(sample_id)

        return '', study_artifacts

    @execute_as_transaction
    def _redbiom_search(self, query, search_on, callback):
        search_f = {'metadata': self._redbiom_metadata_search,
                    'feature': self._redbiom_feature_search,
                    'taxon': self._redbiom_taxon_search}

        message = ''
        results = []

        try:
            df = redbiom.summarize.contexts()
        except ConnectionError:
            message = 'Redbiom is down - contact admin, thanks!'
        else:
            contexts = df.ContextName.values
            if search_on in search_f:
                message, study_artifacts = search_f[search_on](query, contexts)
                if not message:
                    studies = study_artifacts.keys()
                    if studies:
                        results = generate_study_list_without_artifacts(
                            studies)
                        # inserting the artifact_biom_ids to the results
                        for i in range(len(results)):
                            results[i]['artifact_biom_ids'] = study_artifacts[
                                str(results[i]['study_id'])]
                    else:
                        message = "No samples were found! Try again ..."
            else:
                message = ('Incorrect search by: you can use metadata, '
                           'features or taxon and you passed: %s' % search_on)

        callback((results, message))

    @coroutine
    @execute_as_transaction
    def post(self, search):
        search = self.get_argument('search')
        search_on = self.get_argument('search_on')

        data, msg = yield Task(self._redbiom_search, search, search_on)

        self.write({'status': 'success', 'message': msg, 'data': data})
