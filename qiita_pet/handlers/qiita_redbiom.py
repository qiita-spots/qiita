from tornado.gen import coroutine, Task

import pandas as pd

from qiita_core.util import execute_as_transaction

from .base_handlers import BaseHandler
import redbiom.summarize


class RedbiomPublicSearch(BaseHandler):
    @execute_as_transaction
    def get(self, search):
        data = None
        if isinstance(search, pd.DataFrame):
            data = search.to_html()

        self.render('redbiom.html', data=data, msg='')


    @execute_as_transaction
    def _get_shared_for_study(self, analysis, callback):
        shared_links = get_shared_links(analysis)
        users = [u.email for u in analysis.shared_with]
        callback((users, shared_links))

    @coroutine
    @execute_as_transaction
    def post(self, search):
        search = self.get_argument('search', None)
        search_on = self.get_argument('search_on', None)

        data = None
        if search is not None and search and search != ' ':
            if search_on == 'sequences':
                # we will return a set
                data = None
                msg = 'searching on sequences'
            elif search_on == 'metadata':
                # we will return a df
                data = None
                msg = 'searching on metadata'
            else:
                msg = 'Not a valid option for search_on'
        else:
            msg = 'Nothing to search for ...'

        self.write({'status': 'success', 'message': msg, 'data': data})
        # yield Task(self._redbiom_search, search, search_on)
        # data = search.to_html()
        # if selected is not None:
        #
        # if deselected is not None:
        #     yield Task(self._unshare, analysis, deselected)
        #
        # users, links = yield Task(self._get_shared_for_study, analysis)

        # category = ''
        # exact = ''
        # value = None
        # context = ''
        # md = redbiom.summarize.category_from_observations(context, category,
        #                                                   iterable, exact)
