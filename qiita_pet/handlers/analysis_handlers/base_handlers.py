# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import loads

from tornado.web import authenticated

from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import qiita_config, r_client
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.analysis_handlers import check_analysis_access
from qiita_pet.handlers.util import to_int
from qiita_pet.util import get_network_nodes_edges
from qiita_db.analysis import Analysis


class CreateAnalysisHandler(BaseHandler):
    @authenticated
    def post(self):
        name = self.get_argument('name')
        desc = self.get_argument('description')
        analysis = Analysis.create(self.current_user, name, desc,
                                   from_default=True)

        self.redirect(u"%s/analysis/description/%s/"
                      % (qiita_config.portal_dir, analysis.id))


def analysis_description_handler_get_request(analysis_id, user):
    """Returns the analysis information

    Parameters
    ----------
    analysis_id : int
        The analysis id
    user : qiita_db.user.User
        The user performing the request
    """
    analysis = Analysis(analysis_id)
    check_analysis_access(user, analysis)

    job_info = r_client.get("analysis_%s" % analysis.id)
    alert_type = 'info'
    alert_msg = ''
    if job_info:
        job_info = loads(job_info)
        job_id = job_info['job_id']
        if job_id:
            r_payload = r_client.get(job_id)
            if r_payload:
                redis_info = loads(r_client.get(job_id))
                if redis_info['status_msg'] == 'running':
                    alert_msg = ('An artifact is being deleted from this '
                                 'analysis')
                elif redis_info['return'] is not None:
                    alert_type = redis_info['return']['status']
                    alert_msg = redis_info['return']['message'].replace(
                        '\n', '</br>')

    return {'analysis_name': analysis.name,
            'analysis_id': analysis.id,
            'analysis_is_public': analysis.is_public,
            'analysis_description': analysis.description,
            'analysis_mapping_id': analysis.mapping_file,
            'alert_type': alert_type,
            'alert_msg': alert_msg}


class AnalysisDescriptionHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self, analysis_id):
        res = analysis_description_handler_get_request(analysis_id,
                                                       self.current_user)

        self.render("analysis_description.html", **res)

    @authenticated
    @execute_as_transaction
    def post(self, analysis_id):
        analysis = Analysis(analysis_id)
        check_analysis_access(self.current_user, analysis)

        message = ''
        try:
            Analysis(analysis_id).make_public()
        except Exception as e:
            message = str(e)

        res = analysis_description_handler_get_request(
            analysis_id, self.current_user)
        if message:
            # this will display the error message in the main banner
            res['level'] = 'danger'
            res['message'] = message

        self.render("analysis_description.html", **res)


def analyisis_graph_handler_get_request(analysis_id, user):
    """Returns the graph information of the analysis

    Parameters
    ----------
    analysis_id : int
        The analysis id
    user : qiita_db.user.User
        The user performing the request

    Returns
    -------
    dict with the graph information
    """
    analysis = Analysis(analysis_id)
    # Check if the user actually has access to the analysis
    check_analysis_access(user, analysis)

    # A user has full access to the analysis if it is one of its private
    # analyses, the analysis has been shared with the user or the user is a
    # superuser or admin
    full_access = (analysis in (user.private_analyses | user.shared_analyses)
                   or user.level in {'superuser', 'admin'})

    nodes = []
    edges = []
    # Loop through all the initial artifacts of the analysis
    for a in analysis.artifacts:
        if a.processing_parameters is None:
            g = a.descendants_with_jobs
            nodes, edges = get_network_nodes_edges(g, full_access, nodes=nodes,
                                                   edges=edges)

    return {'edges': edges, 'nodes': nodes}


class AnalysisGraphHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self, analysis_id):
        analysis_id = to_int(analysis_id)
        response = analyisis_graph_handler_get_request(
            analysis_id, self.current_user)
        self.write(response)


def analyisis_job_handler_get_request(analysis_id, user):
    """Returns the job information of the analysis

    Parameters
    ----------
    analysis_id: int
        The analysis id
    user : qiita_db.user.User
        The user performing the request

    Returns
    -------
    dict with the jobs information
    """
    analysis = Analysis(analysis_id)
    # Check if the user actually has access to the analysis
    check_analysis_access(user, analysis)
    return {
        j.id: {'status': j.status, 'step': j.step,
               'error': j.log.msg if j.log else ""}
        for j in analysis.jobs}


class AnalysisJobsHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self, analysis_id):
        analysis_id = to_int(analysis_id)
        response = analyisis_job_handler_get_request(
            analysis_id, self.current_user)
        self.write(response)
