# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from functools import partial
from operator import itemgetter

from future.utils import viewitems

from qiita_core.util import execute_as_transaction
from qiita_db.util import get_files_from_uploads_folders, get_data_types
from qiita_db.study import StudyPerson
from qiita_db.metadata_template import SampleTemplate
from qiita_pet.util import linkify, is_local_connection
from .base_uimodule import BaseUIModule


study_person_linkifier = partial(
    linkify, "<a target=\"_blank\" href=\"mailto:{0}\">{1}</a>")
pubmed_linkifier = partial(
    linkify, "<a target=\"_blank\" href=\"http://www.ncbi.nlm.nih.gov/"
    "pubmed/{0}\">{0}</a>")


class StudyInformationTab(BaseUIModule):
    @execute_as_transaction
    def render(self, study):
        study_info = study.info
        id = study.id
        abstract = study_info['study_abstract']
        description = study_info['study_description']
        pmids = ", ".join([pubmed_linkifier([pmid]) for pmid in study.pmids])
        princ_inv = StudyPerson(study_info['principal_investigator_id'])
        pi_link = study_person_linkifier((princ_inv.email, princ_inv.name))
        number_samples_promised = study_info['number_samples_promised']
        number_samples_collected = study_info['number_samples_collected']
        metadata_complete = study_info['metadata_complete']
        data_types = sorted(viewitems(get_data_types()), key=itemgetter(1))

        # Retrieve the files from the uploads folder, so the user can choose
        # the sample template of the study. Filter them to only include the
        # ones that ends with 'txt' or 'tsv'.
        files = [f for _, f in get_files_from_uploads_folders(str(study.id))
                 if f.endswith(('txt', 'tsv'))]

        # If the sample template exists, retrieve all its filepaths
        if SampleTemplate.exists(study.id):
            sample_templates = SampleTemplate(study.id).get_filepaths()
        else:
            # If the sample template does not exist, just pass an empty list
            sample_templates = []

        # Check if the request came from a local source
        is_local_request = is_local_connection(self.request.headers['host'])

        # The user can choose the sample template only if the study is
        # sandboxed or the current user is an admin
        show_select_sample = (
            study.status == 'sandbox' or self.current_user.level == 'admin')

        return self.render_string(
            "study_description_templates/study_information_tab.html",
            abstract=abstract,
            description=description,
            id=id,
            pmids=pmids,
            principal_investigator=pi_link,
            number_samples_promised=number_samples_promised,
            number_samples_collected=number_samples_collected,
            metadata_complete=metadata_complete,
            show_select_sample=show_select_sample,
            files=files,
            study_id=study.id,
            sample_templates=sample_templates,
            is_local_request=is_local_request,
            data_types=data_types)
