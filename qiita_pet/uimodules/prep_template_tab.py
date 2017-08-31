# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import basename
from collections import defaultdict

from qiita_db.util import get_filepath_types
from qiita_pet.util import STATUS_STYLER
from .base_uimodule import BaseUIModule
from qiita_core.util import execute_as_transaction


filepath_types = [k.split('_', 1)[1].replace('_', ' ')
                  for k in get_filepath_types()
                  if k.startswith('raw_')]
fp_type_by_ft = defaultdict(
    lambda: filepath_types, SFF=['sff'], FASTA=['fasta', 'qual'],
    FASTQ=['barcodes', 'forward seqs', 'reverse seqs'],
    FASTA_Sanger=['fasta'],
    per_sample_FASTQ=['forward seqs', 'reverse seqs'])


@execute_as_transaction
def _get_accessible_raw_data(user):
    """Retrieves a tuple of raw_data_id and one study title for that
    raw_data
    """
    d = {}
    accessible_studies = user.user_studies.union(user.shared_studies)
    for study in accessible_studies:
        study_title = study.title
        for artifact in study.artifacts():
            if artifact.artifact_type in ['SFF', 'FASTQ', 'FASTA',
                                          'FASTA_Sanger' 'per_sample_FASTQ']:
                d[int(artifact.id)] = study_title
    return d


@execute_as_transaction
def _template_generator(study, full_access):
    """Generates tuples of prep template information

    Parameters
    ----------
    study : Study
        The study to get all the prep templates
    full_access : boolean
        A boolean that indicates if the user has full access to the study

    Returns
    -------
    Generator of tuples of (int, str, PrepTemplate, (str, str, str))
        Each tuple contains the prep template id, the prep template data_type
        the PrepTemplate object and a tuple with 3 strings for the style of
        the prep template status icons
    """
    for pt in sorted(study.prep_templates()):
        if full_access or pt.status == 'public':
            yield (pt.id, pt.data_type(), pt, STATUS_STYLER[pt.status],
                   pt.is_submitted_to_ebi)


class RawDataInfoDiv(BaseUIModule):
    @execute_as_transaction
    def render(self, rd, prep_template, study, files):
        raw_data_files = [(basename(fp), fp_type[4:])
                          for _, fp, fp_type in rd.filepaths]
        filetype = rd.artifact_type
        fp_types = fp_type_by_ft[filetype]

        show_buttons = rd.study.status == 'sandbox'

        return self.render_string(
            "study_description_templates/raw_data_info.html",
            rd_id=rd.id,
            rd_filetype=filetype,
            raw_data_files=raw_data_files,
            prep_template_id=prep_template.id,
            files=files,
            filepath_types=fp_types,
            show_buttons=show_buttons)


class EditInvestigationType(BaseUIModule):
    @execute_as_transaction
    def render(self, ena_terms, user_defined_terms, prep_id, inv_type, ppd_id):
        return self.render_string(
            "study_description_templates/edit_investigation_type.html",
            ena_terms=ena_terms,
            user_defined_terms=user_defined_terms,
            prep_id=prep_id,
            investigation_type=inv_type,
            ppd_id=ppd_id)
