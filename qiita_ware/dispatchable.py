# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from .analysis_pipeline import RunAnalysis
from qiita_ware.commands import submit_EBI, submit_VAMPS
from qiita_db.analysis import Analysis
from qiita_db.artifact import Artifact


def submit_to_ebi(preprocessed_data_id, submission_type):
    """Submit a study to EBI"""
    submit_EBI(preprocessed_data_id, submission_type, True)


def submit_to_VAMPS(preprocessed_data_id):
    """Submit a study to VAMPS"""
    return submit_VAMPS(preprocessed_data_id)


def run_analysis(analysis_id, commands, comm_opts=None,
                 rarefaction_depth=None, merge_duplicated_sample_ids=False,
                 **kwargs):
    """Run an analysis"""
    analysis = Analysis(analysis_id)
    ar = RunAnalysis(**kwargs)
    return ar(analysis, commands, comm_opts, rarefaction_depth,
              merge_duplicated_sample_ids)


def create_raw_data(filetype, prep_template, filepaths):
    """Creates a new raw data

    Needs to be dispachable because it moves large files
    """
    Artifact.create(filepaths, filetype, prep_template=prep_template)


def copy_raw_data(prep_template, artifact_id):
    """Creates a new raw data by copying from artifact_id"""
    Artifact.copy(Artifact(artifact_id), prep_template)


def create_sample_template(fp, study, is_mapping_file, data_type):
    """Creates a sample template

    Parameters
    ----------
    fp : str
        The file path to the template file
    study : qiita_db.study.Study
        The study to add the sample template to
    is_mapping_file : bool
        Whether `fp` contains a mapping file or a sample template
    data_type : str
        If `is_mapping_file` is True, the data type of the prep template to be
        created

    Returns
    -------
    dict of {str: str}
        A dict of the form {'status': str, 'message': str}
    """
    # The imports need to be in here because this code is executed in
    # the ipython workers
    import warnings
    from os import remove
    from qiita_db.metadata_template.sample_template import SampleTemplate
    from qiita_db.metadata_template.util import load_template_to_dataframe
    from qiita_ware.metadata_pipeline import (
        create_templates_from_qiime_mapping_file)

    status = 'success'
    msg = ''
    try:
        with warnings.catch_warnings(record=True) as warns:
            if is_mapping_file:
                create_templates_from_qiime_mapping_file(fp, study,
                                                         data_type)
            else:
                SampleTemplate.create(load_template_to_dataframe(fp),
                                      study)
            remove(fp)

            # join all the warning messages into one. Note that this
            # info will be ignored if an exception is raised
            if warns:
                msg = '\n'.join(set(str(w.message) for w in warns))
                status = 'warning'
    except Exception as e:
        # Some error occurred while processing the sample template
        # Show the error to the user so they can fix the template
        status = 'danger'
        msg = str(e)

    return {'status': status, 'message': msg}


def update_sample_template(study_id, fp):
    """Updates a sample template

    Parameters
    ----------
    study_id : int
        Study id whose template is going to be updated
    fp : str
        The file path to the template file

    Returns
    -------
    dict of {str: str}
        A dict of the form {'status': str, 'message': str}
    """
    import warnings
    from os import remove
    from qiita_db.metadata_template.util import load_template_to_dataframe
    from qiita_db.metadata_template.sample_template import SampleTemplate

    msg = ''
    status = 'success'

    try:
        with warnings.catch_warnings(record=True) as warns:
            # deleting previous uploads and inserting new one
            st = SampleTemplate(study_id)
            df = load_template_to_dataframe(fp)
            st.extend(df)
            st.update(df)
            remove(fp)

            # join all the warning messages into one. Note that this info
            # will be ignored if an exception is raised
            if warns:
                msg = '\n'.join(set(str(w.message) for w in warns))
                status = 'warning'
    except Exception as e:
            status = 'danger'
            msg = str(e)

    return {'status': status, 'message': msg}


def delete_sample_template(study_id):
    """Delete a sample template

    Parameters
    ----------
    study_id : int
        Study id whose template is going to be deleted

    Returns
    -------
    dict of {str: str}
        A dict of the form {'status': str, 'message': str}
    """
    from qiita_db.metadata_template.sample_template import SampleTemplate

    msg = ''
    status = 'success'
    try:
        SampleTemplate.delete(study_id)
    except Exception as e:
        status = 'danger'
        msg = str(e)

    return {'status': status, 'message': msg}
