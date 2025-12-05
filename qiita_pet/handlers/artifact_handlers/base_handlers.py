# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import dumps
from os.path import basename, relpath

from humanize import naturalsize
from tornado.web import StaticFileHandler, authenticated

from qiita_core.qiita_settings import qiita_config, r_client
from qiita_db.artifact import Artifact
from qiita_db.logger import LogEntry
from qiita_db.meta_util import RAW_DATA_ARTIFACT_TYPE
from qiita_db.processing_job import ProcessingJob
from qiita_db.software import Command, Parameters, Software
from qiita_db.util import get_visibilities, send_email
from qiita_pet.exceptions import QiitaHTTPError
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import safe_execution

PREP_TEMPLATE_KEY_FORMAT = "prep_template_%s"


def check_artifact_access(user, artifact):
    """Checks whether user has access to an artifact

    Parameters
    ----------
    user : qiita_db.user.User object
        User to check
    artifact : qiita_db.artifact.Artifact
        Artifact to check access for

    Raises
    ------
    QiitaHTTPError
        If the user doesn't have access to the given artifact
    """
    if user.level in ("admin", "wet-lab admin"):
        return

    study = artifact.study
    if artifact.visibility == "public":
        # if it's public we need to confirm that this artifact has no possible
        # human sequences
        if artifact.has_human and not study.has_access(user, True):
            raise QiitaHTTPError(403, "Access denied to artifact %s" % artifact.id)
    else:
        analysis = artifact.analysis
        if study:
            if not study.has_access(user):
                raise QiitaHTTPError(403, "Access denied to study %s" % artifact.id)
        elif analysis:
            if not analysis.has_access(user):
                raise QiitaHTTPError(403, "Access denied to artifact %s" % artifact.id)
        else:
            # This can't happen but worth adding a check
            raise QiitaHTTPError(500, "Error accessing artifact %s" % artifact.id)


