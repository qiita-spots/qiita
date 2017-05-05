from tornado.gen import coroutine, Task

from qiita_core.util import execute_as_transaction

from .base_handlers import BaseHandler
import redbiom.summarize
import redbiom.search
import redbiom._requests
import redbiom.util
import redbiom.fetch


class RedbiomPublicSearch(BaseHandler):
    @execute_as_transaction
    def _get_context(self, callback):
        df = redbiom.summarize.contexts()
        result = df.ContextName.values
        callback(result)

    @coroutine
    @execute_as_transaction
    def get(self, search):
        contexts = yield Task(self._get_context)
        self.render('redbiom.html', contexts=contexts)

    @execute_as_transaction
    def _redbiom_search(self, context, query, search_on, callback):
        if search_on == 'metadata':
            samples = redbiom.search.metadata_full(query, categories=None)
        else:
            redbiom._requests.valid(context)
            # from_or_nargs first parameter is the file handler so it uses that
            # as the query input. None basically will force to take the values
            # from query
            it = redbiom.util.from_or_nargs(None, query)
            samples = redbiom.util.samples_from_observations(
                it, False, context)

        if not samples:
            callback(('', 'No samples where found! Try again ...'))

        df, _ = redbiom.fetch.sample_metadata(
            samples, common=True, context=context, restrict_to=None)

        callback((df.to_html(), ''))

    @coroutine
    @execute_as_transaction
    def post(self, search):
        context = self.get_argument('context', None)
        search = self.get_argument('search', None)
        search_on = self.get_argument('search_on', None)

        data = None
        if search is not None and search and search != ' ':
            if search_on in ('observations', 'metadata'):
                data, msg = yield Task(
                    self._redbiom_search, context, search, search_on)
            else:
                msg = 'Not a valid option for search_on'
        else:
            msg = 'Nothing to search for ...'

        print '-->', msg, type(data)

        self.write({'status': 'success', 'message': msg, 'data': data})
