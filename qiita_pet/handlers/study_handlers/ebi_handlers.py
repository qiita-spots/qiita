# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from json import dumps

from qiita_files.demux import stats as demux_stats
from tornado.escape import url_escape
from tornado.web import HTTPError, authenticated

from qiita_core.qiita_settings import qiita_config, r_client
from qiita_core.util import execute_as_transaction
from qiita_db.artifact import Artifact
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.metadata_template.constants import (
    PREP_TEMPLATE_COLUMNS,
    SAMPLE_TEMPLATE_COLUMNS,
)
from qiita_db.processing_job import ProcessingJob
from qiita_db.software import Parameters, Software
from qiita_pet.handlers.base_handlers import BaseHandler

VALID_SUBMISSION_TYPES = ["Demultiplexed", "per_sample_FASTQ"]


class EBISubmitHandler(BaseHandler):
    @execute_as_transaction
    def display_template(self, artifact_id, msg, msg_level):
        """Simple function to avoid duplication of code"""
        artifact_id = int(artifact_id)
        try:
            artifact = Artifact(artifact_id)
        except QiitaDBUnknownIDError:
            raise HTTPError(404, reason="Artifact %d does not exist!" % artifact_id)
        else:
            user = self.current_user
            if user.level != "admin":
                raise HTTPError(
                    403,
                    reason="No permissions of admin, "
                    "get/EBISubmitHandler: %s!" % user.id,
                )

        prep_templates = artifact.prep_templates
        allow_submission = len(prep_templates) == 1
        msg_list = ["Submission to EBI disabled:"]
        if not allow_submission:
            msg_list.append(
                "Only artifacts with a single prep template can be submitted"
            )
        # If allow_submission is already false, we technically don't need to
        # do the following work. However, there is no clean way to fix this
        # using the current structure, so we perform the work as we
        # did so it doesn't fail.
        # We currently support only one prep template for submission, so
        # grabbing the first one
        prep_template = prep_templates[0]
        study = artifact.study
        sample_template = study.sample_template
        stats = {
            "Number of samples": len(prep_template),
            "Number of metadata headers": len(sample_template.categories),
            "Number of sequences": "N/A",
            "Total forward": "N/A",
            "Total reverse": "N/A",
        }

        artifact_type = artifact.artifact_type
        if artifact_type not in VALID_SUBMISSION_TYPES:
            msg = "You can only submit: '%s' and this artifact is '%s'" % (
                ", ".join(VALID_SUBMISSION_TYPES),
                artifact_type,
            )
            msg_level = "danger"
        elif artifact_type == "Demultiplexed":
            demux = [
                x["fp"]
                for x in artifact.filepaths
                if x["fp_type"] == "preprocessed_demux"
            ]
            demux_length = len(demux)
            if demux_length > 1:
                msg = "Study appears to have multiple demultiplexed files!"
                msg_level = "danger"
            else:
                demux_file = demux[0]
                demux_file_stats = demux_stats(demux_file)
                stats["Number of sequences"] = demux_file_stats.n
                msg_level = "success"
        elif artifact_type == "per_sample_FASTQ":
            raw_forward_seqs = []
            raw_reverse_seqs = []
            for x in artifact.filepaths:
                if x["fp_type"] == "raw_forward_seqs":
                    raw_forward_seqs.append(x["fp"])
                elif x["fp_type"] == "raw_reverse_seqs":
                    raw_reverse_seqs.append(x["fp"])
            stats["Total forward"] = len(raw_forward_seqs)
            stats["Total reverse"] = len(raw_reverse_seqs)
            msg_level = "success"

        # Check if the templates have all the required columns for EBI
        pt_missing_cols = prep_template.check_restrictions(
            [PREP_TEMPLATE_COLUMNS["EBI"]]
        )
        st_missing_cols = sample_template.check_restrictions(
            [SAMPLE_TEMPLATE_COLUMNS["EBI"]]
        )
        allow_submission = (
            len(pt_missing_cols) == 0 and len(st_missing_cols) == 0 and allow_submission
        )

        if not allow_submission:
            if len(pt_missing_cols) > 0:
                msg_list.append(
                    "Columns missing in prep template: %s" % ", ".join(pt_missing_cols)
                )
            if len(st_missing_cols) > 0:
                msg_list.append(
                    "Columns missing in sample template: %s"
                    % ", ".join(st_missing_cols)
                )
            ebi_disabled_msg = "<br/>".join(msg_list)
        else:
            ebi_disabled_msg = None

        self.render(
            "ebi_submission.html",
            study_title=study.title,
            stats=stats.items(),
            message=msg,
            study_id=study.id,
            level=msg_level,
            preprocessed_data_id=artifact_id,
            investigation_type=prep_template.investigation_type,
            allow_submission=allow_submission,
            ebi_disabled_msg=ebi_disabled_msg,
        )

    @authenticated
    def get(self, preprocessed_data_id):
        self.display_template(preprocessed_data_id, "", "")

    @authenticated
    @execute_as_transaction
    def post(self, preprocessed_data_id):
        user = self.current_user
        # make sure user is admin and can therefore actually submit to EBI
        if user.level != "admin":
            raise HTTPError(403, reason="User %s cannot submit to EBI!" % user.id)
        submission_type = self.get_argument("submission_type")

        if submission_type not in ["ADD", "MODIFY"]:
            raise HTTPError(
                403,
                reason="User: %s, %s is not a recognized "
                "submission type" % (user.id, submission_type),
            )

        study = Artifact(preprocessed_data_id).study
        state = study.ebi_submission_status
        if state == "submitting":
            message = "Cannot resubmit! Current state is: %s" % state
            self.display_template(preprocessed_data_id, message, "danger")
        else:
            qiita_plugin = Software.from_name_and_version("Qiita", "alpha")
            cmd = qiita_plugin.get_command("submit_to_EBI")
            params = Parameters.load(
                cmd,
                values_dict={
                    "artifact": preprocessed_data_id,
                    "submission_type": submission_type,
                },
            )
            job = ProcessingJob.create(user, params, True)

            r_client.set(
                "ebi_submission_%s" % preprocessed_data_id,
                dumps({"job_id": job.id, "is_qiita_job": True}),
            )
            job.submit()

            level = "success"
            message = "EBI submission started. Job id: %s" % job.id

            self.redirect(
                "%s/study/description/%d?level=%s&message=%s"
                % (qiita_config.portal_dir, study.id, level, url_escape(message))
            )
