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
from os import remove
import traceback
import warnings

import qiita_db as qdb
from qiita_ware.commands import submit_VAMPS


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


def update_sample_template(job):
    """Updates a sample template

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job performing the task
    """
    with qdb.sql_connection.TRN:
        param_vals = job.parameters.values
        study_id = param_vals['study']
        fp = param_vals['template_fp']
        with warnings.catch_warnings(record=True) as warns:
            st = qdb.metadata_template.sample_template.SampleTemplate(study_id)
            df = qdb.metadata_template.util.load_template_to_dataframe(fp)
            st.extend_and_update(df)
            remove(fp)

            # Join all the warning messages into one.NOte that this info
            # will be ignored if an exception is raised
            if warns:
                msg = '\n'.join(set(str(w.message) for w in warns))

        job._set_status('success')


def delete_sample_template(job):
    """Deletes a sample template

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job performing the task
    """
    with qdb.sql_connection.TRN:
        qdb.metadata_template.sample_template.SampleTemplate.delete(
            job.parameters.values['study'])
        job._set_status('success')


def update_prep_template(job):
    """Updates a prep template

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job performing the task
    """
    with qdb.sql_connection.TRN:
        param_vals = job.parameters.values
        prep_id = param_vals['prep_template']
        fp = param_vals['template_fp']

        prep = qdb.metadata_template.prep_template.PrepTemplate(prep_id)
        with warnings.catch_warnings(record=True) as warns:
            df = qdb.metadata_template.util.load_template_to_dataframe(fp)
            prep.extend_and_update(df)
            remove(fp)

            # Join all the warning messages into one. Note that this info
            # will be ignored if an exception is raised
            if warns:
                msg = '\n'.join(set(str(w.message) for w in warns))

        job._set_status('success')


def delete_sample_or_column(job):
    """Deletes a sample or a column from the metadata

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job performing the task
    """
    with qdb.sql_connection.TRN:
        param_vals = job.parameters.values
        obj_class = param_vals['obj_class']
        obj_id = param_vals['obj_id']
        sample_or_col = param_vals['sample_or_col']
        name = param_vals['name']

        if obj_class == 'SampleTemplate':
            constructor = qdb.metadata_template.sample_template.SampleTemplate
        elif obj_class == 'PrepTemplate':
            constructor = qdb.metadata_template.prep_template.PrepTemplate
        else:
            raise ValueError('Unknown value "%s". Choose between '
                             '"SampleTemplate" and "PrepTemplate"' % obj_class)

        if sample_or_col == 'columns':
            del_func = constructor(obj_id).delete_column
        elif sample_or_col == 'samples':
            del_func = constructor(obj_id).delete_sample
        else:
            raise ValueError('Unknown value "%s". Choose between "samples" '
                             'and "columns"' % sample_or_col)

        del_func(name)
        job._set_status('success')

TASK_DICT = {'build_analysis_files': build_analysis_files,
             'release_validators': release_validators,
             'submit_to_VAMPS': submit_to_VAMPS,
             'copy_artifact': copy_artifact,
             'update_sample_template': update_sample_template,
             'delete_sample_template': delete_sample_template,
             'update_prep_template': update_prep_template,
             'delete_sample_or_column': delete_sample_or_column}


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
