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
        df = redbiom.summarize.contexts()
        contexts = df.ContextName.values
        if context not in contexts:
            callback(([], 'The given context is not valid: %s - %s' % (
                context, contexts)))
        else:
            if search_on == 'metadata':
                samples = redbiom.search.metadata_full(query, categories=None)
            elif search_on == 'observations':
                # from_or_nargs first parameter is the file handler so it uses
                # that as the query input. None basically will force to take
                # the values from query
                samples = [s.split('_', 1)[1]
                           for s in redbiom.util.samples_from_observations(
                               query.split(' '), True, context)]
            else:
                callback(([], 'Incorrect search by: you can use observations '
                          'or metadata and you passed: %s' % search_on))

            if bool(samples):
                import qiita_db.sql_connection as qdbsc
                with qdbsc.TRN:
                    sql = """
                    SELECT DISTINCT study_title, study_id,
                        artifact_id, a.name AS aname, sc.name as command,
                        s.name as software, version,
                        array_agg(DISTINCT sample_id) AS samples
                    FROM qiita.study_sample
                    LEFT JOIN qiita.study USING (study_id)
                    LEFT JOIN qiita.study_artifact USING (study_id)
                    LEFT JOIN qiita.artifact a USING (artifact_id)
                    RIGHT JOIN qiita.artifact_type ON
                        a.artifact_type_id=qiita.artifact_type.artifact_type_id
                        AND artifact_type = 'BIOM'
                    LEFT JOIN qiita.software_command sc USING (command_id)
                    LEFT JOIN qiita.software s USING (software_id)
                    WHERE sample_id IN %s
                    GROUP BY study_title, study_id, artifact_id, aname,
                    command, software, version"""
                    qdbsc.TRN.add(sql, [tuple(samples)])
                    callback(([dict(row)
                               for row in qdbsc.TRN.execute_fetchindex()], ''))
            else:
                callback(([], 'No samples where found! Try again ...'))

    @coroutine
    @execute_as_transaction
    def post(self, search):
        context = self.get_argument('context', None)
        search = self.get_argument('search', None)
        search_on = self.get_argument('search_on', None)

        data = []
        if search is not None and search and search != ' ':
            if search_on in ('observations', 'metadata'):
                data, msg = yield Task(
                    self._redbiom_search, context, search, search_on)
            else:
                msg = 'Not a valid option for search_on'
        else:
            msg = 'Nothing to search for ...'

        self.write({'status': 'success', 'message': msg, 'data': data})
