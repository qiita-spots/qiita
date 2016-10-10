# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from tornado.web import authenticated, HTTPError
from qiita_files.demux import stats as demux_stats

from qiita_ware.context import submit
from qiita_ware.dispatchable import submit_to_VAMPS
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.artifact import Artifact
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_core.util import execute_as_transaction


class VAMPSHandler(BaseHandler):
    @execute_as_transaction
    def display_template(self, preprocessed_data_id, msg, msg_level):
        """Simple function to avoid duplication of code"""
        preprocessed_data_id = int(preprocessed_data_id)
        try:
            preprocessed_data = Artifact(preprocessed_data_id)
        except QiitaDBUnknownIDError:
            raise HTTPError(404, "Artifact %d does not exist!" %
                                 preprocessed_data_id)
        else:
            user = self.current_user
            if user.level != 'admin':
                raise HTTPError(403, "No permissions of admin, "
                                     "get/VAMPSSubmitHandler: %s!" % user.id)
        prep_templates = preprocessed_data.prep_templates
        allow_submission = len(prep_templates) == 1
        msg_list = ["Submission to EBI disabled:"]
        if not allow_submission:
            msg_list.append(
                "Only artifacts with a single prep template can be submitted")
        # If allow_submission is already false, we technically don't need to
        # do the following work. However, there is no clean way to fix this
        # using the current structure, so we perform the work as we
        # did so it doesn't fail.
        # We currently support only one prep template for submission, so
        # grabbing the first one
        prep_template = prep_templates[0]
        study = preprocessed_data.study
        sample_template = study.sample_template
        stats = [('Number of samples', len(prep_template)),
                 ('Number of metadata headers',
                  len(sample_template.categories()))]

        demux = [path for _, path, ftype in preprocessed_data.filepaths
                 if ftype == 'preprocessed_demux']
        demux_length = len(demux)

        if not demux_length:
            msg = ("Study does not appear to have demultiplexed "
                   "sequences associated")
            msg_level = 'danger'
        elif demux_length > 1:
            msg = ("Study appears to have multiple demultiplexed files!")
            msg_level = 'danger'
        elif demux_length == 1:
            demux_file = demux[0]
            demux_file_stats = demux_stats(demux_file)
            stats.append(('Number of sequences', demux_file_stats.n))
            msg_level = 'success'

        # In EBI here we check that we have the required field for submission,
        # however for VAMPS we don't need that

        if not allow_submission:
            disabled_msg = "<br/>".join(msg_list)
        else:
            disabled_msg = None

        self.render('vamps_submission.html',
                    study_title=study.title, stats=stats, message=msg,
                    study_id=study.id, level=msg_level,
                    preprocessed_data_id=preprocessed_data_id,
                    investigation_type=prep_template.investigation_type,
                    allow_submission=allow_submission,
                    disabled_msg=disabled_msg)

    @authenticated
    def get(self, preprocessed_data_id):
        self.display_template(preprocessed_data_id, "", "")

    @authenticated
    @execute_as_transaction
    def post(self, preprocessed_data_id):
        user = self.current_user
        # make sure user is admin and can therefore actually submit to VAMPS
        if user.level != 'admin':
            raise HTTPError(403, "User %s cannot submit to VAMPS!" %
                            user.id)
        msg = ''
        msg_level = 'success'
        study = Artifact(preprocessed_data_id).study
        study_id = study.id
        state = study.ebi_submission_status
        if state == 'submitting':
            msg = "Cannot resubmit! Current state is: %s" % state
            msg_level = 'danger'
        else:
            channel = user.id
            job_id = submit(channel, submit_to_VAMPS,
                            int(preprocessed_data_id))

            self.render('compute_wait.html',
                        job_id=job_id, title='VAMPS Submission',
                        completion_redirect=('/study/description/%s?top_tab='
                                             'preprocessed_data_tab&sub_tab=%s'
                                             % (study_id,
                                                preprocessed_data_id)))
            return

        self.display_template(preprocessed_data_id, msg, msg_level)
