# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import loads

from tornado.web import authenticated

from qiita_core.qiita_settings import qiita_config, r_client
from qiita_core.util import execute_as_transaction
from qiita_db.analysis import Analysis
from qiita_db.artifact import Artifact
from qiita_pet.handlers.analysis_handlers import check_analysis_access
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import to_int
from qiita_pet.util import get_network_nodes_edges


class CreateAnalysisHandler(BaseHandler):
    @authenticated
    def post(self):
        name = self.get_argument("name")
        desc = self.get_argument("description")
        mdsi = self.get_argument("merge_duplicated_sample_ids", False)
        metadata = self.request.arguments.get("analysis-metadata", None)
        reservation = self.get_argument("reservation", None)
        # we need to change from bytes to strings
        if metadata is not None:
            metadata = [m.decode("utf-8") for m in metadata]

        if mdsi in (b"on", "on"):
            mdsi = True
        analysis = Analysis.create(
            self.current_user,
            name,
            desc,
            merge_duplicated_sample_ids=mdsi,
            from_default=True,
            categories=metadata,
            reservation=reservation,
        )

        self.redirect(
            "%s/analysis/description/%s/" % (qiita_config.portal_dir, analysis.id)
        )


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
    alert_type = "info"
    alert_msg = ""
    if job_info:
        job_info = loads(job_info)
        job_id = job_info["job_id"]
        if job_id:
            r_payload = r_client.get(job_id)
            if r_payload:
                redis_info = loads(r_client.get(job_id))
                if redis_info["status_msg"] == "running":
                    alert_msg = "An artifact is being deleted from this analysis"
                elif redis_info["return"] is not None:
                    alert_type = redis_info["return"]["status"]
                    alert_msg = redis_info["return"]["message"].replace("\n", "</br>")
    artifacts = {}
    for aid, samples in analysis.samples.items():
        artifact = Artifact(aid)
        prep_ids = set([str(x.id) for x in artifact.prep_templates])
        study = artifact.study
        artifacts[aid] = (
            study.id,
            study.title,
            artifact.merging_scheme,
            samples,
            prep_ids,
        )

    return {
        "analysis_name": analysis.name,
        "analysis_id": analysis.id,
        "analysis_is_public": analysis.is_public,
        "analysis_description": analysis.description,
        "analysis_mapping_id": analysis.mapping_file,
        "analysis_owner": analysis.owner.email,
        "alert_type": alert_type,
        "artifacts": artifacts,
        "analysis_reservation": analysis._slurm_reservation()[0],
        "alert_msg": alert_msg,
    }


class AnalysisHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self, analysis_id):
        res = analysis_description_handler_get_request(analysis_id, self.current_user)

        self.render("analysis_description.html", **res)

    @authenticated
    @execute_as_transaction
    def post(self, analysis_id):
        analysis = Analysis(analysis_id)
        check_analysis_access(self.current_user, analysis)

        message = ""
        try:
            Analysis(analysis_id).make_public()
        except Exception as e:
            message = str(e)

        res = analysis_description_handler_get_request(analysis_id, self.current_user)
        if message:
            # this will display the error message in the main banner
            res["level"] = "danger"
            res["message"] = message

        self.render("analysis_description.html", **res)

    @authenticated
    @execute_as_transaction
    def patch(self, analysis_id):
        """Patches a analysis

        Follows the JSON PATCH specification:
        https://tools.ietf.org/html/rfc6902
        """
        req_op = self.get_argument("op")
        req_path = self.get_argument("path")
        req_value = self.get_argument("value", None)

        if req_op == "replace" and req_path == "reservation":
            Analysis(analysis_id).slurm_reservation = req_value
            response = {"status": "success", "message": ""}
        else:
            response = {"status": "error", "message": "Not implemented"}

        self.write(response)


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

    Raises
    ------
    ValueError
        If there is more than one workflow in a single analysis
    """
    analysis = Analysis(analysis_id)
    # Check if the user actually has access to the analysis
    check_analysis_access(user, analysis)

    # A user has full access to the analysis if it is one of its private
    # analyses, the analysis has been shared with the user or the user is a
    # superuser or admin
    full_access = analysis in (
        user.private_analyses | user.shared_analyses
    ) or user.level in {"superuser", "admin"}

    nodes = []
    edges = []
    artifacts_being_deleted = []
    wf_id = None
    # Loop through all the initial artifacts of the analysis
    for a in analysis.artifacts:
        if a.processing_parameters is None:
            g = a.descendants_with_jobs
            nodes, edges, a_wf_id = get_network_nodes_edges(
                g, full_access, nodes=nodes, edges=edges
            )

            # nodes returns [node_type, node_name, element_id]; here we
            # are looking for the node_type == artifact, and check by
            # the element/artifact_id if it's being deleted
            for a in nodes:
                if a[0] == "artifact" and Artifact(a[2]).being_deleted_by is not None:
                    artifacts_being_deleted.append(a[2])

            if wf_id is None:
                wf_id = a_wf_id
            elif a_wf_id is not None and wf_id != a_wf_id:
                # This should never happen, but worth having a useful message
                raise ValueError("More than one workflow in a single analysis")

    # the list(set()) is to remove any duplicated nodes
    return {
        "edges": list(set(edges)),
        "nodes": list(set(nodes)),
        "workflow": wf_id,
        "artifacts_being_deleted": artifacts_being_deleted,
    }


class AnalysisGraphHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self, analysis_id):
        analysis_id = to_int(analysis_id)
        response = analyisis_graph_handler_get_request(analysis_id, self.current_user)
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
        j.id: {"status": j.status, "step": j.step, "error": j.log.msg if j.log else ""}
        for j in analysis.jobs
    }


class AnalysisJobsHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self, analysis_id):
        analysis_id = to_int(analysis_id)
        response = analyisis_job_handler_get_request(analysis_id, self.current_user)
        self.write(response)
