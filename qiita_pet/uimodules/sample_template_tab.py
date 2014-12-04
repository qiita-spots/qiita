# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import UIModule

from qiita_db.user import User
from qiita_db.metadata_template import SampleTemplate
from qiita_db.util import get_files_from_uploads_folders


class SampleTemplateTab(UIModule):
    def render(self, study):
        # Retrieve the files from the uploads folder, so the user can choose
        # the sample template of the study
        files = get_files_from_uploads_folders(str(study.id))

        # If the sample template exists, retrieve all its filepaths
        if SampleTemplate.exists(study.id):
            sample_templates = SampleTemplate(study.id).get_filepaths()
        else:
            # If the sample template does not exist, just pass an empty list
            sample_templates = []

        # Check if the request came from a local source
        is_local_request = ('localhost' in self.request.headers['host'] or
                            '127.0.0.1' in self.request.headers['host'])

        # The user can choose the sample template only if the study is
        # sandboxed or the current user is an admin
        show_select_sample = (study.status == 'sandbox'
                              or User(self.current_user).level == 'admin')

        return self.render_string(
            "sample_template_tab.html",
            show_select_sample=show_select_sample,
            files=files,
            study_id=study.id,
            sample_templates=sample_templates,
            is_local_request=is_local_request)
