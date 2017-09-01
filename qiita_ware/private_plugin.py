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
from os import remove

import qiita_db as qdb
from qiita_ware.commands import submit_VAMPS, submit_EBI
from qiita_ware.metadata_pipeline import (
    create_templates_from_qiime_mapping_file)


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


def delete_artifact(job):
    """Deletes an artifact from the system

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job performing the task
    """
    with qdb.sql_connection.TRN:
        artifact_id = job.parameters.values['artifact']
        qdb.artifact.Artifact.delete(artifact_id)
        job._set_status('success')


def create_sample_template(job):
    """Creates a sample template

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job performing the task

    """
    with qdb.sql_connection.TRN:
        params = job.parameters.values
        fp = params['fp']
        study = qdb.study.Study(int(params['study_id']))
        is_mapping_file = params['is_mapping_file']
        data_type = params['data_type']

        if is_mapping_file:
            create_templates_from_qiime_mapping_file(fp, study, data_type)
        else:
            qdb.metadata_template.sample_template.SampleTemplate.create(
                qdb.metadata_template.util.load_template_to_dataframe(fp),
                study)
        remove(fp)

        job._set_status('success')


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