def artifact_summary_get_request(user, artifact_id):
    """Returns the information for the artifact summary page

    Parameters
    ----------
    user : qiita_db.user.User
        The user making the request
    artifact_id : int or str
        The artifact id

    Returns
    -------
    dict of objects
        A dictionary containing the artifact summary information
        {'name': str,
         'artifact_id': int,
         'visibility': str,
         'editable': bool,
         'buttons': str,
         'processing_parameters': dict of {str: object},
         'files': list of (int, str),
         'is_from_analysis': bool,
         'summary': str or None,
         'job': [str, str, str],
         'errored_jobs': list of [str, str]}
    """
    artifact_id = int(artifact_id)
    artifact = Artifact(artifact_id)
    artifact_type = artifact.artifact_type

    check_artifact_access(user, artifact)

    visibility = artifact.visibility
    summary = artifact.html_summary_fp
    job_info = None
    errored_summary_jobs = []

    # Check if the HTML summary exists
    if summary:
        # Magic number 1: If the artifact has a summary, the call
        # artifact.html_summary_fp returns a tuple with 2 elements. The first
        # element is the filepath id, while the second one is the actual
        # actual filepath. We are only interested on the actual filepath,
        # hence the 1 value.
        summary = relpath(summary[1], qiita_config.base_data_dir)
    else:
        # Check if the summary is being generated
        command = Command.get_html_generator(artifact_type)
        all_jobs = set(artifact.jobs(cmd=command))
        jobs = []
        errored_summary_jobs = []
        for j in all_jobs:
            if j.status in ["queued", "running"]:
                jobs.append(j)
            elif j.status in ["error"]:
                errored_summary_jobs.append(j)
        if jobs:
            # There is already a job generating the HTML. Also, there should be
            # at most one job, because we are not allowing here to start more
            # than one
            job = jobs[0]
            job_info = [job.id, job.status, job.step]

    # Check if the artifact is editable by the given user
    study = artifact.study
    analysis = artifact.analysis
    # if is a folder and has no parents, it means that is an SPP job and
    # nobody should be able to change anything about it
    if artifact_type == "job-output-folder" and not artifact.parents:
        editable = False
    else:
        editable = study.can_edit(user) if study else analysis.can_edit(user)

    buttons = []
    btn_base = (
        "<button onclick=\"if (confirm('Are you sure you want to %s "
        "artifact id: {0}?')) {{ set_artifact_visibility('%s', {0}) }}\" "
        'class="btn btn-primary btn-sm">%s</button>'
    ).format(artifact_id)
    if not analysis and artifact_type != "job-output-folder":
        # If the artifact is part of a study, the buttons shown depend in
        # multiple factors (see each if statement for an explanation of those)
        if qiita_config.require_approval:
            if visibility == "sandbox" and artifact.parents:
                # The request approval button only appears if the artifact is
                # sandboxed and the qiita_config specifies that the approval
                # should be requested
                buttons.append(
                    btn_base
                    % ("request approval for", "awaiting_approval", "Request approval")
                )
            elif user.level == "admin" and visibility == "awaiting_approval":
                # The approve artifact button only appears if the user is an
                # admin the artifact is waiting to be approvaed and the qiita
                # config requires artifact approval
                buttons.append(btn_base % ("approve", "private", "Approve artifact"))

        if visibility == "private":
            # The make public button only appears if the artifact is private
            buttons.append(btn_base % ("make public", "public", "Make public"))

        # The revert to sandbox button only appears if the artifact is not
        # sandboxed nor public
        if visibility not in {"sandbox", "public"}:
            buttons.append(
                btn_base % ("revert to sandbox", "sandbox", "Revert to sandbox")
            )

        if user.level == "admin" and not study.autoloaded:
            if artifact.can_be_submitted_to_ebi:
                buttons.append(
                    '<a class="btn btn-primary btn-sm" '
                    'href="/ebi_submission/%d">'
                    '<span class="glyphicon glyphicon-export"></span>'
                    " Submit to EBI</a>" % artifact_id
                )
            if artifact.can_be_submitted_to_vamps:
                if not artifact.is_submitted_to_vamps:
                    buttons.append(
                        '<a class="btn btn-primary btn-sm" href="/vamps/%d">'
                        '<span class="glyphicon glyphicon-export"></span>'
                        " Submit to VAMPS</a>" % artifact_id
                    )

    if visibility != "public":
        # Have no fear, this is just python to generate html with an onclick in
        # javascript that makes an ajax call to a separate url, takes the
        # response and writes it to the newly uncollapsed div.  Do note that
        # you have to be REALLY CAREFUL with properly escaping quotation marks.
        private_download = (
            '<button class="btn btn-primary btn-sm" type="button" '
            'aria-expanded="false" aria-controls="privateDownloadLink" '
            'onclick="generate_private_download_link(%d)">Generate '
            'Download Link</button><div class="collapse" '
            'id="privateDownloadLink"><div class="card card-body" '
            'id="privateDownloadText">Generating Download Link...'
            "</div></div>"
        ) % artifact_id
        buttons.append(private_download)

    files = [
        (
            x["fp_id"],
            "%s (%s)" % (basename(x["fp"]), x["fp_type"].replace("_", " ")),
            x["checksum"],
            naturalsize(x["fp_size"], gnu=True),
        )
        for x in artifact.filepaths
        if x["fp_type"] != "directory"
    ]

    # TODO: https://github.com/biocore/qiita/issues/1724 Remove this hardcoded
    # values to actually get the information from the database once it stores
    # the information
    if artifact_type in RAW_DATA_ARTIFACT_TYPE:
        # If the artifact is one of the "raw" types, only the owner of the
        # study and users that has been shared with can see the files
        study = artifact.study
        has_access = study.has_access(user, no_public=True)
        if not study.public_raw_download and not has_access:
            files = []

    proc_params = artifact.processing_parameters
    if proc_params:
        cmd = proc_params.command
        sw = cmd.software
        processing_info = {
            "command": cmd.name,
            "software": sw.name,
            "software_version": sw.version,
            "processing_parameters": proc_params.values,
            "command_active": cmd.active,
            "software_deprecated": sw.deprecated,
            "software_description": sw.description,
        }
    else:
        processing_info = {}

    return {
        "name": artifact.name,
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "visibility": visibility,
        "editable": editable,
        "buttons": " ".join(buttons),
        "processing_info": processing_info,
        "files": files,
        "is_from_analysis": artifact.analysis is not None,
        "summary": summary,
        "job": job_info,
        "artifact_timestamp": artifact.timestamp.strftime("%Y-%m-%d %H:%m"),
        "being_deleted": artifact.being_deleted_by is not None,
        "errored_summary_jobs": errored_summary_jobs,
    }


