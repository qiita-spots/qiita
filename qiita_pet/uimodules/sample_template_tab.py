# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.web import UIModule

from qiita_db.study import Study
from qiita_db.user import User
from qiita_db.metadata_template import SampleTemplate
from qiita_db.util import get_files_from_uploads_folders


class SampleTemplateTab(UIModule):
    def render(self, study_id):
        study = Study(int(study_id))

        study_status = study.status
        user = User(self.current_user)
        user_level = user.level
        files = get_files_from_uploads_folders(str(study.id))

        ste = SampleTemplate.exists(study.id)
        if ste:
            sample_templates = SampleTemplate(study.id).get_filepaths()
        else:
            sample_templates = []

        # Check if the request came from a local source
        is_local_request = ('localhost' in self.request.headers['host'] or
                            '127.0.0.1' in self.request.headers['host'])

        return self.render_string(
            "sample_template_tab.html",
            study_status=study_status,
            user_level=user_level,
            files=files,
            study_id=study_id,
            sample_templates=sample_templates,
            is_local_request=is_local_request,
            ste=ste)
