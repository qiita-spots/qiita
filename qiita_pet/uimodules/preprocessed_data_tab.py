# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import UIModule


class PreprocessedDataTab(UIModule):
    def render(self, study_id):
        return self.render_string(
            "preprocessed_data_tab.html",
            available_preprocessed_data=[], study_id=study_id)


class PreprocessedDataInfoTab(UIModule):
    def render(self, study_id, preprocessed_data):
        ppd_id = preprocessed_data.id

        return self.render_string(
            "preprocessed_data_info_tab",
            ppd_id=ppd_id)