def artifact_summary_post_request(user, artifact_id, force_creation=False):
    """Launches the HTML summary generation and returns the job information

    Parameters
    ----------
    user : qiita_db.user.User
        The user making the request
    artifact_id : int or str
        The artifact id
    force_creation : bool
        If all jobs should be ignored and it should force creation

    Returns
    -------
    dict of objects
        A dictionary containing the job summary information
        {'job': [str, str, str]}
    """
    artifact_id = int(artifact_id)
    artifact = Artifact(artifact_id)

    check_artifact_access(user, artifact)

    # Check if the summary is being generated or has been already generated
    command = Command.get_html_generator(artifact.artifact_type)
    jobs = artifact.jobs(cmd=command)
    jobs = [j for j in jobs if j.status in ["queued", "running", "success"]]
    if not force_creation and jobs:
        # The HTML summary is either being generated or already generated.
        # Return the information of that job so we only generate the HTML
        # once - Magic number 0 -> we are ensuring that there is only one
        # job generating the summary, so we can use the index 0 to access to
        # that job
        job = jobs[0]
    else:
        # Create a new job to generate the HTML summary and return the newly
        # created job information
        job = ProcessingJob.create(
            user,
            Parameters.load(command, values_dict={"input_data": artifact_id}),
            True,
        )
        job.submit()

    return {"job": [job.id, job.status, job.step]}


class ArtifactSummaryAJAX(BaseHandler):
    @authenticated
    def get(self, artifact_id):
        with safe_execution():
            res = artifact_summary_get_request(self.current_user, artifact_id)

        self.render("artifact_ajax/artifact_summary.html", **res)

    @authenticated
    def post(self, artifact_id):
        with safe_execution():
            res = artifact_summary_post_request(self.current_user, artifact_id)
        self.write(res)


def artifact_patch_request(
    user, artifact_id, req_op, req_path, req_value=None, req_from=None
):
    """Modifies an attribute of the artifact

    Parameters
    ----------
    user : qiita_db.user.User
        The user performing the patch operation
    artifact_id : int
        Id of the artifact in which the patch operation is being performed
    req_op : str
        The operation to perform on the artifact
    req_path : str
        The prep information and attribute to patch
    req_value : str, optional
        The value that needs to be modified
    req_from : str, optional
        The original path of the element

    Raises
    ------
    QiitaHTTPError
        If `req_op` != 'replace'
        If the path parameter is incorrect
        If missing req_value
        If the attribute to replace is not known
    """
    if req_op == "replace":
        req_path = [v for v in req_path.split("/") if v]
        if len(req_path) != 1:
            raise QiitaHTTPError(404, "Incorrect path parameter")

        attribute = req_path[0]

        # Check if the user actually has access to the artifact
        artifact = Artifact(artifact_id)
        check_artifact_access(user, artifact)

        if not req_value:
            raise QiitaHTTPError(404, "Missing value to replace")

        if attribute == "name":
            artifact.name = req_value
            return
        elif attribute == "visibility":
            if req_value not in get_visibilities():
                raise QiitaHTTPError(400, "Unknown visibility value: %s" % req_value)

            if (
                req_value == "private"
                and qiita_config.require_approval
                and not user.level == "admin"
            ):
                raise QiitaHTTPError(
                    403, "User does not have permissions to approve change"
                )

            try:
                artifact.visibility = req_value
            except Exception as e:
                raise QiitaHTTPError(403, str(e).replace("\n", "<br/>"))

            sid = artifact.study.id
            if artifact.visibility == "awaiting_approval":
                email_to = qiita_config.help_email
                subject = "QIITA: Artifact %s awaiting_approval. Study %d, Prep %d" % (
                    artifact_id,
                    sid,
                    artifact.prep_templates[0].id,
                )
                message = (
                    "%s requested approval. <a "
                    'href="https://qiita.ucsd.edu/study/description/'
                    '%d">Study %d</a>.' % (user.email, sid, sid)
                )
                try:
                    send_email(email_to, subject, message)
                except Exception:
                    msg = (
                        "Couldn't send email to admins, please email us "
                        "directly to <a href='mailto:{0}'>{0}</a>.".format(email_to)
                    )
                    raise QiitaHTTPError(400, msg)
            else:
                msg = "%s changed artifact %s (study %d) to %s" % (
                    user.email,
                    artifact_id,
                    sid,
                    req_value,
                )
                LogEntry.create("Warning", msg)
        else:
            # We don't understand the attribute so return an error
            raise QiitaHTTPError(
                404,
                'Attribute "%s" not found. Please, '
                "check the path parameter" % attribute,
            )
    else:
        raise QiitaHTTPError(
            400,
            'Operation "%s" not supported. Current '
            "supported operations: replace" % req_op,
        )


