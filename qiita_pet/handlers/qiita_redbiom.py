# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from future.utils import viewitems
from requests import ConnectionError
from collections import defaultdict
import redbiom.summarize
import redbiom.search
import redbiom._requests
import redbiom.util
import redbiom.fetch
from tornado.gen import coroutine, Task

from qiita_core.util import execute_as_transaction
from qiita_db.util import generate_study_list_without_artifacts

from .base_handlers import BaseHandler


class RedbiomPublicSearch(BaseHandler):
    @execute_as_transaction
    def get(self, search):
        self.render('redbiom.html')

    @execute_as_transaction
    def _redbiom_search(self, query, search_on, callback):
        message = ''
        results = []

        try:
            df = redbiom.summarize.contexts()
        except ConnectionError:
            message = 'Redbiom is down - contact admin, thanks!'

        if not message:
            study_artifacts = defaultdict(list)
            contexts = df.ContextName.values
            if search_on == 'metadata':
                query = query.lower()
                try:
                    samples = redbiom.search.metadata_full(query, False)
                except TypeError:
                    message = (
                        'Not a valid search: "%s", are you sure this is a '
                        'valid metadata %s?' % (
                            query, 'value' if search_on == 'metadata' else
                            'category'))
                except ValueError:
                    message = (
                        'Not a valid search: "%s", your query is too small '
                        '(too few letters), try a longer query' % query)

                if message == '':
                    config = redbiom.get_config()
                    get = redbiom._requests.make_get(config)
                    ambs = {ctx: redbiom.util.resolve_ambiguities(
                        ctx, samples, get)[2] for ctx in contexts}
                    for ctx, amb in viewitems(ambs):
                        for i in (samples & set(amb)):
                            for rid in amb[i]:
                                aid = rid.split('_', 1)[0]
                                sid = i.split('.', 1)[0]
                                study_artifacts[sid].append(aid)
            elif search_on == 'feature':
                query = [f for f in query.split(' ')]
                for ctx in contexts:
                    for idx in redbiom.util.ids_from(query, True, 'feature',
                                                     ctx):
                        aid, sid = idx.split('_', 1)
                        sid = sid.split('.', 1)[0]
                        study_artifacts[sid].append(aid)
            elif search_on == 'taxon':
                for ctx in contexts:
                    # find the features with those taxonomies and then search
                    # those features in the samples
                    features = redbiom.fetch.taxon_descendents(ctx, query)
                    for idx in redbiom.util.ids_from(features, True, 'feature',
                                                     ctx):
                        aid, sid = idx.split('_', 1)
                        sid = sid.split('.', 1)[0]
                        study_artifacts[sid].append(aid)
            else:
                message = ('Incorrect search by: you can use metadata, '
                           'features or taxon and you passed: %s' % search_on)

            if message == '':
                keys = study_artifacts.keys()
                if keys:
                    results = generate_study_list_without_artifacts(
                        study_artifacts.keys(), True)
                    # inserting the artifact_biom_ids to the results
                    for i in range(len(results)):
                        results[i]['artifact_biom_ids'] = list(set(
                            study_artifacts[str(results[i]['study_id'])]))
                else:
                    message = "No samples where found! Try again ..."

        callback((results, message))

    @coroutine
    @execute_as_transaction
    def post(self, search):
        search = self.get_argument('search', None)
        search_on = self.get_argument('search_on', None)

        data = []
        if search is not None and search and search != ' ':
            data, msg = yield Task(self._redbiom_search, search, search_on)
        else:
            msg = 'Nothing to search for ...'

        self.write({'status': 'success', 'message': msg, 'data': data})
