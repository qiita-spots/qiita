# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import dumps, loads
from sys import exc_info
from time import sleep
from os import remove
from os.path import join
import traceback
import warnings

import qiita_db as qdb
from qiita_core.qiita_settings import r_client, qiita_config
from qiita_ware.commands import (download_remote, list_remote,
                                 submit_VAMPS, submit_EBI)
from qiita_ware.metadata_pipeline import (
    create_templates_from_qiime_mapping_file)
from qiita_ware.exceptions import EBISubmissionError


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
        for dtype, biom_fp, archive_artifact_fp in biom_files:
            if archive_artifact_fp is not None:
                files = dumps({'biom': [biom_fp],
                               'plain_text': [archive_artifact_fp]})
            else:
                files = dumps({'biom': [biom_fp]})
            validate_params = qdb.software.Parameters.load(
                cmd, values_dict={'files': files,
                                  'artifact_type': 'BIOM',
                                  'provenance': dumps({'job': job.id,
                                                       'data_type': dtype}),
                                  'analysis': analysis_id,
                                  'template': None})
            val_jobs.append(qdb.processing_job.ProcessingJob.create(
                analysis.owner, validate_params, True))

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


def submit_to_EBI(job):
    """Submit a study to EBI

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job performing the task
    """
    with qdb.sql_connection.TRN:
        param_vals = job.parameters.values
        artifact_id = int(param_vals['artifact'])
        submission_type = param_vals['submission_type']
        artifact = qdb.artifact.Artifact(artifact_id)

        for info in artifact.study._ebi_submission_jobs():
            jid, aid, js, cbste, era = info
            if js in ('running', 'queued') and jid != job.id:
                error_msg = ("Cannot perform parallel EBI submission for "
                             "the same study. Current job running: %s" % js)
                raise EBISubmissionError(error_msg)
        submit_EBI(artifact_id, submission_type, True)
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

        with warnings.catch_warnings(record=True) as warns:
            if is_mapping_file:
                create_templates_from_qiime_mapping_file(fp, study, data_type)
            else:
                qdb.metadata_template.sample_template.SampleTemplate.create(
                    qdb.metadata_template.util.load_template_to_dataframe(fp),
                    study)
            remove(fp)

            if warns:
                msg = '\n'.join(set(str(w) for w in warns))
                r_client.set("sample_template_%s" % study.id,
                             dumps({'job_id': job.id, 'alert_type': 'warning',
                                    'alert_msg': msg}))

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

            # Join all the warning messages into one. Note that this info
            # will be ignored if an exception is raised
            if warns:
                msg = '\n'.join(set(str(w) for w in warns))
                r_client.set("sample_template_%s" % study_id,
                             dumps({'job_id': job.id, 'alert_type': 'warning',
                                    'alert_msg': msg}))

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
                msg = '\n'.join(set(str(w) for w in warns))
                r_client.set("prep_template_%s" % prep_id,
                             dumps({'job_id': job.id, 'alert_type': 'warning',
                                    'alert_msg': msg}))

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
        name = param_vals['name'].split(',')

        if obj_class == 'SampleTemplate':
            constructor = qdb.metadata_template.sample_template.SampleTemplate
        elif obj_class == 'PrepTemplate':
            constructor = qdb.metadata_template.prep_template.PrepTemplate
        else:
            raise ValueError('Unknown value "%s". Choose between '
                             '"SampleTemplate" and "PrepTemplate"' % obj_class)

        if sample_or_col == 'columns':
            del_func = constructor(obj_id).delete_column
            name = name[0]
        elif sample_or_col == 'samples':
            del_func = constructor(obj_id).delete_samples
        else:
            raise ValueError('Unknown value "%s". Choose between "samples" '
                             'and "columns"' % sample_or_col)

        del_func(name)
        job._set_status('success')


def delete_study(job):
    """Deletes a full study

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job performing the task
    """
    MT = qdb.metadata_template
    with qdb.sql_connection.TRN:
        study_id = job.parameters.values['study']
        study = qdb.study.Study(study_id)

        # deleting analyses
        for analysis in study.analyses():
            # selecting roots of the analysis, can be multiple
            artifacts = [a for a in analysis.artifacts
                         if a.processing_parameters is None]
            # deleting each of the processing graphs
            for a in artifacts:
                to_delete = list(a.descendants.nodes())
                to_delete.reverse()
                for td in to_delete:
                    qdb.artifact.Artifact.delete(td.id)
            qdb.analysis.Analysis.delete(analysis.id)

        for pt in study.prep_templates():
            to_delete = list(pt.artifact.descendants.nodes())
            to_delete.reverse()
            for td in to_delete:
                qdb.artifact.Artifact.delete(td.id)
            MT.prep_template.PrepTemplate.delete(pt.id)

        if MT.sample_template.SampleTemplate.exists(study_id):
            MT.sample_template.SampleTemplate.delete(study_id)

        qdb.study.Study.delete(study_id)

        job._set_status('success')


