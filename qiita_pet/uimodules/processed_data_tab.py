# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from qiita_db.data import ProcessedData
from .base_uimodule import BaseUIModule


class ProcessedDataTab(BaseUIModule):
    def render(self, study):
        avail_pd = [(pd_id, ProcessedData(pd_id))
                    for pd_id in study.processed_data()]
        return self.render_string(
            "study_description_templates/processed_data_tab.html",
            available_processed_data=avail_pd,
            study_id=study.id)


class ProcessedDataInfoTab(BaseUIModule):
    def render(self, study_id, processed_data):
        pd_id = processed_data.id
        preprocessed_data_id = processed_data.preprocessed_data
        process_date = processed_data.processed_date
        filepaths = processed_data.get_filepaths()
        is_local_request = self._is_local()

        return self.render_string(
            "study_description_templates/processed_data_info_tab.html",
            pd_id=pd_id,
            preprocessed_data_id=preprocessed_data_id,
            process_date=process_date,
            filepaths=filepaths,
            is_local_request=is_local_request)
