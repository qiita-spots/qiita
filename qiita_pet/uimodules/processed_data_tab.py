# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from qiita_core.util import execute_as_transaction
from qiita_core.qiita_settings import qiita_config
from qiita_db.data import ProcessedData
from qiita_pet.util import STATUS_STYLER, is_local_connection
from .base_uimodule import BaseUIModule


class ProcessedDataTab(BaseUIModule):
    @execute_as_transaction
    def render(self, study, full_access, allow_approval, approval_deny_msg):
        pd_gen = (ProcessedData(pd_id) for pd_id in
                  sorted(study.processed_data()))
        avail_pd = [(pd.id, pd, STATUS_STYLER[pd.status]) for pd in pd_gen
                    if full_access or pd.status == 'public']

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
        status = processed_data.status
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

        pd_id = processed_data.id
        preprocessed_data_id = processed_data.preprocessed_data
        process_date = processed_data.processing_info['processed_date']
        filepaths = processed_data.get_filepaths()
        is_local_request = is_local_connection(self.request.headers['host'])

        return self.render_string(
            "study_description_templates/processed_data_info_tab.html",
            pd_id=pd_id,
            preprocessed_data_id=preprocessed_data_id,
            process_date=process_date,
            filepaths=filepaths,
            is_local_request=is_local_request,
            btn_to_show=btn_to_show,
            show_revert_btn=show_revert_btn,
            allow_approval=allow_approval,
            approval_deny_msg=approval_deny_msg)
