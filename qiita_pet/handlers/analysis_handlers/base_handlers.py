# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import authenticated

from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import qiita_config
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.analysis_handlers import check_analysis_access
from qiita_pet.handlers.util import to_int
from qiita_db.analysis import Analysis


class CreateAnalysisHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def post(self):
        name = self.get_argument('name')
        desc = self.get_argument('description')
        analysis = Analysis.create(self.current_user, name, desc,
                                   from_default=True)

        self.redirect(u"%s/analysis/description/%s/"
                      % (qiita_config.portal_dir, analysis.id))


class AnalysisDescriptionHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self, analysis_id):
        analysis = Analysis(analysis_id)
        check_analysis_access(self.current_user, analysis)

        self.render("analysis_description.html", analysis_name=analysis.name,
                    analysis_id=analysis_id,
                    analysis_description=analysis.description)


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

    nodes = set()
    edges = set()
    # Loop through all the initial artifacts of the analysis
    for a in analysis.artifacts:
        g = a.descendants_with_jobs
        # Loop through all the nodes in artifact descendants graph
        for n in g.nodes():
            # Get if the object is an artifact or a job
            obj_type = n[0]
            # Get the actual object
            obj = n[1]
            if obj_type == 'job':
                name = obj.command.name
            else:
                if full_access or obj.visibility == 'public':
                    name = '%s - %s' % (obj.name, obj.artifact_type)
                else:
                    continue
            nodes.add((obj_type, obj.id, name))

        edges.update({(s[1].id, t[1].id) for s, t in g.edges()})

    # Transforming to lists so they are JSON serializable
    return {'edges': list(edges), 'nodes': list(nodes)}


class AnalysisGraphHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self):
        analysis_id = to_int(self.get_argument('analysis_id'))
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
    def get(self):
        analysis_id = to_int(self.get_argument('analysis_id'))
        response = analyisis_job_handler_get_request(
            analysis_id, self.current_user)
        self.write(response)