def artifact_post_req(user, artifact_id):
    """Deletes the artifact

    Parameters
    ----------
    user : qiita_db.user.User
        The user requesting the action
    artifact_id : int
        Id of the artifact being deleted
    """
    artifact_id = int(artifact_id)
    artifact = Artifact(artifact_id)
    check_artifact_access(user, artifact)

    being_deleted_by = artifact.being_deleted_by

    if being_deleted_by is None:
        analysis = artifact.analysis

        if analysis:
            # Do something when deleting in the analysis part to keep
            # track of it
            redis_key = "analysis_%s" % analysis.id
        else:
            pt_id = artifact.prep_templates[0].id
            redis_key = PREP_TEMPLATE_KEY_FORMAT % pt_id

        qiita_plugin = Software.from_name_and_version("Qiita", "alpha")
        cmd = qiita_plugin.get_command("delete_artifact")
        params = Parameters.load(cmd, values_dict={"artifact": artifact_id})
        job = ProcessingJob.create(user, params, True)

        r_client.set(redis_key, dumps({"job_id": job.id, "is_qiita_job": True}))

        job.submit()
    else:
        job = being_deleted_by

    return {"job": job.id}


class ArtifactAJAX(BaseHandler):
    @authenticated
    def post(self, artifact_id):
        with safe_execution():
            res = artifact_post_req(self.current_user, artifact_id)
        self.write(res)
        self.finish()

    @authenticated
    def patch(self, artifact_id):
        """Patches a prep template in the system

        Follows the JSON PATCH specification:
        https://tools.ietf.org/html/rfc6902
        """
        req_op = self.get_argument("op")
        req_path = self.get_argument("path")
        req_value = self.get_argument("value", None)
        req_from = self.get_argument("from", None)

        with safe_execution():
            artifact_patch_request(
                self.current_user, artifact_id, req_op, req_path, req_value, req_from
            )

        self.finish()


class ArtifactSummaryHandler(StaticFileHandler, BaseHandler):
    @authenticated
    def validate_absolute_path(self, root, absolute_path):
        """Overrides StaticFileHandler's method to include authentication"""
        user = self.current_user

        # we are going to inverse traverse the absolute_path and find the first
        # instance of an int, which is the artifact_id
        for s in reversed(absolute_path.split("/")):
            try:
                artifact_id = int(s)
                break
            except ValueError:
                pass

        # This call will check if the user has access to the artifact or not,
        # taking into account admin privileges. If not it will raise a 403
        # which will be handled correctly by tornado
        check_artifact_access(user, Artifact(artifact_id))

        # If we reach this point the user has access to the file - return it
        return super(ArtifactSummaryHandler, self).validate_absolute_path(
            root, absolute_path
        )