def complete_job(job):
    """Completes a job

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job performing the task
    """
    with qdb.sql_connection.TRN:
        param_vals = job.parameters.values
        payload = loads(param_vals['payload'])
        if payload['success']:
            artifacts = payload['artifacts']
            error = None
        else:
            artifacts = None
            error = payload['error']
        c_job = qdb.processing_job.ProcessingJob(param_vals['job_id'])
        try:
            c_job.complete(payload['success'], artifacts, error)
        except Exception:
            c_job._set_error(traceback.format_exception(*exc_info()))

        job._set_status('success')

    if 'archive' in payload:
        pass
        # ToDo: Archive
        # features = payload['archive']
        # here we should call the method from the command to archive


def delete_analysis(job):
    """Deletes a full analysis

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job performing the task
    """
    with qdb.sql_connection.TRN:
        analysis_id = job.parameters.values['analysis_id']
        analysis = qdb.analysis.Analysis(analysis_id)

        # selecting roots of the analysis, can be multiple
        artifacts = [a for a in analysis.artifacts
                     if a.processing_parameters is None]
        # deleting each of the processing graphs
        for a in artifacts:
            to_delete = list(a.descendants.nodes())
            to_delete.reverse()
            for td in to_delete:
                qdb.artifact.Artifact.delete(td.id)
        qdb.analysis.Analysis.delete(analysis_id)

        r_client.delete('analysis_delete_%d' % analysis_id)

        job._set_status('success')


def list_remote_files(job):
    """Lists valid study files on a remote server

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job performing the task
    """
    with qdb.sql_connection.TRN:
        url = job.parameters.values['url']
        private_key = job.parameters.values['private_key']
        study_id = job.parameters.values['study_id']
        try:
            files = list_remote(url, private_key)
            r_client.set("upload_study_%s" % study_id,
                         dumps({'job_id': job.id, 'url': url, 'files': files}))
        except Exception:
            job._set_error(traceback.format_exception(*exc_info()))
        else:
            job._set_status('success')
        finally:
            # making sure to always delete the key so Qiita never keeps it
            remove(private_key)


def download_remote_files(job):
    """Downloads valid study files from a remote server

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job performing the task
    """
    with qdb.sql_connection.TRN:
        url = job.parameters.values['url']
        destination = job.parameters.values['destination']
        private_key = job.parameters.values['private_key']
        try:
            download_remote(url, private_key, destination)
        except Exception:
            job._set_error(traceback.format_exception(*exc_info()))
        else:
            job._set_status('success')


def INSDC_download(job):
    """Download an accession from INSDC

    Parameters
    ----------
    job : qiita_db.processing_job.ProcessingJob
        The processing job performing the task
    """
    with qdb.sql_connection.TRN:
        param_vals = job.parameters.values
        download_source = param_vals['download_source']
        accession = param_vals['accession']

        if job.user.level != 'admin':
            job._set_error('INSDC_download is only for administrators')

        job_dir = join(qiita_config.working_dir, job.id)
        qdb.util.create_nested_path(job_dir)

        # code doing something
        print(download_source, accession)

        job._set_status('success')


TASK_DICT = {'build_analysis_files': build_analysis_files,
             'release_validators': release_validators,
             'submit_to_VAMPS': submit_to_VAMPS,
             'submit_to_EBI': submit_to_EBI,
             'copy_artifact': copy_artifact,
             'delete_artifact': delete_artifact,
             'create_sample_template': create_sample_template,
             'update_sample_template': update_sample_template,
             'delete_sample_template': delete_sample_template,
             'update_prep_template': update_prep_template,
             'delete_sample_or_column': delete_sample_or_column,
             'delete_study': delete_study,
             'complete_job': complete_job,
             'delete_analysis': delete_analysis,
             'list_remote_files': list_remote_files,
             'download_remote_files': download_remote_files,
             'INSDC_download': INSDC_download}


def private_task(job_id):
    """Completes a Qiita private task

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
    except Exception as e:
        log_msg = "Error on job %s: %s" % (
            job.id, ''.join(traceback.format_exception(*exc_info())))
        le = qdb.logger.LogEntry.create('Runtime', log_msg)
        job.complete(False, error="Error (log id: %d): %s" % (le.id, e))
