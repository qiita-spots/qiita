# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import qiita_config
from qiita_pet.util import STATUS_STYLER, is_localhost
from .base_uimodule import BaseUIModule


class ProcessedDataTab(BaseUIModule):
    @execute_as_transaction
    def render(self, study, full_access, allow_approval, approval_deny_msg):
        # currently all process data are 'BIOM'
        pd_gen = [ar for ar in study.artifacts()
                  if ar.artifact_type == 'BIOM']
        avail_pd = [(pd, STATUS_STYLER[pd.visibility]) for pd in pd_gen
                    if full_access or pd.visibility == 'public']

        return self.render_string(
            "study_description_templates/processed_data_tab.html",
            available_processed_data=avail_pd,
            study_id=study.id,
            allow_approval=allow_approval,
            approval_deny_msg=approval_deny_msg)


class ProcessedDataInfoTab(BaseUIModule):
    @execute_as_transaction
    def render(self, study_id, processed_data, allow_approval,
               approval_deny_msg):
        user = self.current_user
        # The request approval, approve processed data and make public buttons
        # are mutually exclusive. Only one of them will be shown, depending on
        # the current status of the processed data
        status = processed_data.visibility
        btn_to_show = None
        if status == 'sandbox' and qiita_config.require_approval:
            # The request approval button only appears if the processed data is
            # sandboxed and the qiita_config specifies that the approval should
            # be requested
            btn_to_show = 'request_approval'
        elif (user.level == 'admin' and status == 'awaiting_approval' and
                qiita_config.require_approval):
            # The approve processed data button only appears if the user is an
            # admin, the processed data is waiting to be approved and the qiita
            # config requires processed data approval
            btn_to_show = 'approve'
        elif status == 'private':
            # The make public button only appears if the status is private
            btn_to_show = 'make_public'

        # The revert to sandbox button only appears if the processed data is
        # not sandboxed or public
        show_revert_btn = status not in {'sandbox', 'public'}

        # process data can only have one preprocess_data
        preprocessed_data_id = processed_data.parents[0].id
        process_date = str(processed_data.timestamp)
        filepaths = processed_data.filepaths
        is_local_request = is_localhost(self.request.headers['host'])

        return self.render_string(
            "study_description_templates/processed_data_info_tab.html",
            pd_id=processed_data.id,
            preprocessed_data_id=preprocessed_data_id,
            process_date=process_date,
            filepaths=filepaths,
            is_local_request=is_local_request,
            btn_to_show=btn_to_show,
            show_revert_btn=show_revert_btn,
            allow_approval=allow_approval,
            approval_deny_msg=approval_deny_msg)
