# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import basename
from json import dumps

from tornado.web import authenticated
from moi import r_client

from qiita_core.qiita_settings import qiita_config
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import safe_execution
from qiita_pet.exceptions import QiitaHTTPError
from qiita_ware.context import safe_submit
from qiita_ware.dispatchable import delete_artifact
from qiita_db.artifact import Artifact
from qiita_db.software import Command, Parameters
from qiita_db.processing_job import ProcessingJob
from qiita_db.util import get_visibilities


PREP_TEMPLATE_KEY_FORMAT = 'prep_template_%s'


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
    if user.level == 'admin':
        return
    if artifact.visibility != 'public':
        study = artifact.study
        analysis = artifact.analysis
        if study:
            if not study.has_access(user):
                raise QiitaHTTPError(403, "Access denied to study %s"
                                          % artifact.id)
        elif analysis:
            if not analysis.has_access(user):
                raise QiitaHTTPError(403, "Access denied to artifact %s"
                                          % artifact.id)
        else:
            # This can't happen but worth adding a check
            raise QiitaHTTPError(500, "Error accessing artifact %s"
                                      % artifact.id)


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
         'processing_jobs': list of [str, str, str, str, str],
         'summary': str or None,
         'job': [str, str, str],
         'errored_jobs': list of [str, str]}
    """
    artifact_id = int(artifact_id)
    artifact = Artifact(artifact_id)

    check_artifact_access(user, artifact)

    visibility = artifact.visibility
    summary = artifact.html_summary_fp
    job_info = None
    errored_jobs = []
    processing_jobs = []
    for j in artifact.jobs():
        if j.command.software.type == "artifact transformation":
            status = j.status
            if status == 'success':
                continue
            j_msg = j.log.msg if status == 'error' else None
            processing_jobs.append(
                [j.id, j.command.name, j.status, j.step, j_msg])

    # Check if the HTML summary exists
    if summary:
        with open(summary[1]) as f:
            summary = f.read()
    else:
        # Check if the summary is being generated
        command = Command.get_html_generator(artifact.artifact_type)
        all_jobs = set(artifact.jobs(cmd=command))
        jobs = [j for j in all_jobs if j.status in ['queued', 'running']]
        errored_jobs = [(j.id, j.log.msg)
                        for j in all_jobs if j.status in ['error']]
        if jobs:
            # There is already a job generating the HTML. Also, there should be
            # at most one job, because we are not allowing here to start more
            # than one
            job = jobs[0]
            job_info = [job.id, job.status, job.step]

    # Check if the artifact is editable by the given user
    study = artifact.study
    analysis = artifact.analysis
    editable = study.can_edit(user) if study else analysis.can_edit(user)

    buttons = []
    btn_base = (
        '<button onclick="if (confirm(\'Are you sure you want to %s '
        'artifact id: {0}?\')) {{ set_artifact_visibility(\'%s\', {0}) }}" '
        'class="btn btn-primary btn-sm">%s</button>').format(artifact_id)

    if analysis:
        # If the artifact is part of an analysis, we don't require admin
        # approval, and the artifact can be made public only if all the
        # artifacts used to create the initial artifact set are public
        if analysis.can_be_publicized and visibility != 'public':
            buttons.append(btn_base % ('make public', 'public', 'Make public'))

    else:
        # If the artifact is part of a study, the buttons shown depend in
        # multiple factors (see each if statement for an explanation of those)
        if qiita_config.require_approval:
            if visibility == 'sandbox':
                # The request approval button only appears if the artifact is
                # sandboxed and the qiita_config specifies that the approval
                # should be requested
                buttons.append(
                    btn_base % ('request approval for', 'awaiting_approval',
                                'Request approval'))
            elif user.level == 'admin' and visibility == 'awaiting_approval':
                # The approve artifact button only appears if the user is an
                # admin the artifact is waiting to be approvaed and the qiita
                # config requires artifact approval
                buttons.append(btn_base % ('approve', 'private',
                                           'Approve artifact'))

        if visibility == 'private':
            # The make public button only appears if the artifact is private
            buttons.append(btn_base % ('make public', 'public', 'Make public'))

        # The revert to sandbox button only appears if the artifact is not
        # sandboxed nor public
        if visibility not in {'sandbox', 'public'}:
            buttons.append(btn_base % ('revert to sandbox', 'sandbox',
                                       'Revert to sandbox'))

        if user.level == 'admin':
            if artifact.can_be_submitted_to_ebi:
                if not artifact.is_submitted_to_ebi:
                    buttons.append(
                        '<a class="btn btn-primary btn-sm" '
                        'href="/ebi_submission/%d">'
                        '<span class="glyphicon glyphicon-export"></span>'
                        ' Submit to EBI</a>' % artifact_id)
            if artifact.can_be_submitted_to_vamps:
                if not artifact.is_submitted_to_vamps:
                    buttons.append(
                        '<a class="btn btn-primary btn-sm" href="/vamps/%d">'
                        '<span class="glyphicon glyphicon-export"></span>'
                        ' Submit to VAMPS</a>' % artifact_id)

    files = [(f_id, "%s (%s)" % (basename(fp), f_type.replace('_', ' ')))
             for f_id, fp, f_type in artifact.filepaths
             if f_type != 'directory']

    # TODO: https://github.com/biocore/qiita/issues/1724 Remove this hardcoded
    # values to actually get the information from the database once it stores
    # the information
    if artifact.artifact_type in ['SFF', 'FASTQ', 'FASTA', 'FASTA_Sanger',
                                  'per_sample_FASTQ']:
        # If the artifact is one of the "raw" types, only the owner of the
        # study and users that has been shared with can see the files
        if not artifact.study.has_access(user, no_public=True):
            files = []

    processing_parameters = (artifact.processing_parameters.values
                             if artifact.processing_parameters is not None
                             else {})

    return {'name': artifact.name,
            'artifact_id': artifact_id,
            'visibility': visibility,
            'editable': editable,
            'buttons': ' '.join(buttons),
            'processing_parameters': processing_parameters,
            'files': files,
            'processing_jobs': processing_jobs,
            'summary': summary,
            'job': job_info,
            'errored_jobs': errored_jobs}


def artifact_summary_post_request(user, artifact_id):
    """Launches the HTML summary generation and returns the job information

    Parameters
    ----------
    user : qiita_db.user.User
        The user making the request
    artifact_id : int or str
        The artifact id

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
    jobs = [j for j in jobs if j.status in ['queued', 'running', 'success']]
    if jobs:
        # The HTML summary is either being generated or already generated.
        # Return the information of that job so we only generate the HTML
        # once - Magic number 0 -> we are ensuring that there is only one
        # job generating the summary, so we can use the index 0 to access to
        # that job
        job = jobs[0]
    else:
        # Create a new job to generate the HTML summary and return the newly
        # created job information
        job = ProcessingJob.create(user, Parameters.load(
            command, values_dict={'input_data': artifact_id}))
        job.submit()

    return {'job': [job.id, job.status, job.step]}


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


