# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import dumps
from sys import exc_info
from time import sleep
import traceback

import qiita_db as qdb
from qiita_ware.commands import submit_VAMPS, submit_EBI


def build_analysis_files(job):
    """Builds the files for an analysis

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job with the information for building the files
    """
    with qdb.sql_connection.TRN:
        params = job.parameters.values
        analysis_id = params['analysis']
        merge_duplicated_sample_ids = params['merge_dup_sample_ids']
        analysis = qdb.analysis.Analysis(analysis_id)
        biom_files = analysis.build_files(merge_duplicated_sample_ids)

        cmd = qdb.software.Command.get_validator('BIOM')
        val_jobs = []
        for dtype, biom_fp in biom_files:
            validate_params = qdb.software.Parameters.load(
                cmd, values_dict={'files': dumps({'biom': [biom_fp]}),
                                  'artifact_type': 'BIOM',
                                  'provenance': dumps({'job': job.id,
                                                       'data_type': dtype}),
                                  'analysis': analysis_id})
            val_jobs.append(qdb.processing_job.ProcessingJob.create(
                analysis.owner, validate_params))

        job._set_validator_jobs(val_jobs)

        for j in val_jobs:
            j.submit()
            sleep(1)

    # The validator jobs no longer finish the job automatically so we need
    # to release the validators here
    job.release_validators()


def release_validators(job):
    """Waits until all the validators of a job are completed

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job with the information of the parent job
    """
    with qdb.sql_connection.TRN:
        qdb.processing_job.ProcessingJob(
            job.parameters.values['job']).release_validators()
        job._set_status('success')


def submit_to_VAMPS(job):
    """Submits an artifact to VAMPS

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job performing the task
    """
    with qdb.sql_connection.TRN:
        submit_VAMPS(job.parameters.values['artifact'])
        job._set_status('success')


def copy_artifact(job):
    """Creates a copy of an artifact

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job performing the task
    """
    with qdb.sql_connection.TRN:
        param_vals = job.parameters.values
        orig_artifact = qdb.artifact.Artifact(param_vals['artifact'])
        prep_template = qdb.metadata_template.prep_template.PrepTemplate(
            param_vals['prep_template'])
        qdb.artifact.Artifact.copy(orig_artifact, prep_template)
        job._set_status('success')


def submit_to_ebi(preprocessed_data_id, submission_type):
    """Submit a study to EBI"""
    submit_EBI(preprocessed_data_id, submission_type, True)


def delete_artifact(artifact_id):
    """Deletes an artifact from the system

    Parameters
    ----------
    artifact_id : int
        The artifact to delete

    Returns
    -------
    dict of {str: str}
        A dict of the form {'status': str, 'message': str}
    """
    from qiita_db.artifact import Artifact

    status = 'success'
    msg = ''
    try:
        Artifact.delete(artifact_id)
    except Exception as e:
        status = 'danger'
        msg = str(e)

    return {'status': status, 'message': msg}


def create_sample_template(fp, study, is_mapping_file, data_type=None):
    """Creates a sample template

    Parameters
    ----------
    fp : str
        The file path to the template file
    study : qiita_db.study.Study
        The study to add the sample template to
    is_mapping_file : bool
        Whether `fp` contains a mapping file or a sample template
    data_type : str, optional
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

    return {'status': status, 'message': msg.decode('utf-8', 'replace')}


TASK_DICT = {
    'build_analysis_files': build_analysis_files,
    'release_validators': release_validators,
    'submit_to_VAMPS': submit_to_VAMPS,
    'copy_artifact': copy_artifact,
    'submit_to_ebi': submit_to_ebi,
    'delete_artifact': delete_artifact,
    'create_sample_template': create_sample_template,
}


def private_task(job_id):
    """Complets a Qiita private task

    Parameters
    ----------
    job_id : str
        The job id
    """
    if job_id == 'register':
        # We don't need to do anything here if Qiita is registering plugins
        return

    job = qdb.processing_job.ProcessingJob(job_id)
    job.update_heartbeat_state()
    task_name = job.command.name

    try:
        TASK_DICT[task_name](job)
    except Exception:
        job.complete(False, error="Error executing private task: %s"
                                  % traceback.format_exception(*exc_info()))
