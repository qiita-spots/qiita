# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from functools import partial

from tornado.web import UIModule

from qiita_db.study import StudyPerson
from qiita_pet.util import linkify


study_person_linkifier = partial(
    linkify, "<a target=\"_blank\" href=\"mailto:{0}\">{1}</a>")
pubmed_linkifier = partial(
    linkify, "<a target=\"_blank\" href=\"http://www.ncbi.nlm.nih.gov/"
    "pubmed/{0}\">{0}</a>")


class StudyInformationTab(UIModule):
    def render(self, study):
        study_info = study.info
        abstract = study_info['study_abstract']
        description = study_info['study_description']
        pmids = ", ".join([pubmed_linkifier([pmid]) for pmid in study.pmids])
        princ_inv = StudyPerson(study_info['principal_investigator_id'])
        pi_link = study_person_linkifier((princ_inv.email, princ_inv.name))
        number_samples_promised = study_info['number_samples_promised']
        number_samples_collected = study_info['number_samples_collected']
        metadata_complete = study_info['metadata_complete']

        return self.render_string(
            "study_information_tab.html", abstract=abstract,
            description=description,
            pmids=pmids,
            principal_investigator=pi_link,
            number_samples_promised=number_samples_promised,
            number_samples_collected=number_samples_collected,
            metadata_complete=metadata_complete)
