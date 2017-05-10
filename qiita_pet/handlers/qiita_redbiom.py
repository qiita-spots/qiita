from tornado.gen import coroutine, Task

from qiita_core.util import execute_as_transaction

from .base_handlers import BaseHandler
from request import ConnectionError
import redbiom.summarize
import redbiom.search
import redbiom._requests
import redbiom.util
import redbiom.fetch


class RedbiomPublicSearch(BaseHandler):
    @execute_as_transaction
    def get(self, search):
        self.render('redbiom.html')

    @execute_as_transaction
    def _redbiom_search(self, query, search_on, callback):
        try:
            df = redbiom.summarize.contexts()
            contexts = df.ContextName.values
        except ConnectionError:
            callback(([], 'Redbiom is down - contact admin, thanks!' % query))

        query = query.lower()
        samples, categories = [], []

        if search_on == 'metadata':
            try:
                samples = redbiom.search.metadata_full(query, categories=False)
            except TypeError:
                callback(([], 'Not a valid search: "%s", are you sure this is '
                              'a valid metadata value?' % query))
        elif search_on == 'categories':
            try:
                categories = redbiom.search.metadata_full(query,
                                                          categories=True)
            except ValueError:
                callback(([], 'Not a valid search: "%s", try a longer query'
                         % query))
            except TypeError:
                callback(([], 'Not a valid search: "%s", are you sure this is '
                              'a valid metadata category?' % query))
        elif search_on == 'observations':
            samples = [s.split('_', 1)[1] for context in contexts
                       for s in redbiom.util.samples_from_observations(
                           query.split(' '), True, context)]
        else:
            callback(([], 'Incorrect search by: you can use observations '
                      'or metadata and you passed: %s' % search_on))

        import qiita_db as qdb
        import qiita_db.sql_connection as qdbsc
        if samples:
            sql = """
            WITH main_query AS (
                SELECT study_title, study_id, artifact_id,
                    array_agg(DISTINCT sample_id) AS samples,
                    qiita.artifact_descendants(artifact_id) AS children
                FROM qiita.study_prep_template
                JOIN qiita.prep_template USING (prep_template_id)
                JOIN qiita.prep_template_sample USING (prep_template_id)
                JOIN qiita.study USING (study_id)
                WHERE sample_id IN %s
                GROUP BY study_title, study_id, artifact_id)
            SELECT study_title, study_id, samples, name, command_id,
                (main_query.children).artifact_id AS artifact_id
            FROM main_query
            JOIN qiita.artifact a ON (main_query.children).artifact_id =
                a.artifact_id
            JOIN qiita.artifact_type at ON (
                at.artifact_type_id = a.artifact_type_id
                AND artifact_type = 'BIOM')
            ORDER BY artifact_id
            """
            with qdbsc.TRN:
                qdbsc.TRN.add(sql, [tuple(samples)])
                results = []
                commands = {}
                for row in qdbsc.TRN.execute_fetchindex():
                    title, sid, samples, name, cid, aid = row
                    nr = {'study_title': title, 'study_id': sid,
                          'artifact_id': aid, 'aname': name,
                          'samples': samples}
                    if cid is not None:
                        if cid not in commands:
                            c = qdb.software.Command(cid)
                            commands[cid] = {
                                'sfwn': c.software.name,
                                'sfv': c.software.version,
                                'cmdn': c.name
                            }
                        nr['command'] = commands[cid]['cmdn']
                        nr['software'] = commands[cid]['sfwn']
                        nr['version'] = commands[cid]['sfv']
                    else:
                        nr['command'] = None
                        nr['software'] = None
                        nr['version'] = None
                    results.append(nr)
                callback((results, ''))
        elif categories:
            sql = """
                WITH get_studies AS (
                    SELECT trim(table_name, 'sample_')::int AS study_id,
                        array_agg(column_name::text) AS columns
                    FROM information_schema.columns
                    WHERE column_name IN %s
                        AND table_name LIKE 'sample_%%'
                        AND table_name NOT IN (
                            'prep_template', 'prep_template_sample')
                    GROUP BY table_name)
                SELECT study_title, get_studies.study_id, columns
                -- artifact_id, samples
                FROM get_studies
                JOIN qiita.study ON get_studies.study_id =
                    qiita.study.study_id"""
            with qdbsc.TRN:
                results = []
                qdbsc.TRN.add(sql, [tuple(categories)])
                for title, sid, cols in qdbsc.TRN.execute_fetchindex():
                    nr = {'study_title': title, 'study_id': sid,
                          'artifact_id': None, 'aname': None,
                          'samples': cols, 'command': ', '.join(cols),
                          'software': None, 'version': None}
                    results.append(nr)
                callback((results, ''))
        else:
            callback(([], 'No samples where found! Try again ...'))

    @coroutine
    @execute_as_transaction
    def post(self, search):
        search = self.get_argument('search', None)
        search_on = self.get_argument('search_on', None)

        data = []
        if search is not None and search and search != ' ':
            if search_on in ('observations', 'metadata', 'categories'):
                data, msg = yield Task(
                    self._redbiom_search, search, search_on)
            else:
                msg = 'Not a valid option for search_on'
        else:
            msg = 'Nothing to search for ...'

        self.write({'status': 'success', 'message': msg, 'data': data})
