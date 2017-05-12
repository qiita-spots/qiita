# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from future.utils import viewitems
from requests import ConnectionError
import redbiom.summarize
import redbiom.search
import redbiom._requests
import redbiom.util
import redbiom.fetch
from tornado.gen import coroutine, Task

from qiita_core.util import execute_as_transaction

from .base_handlers import BaseHandler


class RedbiomPublicSearch(BaseHandler):
    @execute_as_transaction
    def get(self, search):
        self.render('redbiom.html')

    @execute_as_transaction
    def _redbiom_search(self, query, search_on, callback):
        error = False
        message = ''
        results = []

        try:
            df = redbiom.summarize.contexts()
        except ConnectionError:
            error = True
            message = 'Redbiom is down - contact admin, thanks!'

        if not error:
            contexts = df.ContextName.values
            query = query.lower()
            features = []

            if search_on in ('metadata', 'categories'):
                try:
                    features = redbiom.search.metadata_full(
                        query, categories=(search_on == 'categories'))
                except TypeError:
                    error = True
                    message = (
                        'Not a valid search: "%s", are you sure this is a '
                        'valid metadata %s?' % (
                            query, 'value' if search_on == 'metadata' else
                            'category'))
                except ValueError:
                    error = True
                    message = (
                        'Not a valid search: "%s", your query is too small '
                        '(too few letters), try a longer query' % query)
            elif search_on == 'observations':
                features = [s.split('_', 1)[1] for context in contexts
                            for s in redbiom.util.samples_from_observations(
                                query.split(' '), True, context)]
            else:
                error = True
                message = ('Incorrect search by: you can use observations '
                           'or metadata and you passed: %s' % search_on)

            if not error:
                import qiita_db as qdb
                import qiita_db.sql_connection as qdbsc
                if features:
                    if search_on in ('metadata', 'observations'):
                        sql = """
                        WITH main_query AS (
                            SELECT study_title, study_id, artifact_id,
                                array_agg(DISTINCT sample_id) AS samples,
                                qiita.artifact_descendants(artifact_id) AS
                                    children
                            FROM qiita.study_prep_template
                            JOIN qiita.prep_template USING (prep_template_id)
                            JOIN qiita.prep_template_sample USING
                                (prep_template_id)
                            JOIN qiita.study USING (study_id)
                            WHERE sample_id IN %s
                            GROUP BY study_title, study_id, artifact_id),
                         artifact_query AS (
                            SELECT study_title, study_id, samples,
                                name, command_id,
                                (main_query.children).artifact_id AS
                                    artifact_id
                            FROM main_query
                            JOIN qiita.artifact a ON
                                (main_query.children).artifact_id =
                                    a.artifact_id
                            JOIN qiita.artifact_type at ON (
                                at.artifact_type_id = a.artifact_type_id
                                AND artifact_type = 'BIOM')
                            ORDER BY artifact_id),
                         parent_query AS (
                            SELECT artifact_query.*,
                                array_agg(parent_params) as parent_parameters
                            FROM artifact_query
                            LEFT JOIN qiita.parent_artifact pa ON (
                                artifact_query.artifact_id = pa.artifact_id)
                            LEFT JOIN qiita.artifact a ON (
                                pa.parent_id = a.artifact_id),
                                json_each_text(command_parameters)
                                    parent_params
                            GROUP BY artifact_query.study_title,
                                artifact_query.study_id,
                                artifact_query.samples, artifact_query.name,
                                artifact_query.command_id,
                                artifact_query.artifact_id)
                        SELECT * FROM parent_query
                        """

                        sql_params = """
                        SELECT parameter_set_name, array_agg(ps) AS param_set
                        FROM qiita.default_parameter_set,
                            json_each_text(parameter_set) ps
                        GROUP BY parameter_set_name"""

                        with qdbsc.TRN:
                            results = []
                            commands = {}
                            # obtaining all existing parameters, note that
                            # they are not that many (~40) and we don't expect
                            # to have a huge growth in the near future
                            qdbsc.TRN.add(sql_params)
                            params = {pname: eval(params) for pname, params
                                      in qdbsc.TRN.execute_fetchindex()}

                            # now let's get the actual artifacts
                            qdbsc.TRN.add(sql, [tuple(features)])
                            for row in qdbsc.TRN.execute_fetchindex():
                                title, sid, samples, name, cid, aid, pp = row
                                nr = {'study_title': title, 'study_id': sid,
                                      'artifact_id': aid, 'aname': name,
                                      'samples': samples}
                                if cid is not None:
                                    if cid not in commands:
                                        c = qdb.software.Command(cid)
                                        commands[cid] = '%s - %s v%s' % (
                                            c.name, c.software.name,
                                            c.software.version)

                                    # [-1] taking the last cause it's sorted by
                                    #      the number of overlapping parameters
                                    # [0] then taking the first element that is
                                    # the name of the parameter set
                                    ppc = sorted(
                                        [[k, len(eval(pp) & v)]
                                         for k, v in viewitems(params)],
                                        key=lambda x: x[1])[-1][0]

                                    nr['command'] = '%s @ %s' % (
                                        commands[cid], ppc)
                                else:
                                    nr['command'] = ''
                                results.append(nr)
                    else:
                        sql = """
                            WITH get_studies AS (
                                SELECT
                                    trim(table_name, 'sample_')::int AS
                                        study_id,
                                    array_agg(column_name::text) AS columns
                                FROM information_schema.columns
                                WHERE column_name IN %s
                                    AND table_name LIKE 'sample_%%'
                                    AND table_name NOT IN (
                                        'prep_template',
                                        'prep_template_sample')
                                GROUP BY table_name)
                            SELECT study_title, get_studies.study_id, columns
                            FROM get_studies
                            JOIN qiita.study ON get_studies.study_id =
                                qiita.study.study_id"""
                        with qdbsc.TRN:
                            results = []
                            qdbsc.TRN.add(sql, [tuple(features)])
                            for row in qdbsc.TRN.execute_fetchindex():
                                title, sid, cols = row
                                nr = {'study_title': title, 'study_id': sid,
                                      'artifact_id': None, 'aname': None,
                                      'samples': cols,
                                      'command': ', '.join(cols),
                                      'software': None, 'version': None}
                                results.append(nr)
                else:
                    error = True
                    message = 'No samples where found! Try again ...'
        callback((results, message))

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