def artifact_patch_request(user, artifact_id, req_op, req_path, req_value=None,
                           req_from=None):
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
    if req_op == 'replace':
        req_path = [v for v in req_path.split('/') if v]
        if len(req_path) != 1:
            raise QiitaHTTPError(404, 'Incorrect path parameter')

        attribute = req_path[0]

        # Check if the user actually has access to the artifact
        artifact = Artifact(artifact_id)
        check_artifact_access(user, artifact)

        if not req_value:
            raise QiitaHTTPError(404, 'Missing value to replace')

        if attribute == 'name':
            artifact.name = req_value
            return
        elif attribute == 'visibility':
            if req_value not in get_visibilities():
                raise QiitaHTTPError(400, 'Unknown visibility value: %s'
                                          % req_value)
            # Set the approval to private if needs approval and admin
            if req_value == 'private':
                if not qiita_config.require_approval:
                    artifact.visibility = 'private'
                # Set the approval to private if approval not required
                elif user.level == 'admin':
                    artifact.visibility = 'private'
                # Trying to set approval without admin privileges
                else:
                    raise QiitaHTTPError(403, 'User does not have permissions '
                                              'to approve change')
            else:
                artifact.visibility = req_value
        else:
            # We don't understand the attribute so return an error
            raise QiitaHTTPError(404, 'Attribute "%s" not found. Please, '
                                      'check the path parameter' % attribute)
    else:
        raise QiitaHTTPError(400, 'Operation "%s" not supported. Current '
                                  'supported operations: replace' % req_op)


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

    analysis = artifact.analysis

    if analysis:
        # Do something when deleting in the analysis part to keep track of it
        redis_key = "analysis_%s" % analysis.id
    else:
        pt_id = artifact.prep_templates[0].id
        redis_key = PREP_TEMPLATE_KEY_FORMAT % pt_id

    job_id = safe_submit(user.id, delete_artifact, artifact_id)
    r_client.set(redis_key, dumps({'job_id': job_id, 'is_qiita_job': False}))


class ArtifactAJAX(BaseHandler):
    @authenticated
    def post(self, artifact_id):
        with safe_execution():
            artifact_post_req(self.current_user, artifact_id)
        self.finish()

    @authenticated
    def patch(self, artifact_id):
        """Patches a prep template in the system

        Follows the JSON PATCH specification:
        https://tools.ietf.org/html/rfc6902
        """
        req_op = self.get_argument('op')
        req_path = self.get_argument('path')
        req_value = self.get_argument('value', None)
        req_from = self.get_argument('from', None)

        with safe_execution():
            artifact_patch_request(self.current_user, artifact_id, req_op,
                                   req_path, req_value, req_from)

        self.finish()
