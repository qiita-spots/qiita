# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from tornado.web import authenticated, HTTPError

from qiita_ware.context import submit
from qiita_ware.demux import stats as demux_stats
from qiita_ware.dispatchable import submit_to_VAMPS
from qiita_db.metadata_template.prep_template import PrepTemplate
from qiita_db.metadata_template.sample_template import SampleTemplate
from qiita_db.study import Study
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_core.util import execute_as_transaction


class VAMPSHandler(BaseHandler):
    @execute_as_transaction
    def display_template(self, preprocessed_data_id, msg, msg_level):
        """Simple function to avoid duplication of code"""
        preprocessed_data_id = int(preprocessed_data_id)
        try:
            preprocessed_data = PreprocessedData(preprocessed_data_id)
        except QiitaDBUnknownIDError:
            raise HTTPError(404, "PreprocessedData %d does not exist!" %
                                 preprocessed_data_id)
        else:
            user = self.current_user
            if user.level != 'admin':
                raise HTTPError(403, "No permissions of admin, "
                                     "get/VAMPSSubmitHandler: %s!" % user.id)

        prep_template = PrepTemplate(preprocessed_data.prep_template)
        sample_template = SampleTemplate(preprocessed_data.study)
        study = Study(preprocessed_data.study)
        stats = [('Number of samples', len(prep_template)),
                 ('Number of metadata headers',
                  len(sample_template.categories()))]

        demux = [path for _, path, ftype in preprocessed_data.get_filepaths()
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

        self.render('vamps_submission.html',
                    study_title=study.title, stats=stats, message=msg,
                    study_id=study.id, level=msg_level,
                    preprocessed_data_id=preprocessed_data_id)

    @authenticated
    def get(self, preprocessed_data_id):
        self.display_template(preprocessed_data_id, "", "")

    @authenticated
    @execute_as_transaction
    def post(self, preprocessed_data_id):
        # make sure user is admin and can therefore actually submit to VAMPS
        if self.current_user.level != 'admin':
            raise HTTPError(403, "User %s cannot submit to VAMPS!" %
                            self.current_user.id)
        msg = ''
        msg_level = 'success'
        preprocessed_data = PreprocessedData(preprocessed_data_id)
        state = preprocessed_data.submitted_to_vamps_status()

        demux = [path for _, path, ftype in preprocessed_data.get_filepaths()
                 if ftype == 'preprocessed_demux']
        demux_length = len(demux)

        if state in ('submitting',  'success'):
            msg = "Cannot resubmit! Current state is: %s" % state
            msg_level = 'danger'
        elif demux_length != 1:
            msg = "The study doesn't have demux files or have too many" % state
            msg_level = 'danger'
        else:
            channel = self.current_user.id
            job_id = submit(channel, submit_to_VAMPS,
                            int(preprocessed_data_id))

            self.render('compute_wait.html',
                        job_id=job_id, title='VAMPS Submission',
                        completion_redirect='/compute_complete/%s' % job_id)
            return

        self.display_template(preprocessed_data_id, msg, msg_level)
