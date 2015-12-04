# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from qiita_core.util import execute_as_transaction
from qiita_db.study import Study
from qiita_db.ontology import Ontology
from qiita_db.software import Command
from qiita_db.util import convert_to_id
from qiita_pet.util import convert_text_html
from .base_uimodule import BaseUIModule
from qiita_pet.util import (generate_param_str, STATUS_STYLER,
                            is_localhost, EBI_LINKIFIER)


class PreprocessedDataTab(BaseUIModule):
    @execute_as_transaction
    def render(self, study, full_access):
        # currently all preprocess data are 'Demultiplexed'
        ppd_gen = [ar for ar in study.artifacts()
                   if ar.artifact_type == 'Demultiplexed']
        avail_ppd = [(ppd, STATUS_STYLER[ppd.visibility],
                      ppd.is_submitted_to_ebi) for ppd in ppd_gen
                     if full_access or ppd.visibility == 'public']
        return self.render_string(
            "study_description_templates/preprocessed_data_tab.html",
            available_preprocessed_data=avail_ppd,
            study_id=study.id)


class PreprocessedDataInfoTab(BaseUIModule):
    @execute_as_transaction
    def render(self, study_id, preprocessed_data):
        user = self.current_user
        ppd_id = preprocessed_data.id
        vamps_status = preprocessed_data.is_submitted_to_vamps
        filepaths = preprocessed_data.filepaths
        is_local_request = is_localhost(self.request.headers['host'])
        show_ebi_btn = user.level == "admin"
        processing_status = convert_text_html('TODO: plugin')
        processed_data = sorted([pd.id for pd in preprocessed_data.children])

        # Get all the ENA terms for the investigation type
        ontology = Ontology(convert_to_id('ENA', 'ontology'))
        # make "Other" show at the bottom of the drop down menu
        ena_terms = []
        for v in sorted(ontology.terms):
            if v != 'Other':
                ena_terms.append('<option value="%s">%s</option>' % (v, v))
        ena_terms.append('<option value="Other">Other</option>')

        # New Type is for users to add a new user-defined investigation type
        user_defined_terms = ontology.user_defined_terms + ['New Type']

        # ppd can only have 1 prep template
        prep_template = preprocessed_data.prep_templates[0]
        # this block might seem wrong but is here due to a possible
        # pathological case that we used to have in the system: preprocessed
        # data without valid prep_templates
        prep_templates = preprocessed_data.prep_templates
        if len(prep_templates == 1):
            prep_template_id = prep_template.id
            raw_data_id = prep_template.artifact.id
            inv_type = prep_template.investigation_type or "None selected"
        else:
            prep_template_id = None
            raw_data_id = None
            inv_type = "None Selected"

        process_params = {param.id: (generate_param_str(param), param.name)
                          for param in Command(3).default_parameter_sets}
        # We just need to provide an ID for the default parameters,
        # so we can initialize the interface
        default_params = 1

        ebi_link = None
        if preprocessed_data.is_submitted_to_ebi:
            ebi_link = EBI_LINKIFIER.format(
                Study(study_id).ebi_study_accession)

        return self.render_string(
            "study_description_templates/preprocessed_data_info_tab.html",
            ppd_id=ppd_id,
            show_ebi_btn=show_ebi_btn,
            filepaths=filepaths,
            is_local_request=is_local_request,
            prep_template_id=prep_template_id,
            raw_data_id=raw_data_id,
            inv_type=inv_type,
            ena_terms=ena_terms,
            vamps_status=vamps_status,
            user_defined_terms=user_defined_terms,
            process_params=process_params,
            default_params=default_params,
            study_id=preprocessed_data.study,
            processing_status=processing_status,
            processed_data=processed_data,
            ebi_link=ebi_link)
