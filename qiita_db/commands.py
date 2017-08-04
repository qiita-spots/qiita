# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from functools import partial
from future import standard_library
from json import loads
from sys import exc_info
import traceback

import qiita_db as qdb

with standard_library.hooks():
    from configparser import ConfigParser


SUPPORTED_PARAMS = ['preprocessed_sequence_illumina_params',
                    'preprocessed_sequence_454_params',
                    'processed_params_sortmerna']


def load_study_from_cmd(owner, title, info):
    r"""Adds a study to the database

    Parameters
    ----------
    owner : str
        The email address of the owner of the study_abstract
    title : str
        The title of the study_abstract
    info : file-like object
        File-like object containing study information

    """
    # Parse the configuration file
    config = ConfigParser()
    config.readfp(info)

    optional = dict(config.items('optional'))

    def get_optional(name):
        return optional.get(name, None)

    get_required = partial(config.get, 'required')
    required_fields = ['timeseries_type_id', 'mixs_compliant',
                       'reprocess', 'study_alias',
                       'study_description', 'study_abstract',
                       'metadata_complete', 'principal_investigator']
    optional_fields = ['funding', 'most_recent_contact', 'spatial_series',
                       'number_samples_collected', 'number_samples_promised',
                       'vamps_id', 'study_id']
    infodict = {}
    for value in required_fields:
        infodict[value] = get_required(value)

    for value in optional_fields:
        optvalue = get_optional(value)
        if optvalue is not None:
            infodict[value] = optvalue

    with qdb.sql_connection.TRN:
        emp_person_name_email = get_optional('emp_person_name')
        if emp_person_name_email is not None:
            emp_name, emp_email, emp_affiliation = \
                emp_person_name_email.split(',')
            infodict['emp_person_id'] = qdb.study.StudyPerson.create(
                emp_name.strip(), emp_email.strip(), emp_affiliation.strip())
        lab_name_email = get_optional('lab_person')
        if lab_name_email is not None:
            lab_name, lab_email, lab_affiliation = lab_name_email.split(',')
            infodict['lab_person_id'] = qdb.study.StudyPerson.create(
                lab_name.strip(), lab_email.strip(), lab_affiliation.strip())

        pi_name_email = infodict.pop('principal_investigator')
        pi_name, pi_email, pi_affiliation = pi_name_email.split(',', 2)
        infodict['principal_investigator_id'] = qdb.study.StudyPerson.create(
            pi_name.strip(), pi_email.strip(), pi_affiliation.strip())

        return qdb.study.Study.create(qdb.user.User(owner), title, infodict)


def load_artifact_from_cmd(filepaths, filepath_types, artifact_type,
                           prep_template=None, parents=None,
                           dflt_params_id=None, required_params=None,
                           optional_params=None):
    r"""Adds an artifact to the system

    Parameters
    ----------
    filepaths : iterable of str
        Paths to the artifact files
    filepath_types : iterable of str
        Describes the contents of the files
    artifact_type : str
        The type of artifact
    prep_template : int, optional
        The prep template id
    parents : list of int, optional
        The list of artifacts id of the parent artifacts
    dflt_params_id : int, optional
        The id of the default parameter set used to process the artifact
    required_params : str, optional
        JSON string with the required parameters used to process the artifact
    optional_params : str, optional
        JSON string with the optional parameters used to process the artifact

    Returns
    -------
    qiita_db.artifact.Artifact
        The newly created artifact

    Raises
    ------
    ValueError
        If the lists `filepaths` and `filepath_types` don't have the same
        length
    """
    if len(filepaths) != len(filepath_types):
        raise ValueError("Please provide exactly one filepath_type for each "
                         "and every filepath")
    with qdb.sql_connection.TRN:
        fp_types_dict = qdb.util.get_filepath_types()
        fps = [(fp, fp_types_dict[ftype])
               for fp, ftype in zip(filepaths, filepath_types)]

        if prep_template:
            prep_template = qdb.metadata_template.prep_template.PrepTemplate(
                prep_template)

        if parents:
            if len(parents) > 1 and required_params is None:
                raise ValueError("When you pass more than 1 parent you need "
                                 "to also pass required_params")
            parents = [qdb.artifact.Artifact(pid) for pid in parents]

        params = None
        if dflt_params_id:
            if required_params:
                required_dict = loads(required_params)
            else:
                # if we reach this point we know tha we only have one parent
                required_dict = loads('{"input_data": %d}' % parents[0].id)
            optional_dict = loads(optional_params) if optional_params else None
            params = qdb.software.Parameters.from_default_params(
                qdb.software.DefaultParameters(dflt_params_id),
                required_dict, optional_dict)

        return qdb.artifact.Artifact.create(
            fps, artifact_type, prep_template=prep_template, parents=parents,
            processing_parameters=params)


def load_sample_template_from_cmd(sample_temp_path, study_id):
    r"""Adds a sample template to the database

    Parameters
    ----------
    sample_temp_path : str
        Path to the sample template file
    study_id : int
        The study id to which the sample template belongs
    """
    sample_temp = qdb.metadata_template.util.load_template_to_dataframe(
        sample_temp_path)
    return qdb.metadata_template.sample_template.SampleTemplate.create(
        sample_temp, qdb.study.Study(study_id))


def load_prep_template_from_cmd(prep_temp_path, study_id, data_type):
    r"""Adds a prep template to the database

    Parameters
    ----------
    prep_temp_path : str
        Path to the prep template file
    study_id : int
        The study id to which the prep template belongs
    data_type : str
        The data type of the prep template
    """
    prep_temp = qdb.metadata_template.util.load_template_to_dataframe(
        prep_temp_path)
    return qdb.metadata_template.prep_template.PrepTemplate.create(
        prep_temp, qdb.study.Study(study_id), data_type)


def load_parameters_from_cmd(name, fp, cmd_id):
    """Add a new parameters entry on `table`

    Parameters
    ----------
    fp : str
        The filepath to the parameters file
    cmd_id : int
        The command to add the new default parameter set

    Returns
    -------
    qiita_db.software.DefaultParameters
        The newly parameter set object created

    Raises
    ------
    ValueError
        If the table does not exists on the DB
        If the fp is not correctly formatted

    Notes
    -----
    `fp` should be a tab-delimited text file following this format:
        parameter_1<TAB>value
        parameter_2<TAB>value
        ...
    """
    cmd = qdb.software.Command(cmd_id)

    try:
        params = dict(tuple(l.strip().split('\t')) for l in open(fp, 'U'))
    except ValueError:
        raise ValueError("The format of the parameters files is not correct. "
                         "The format is PARAMETER_NAME<tab>VALUE")

    return qdb.software.DefaultParameters.create(name, cmd, **params)


def update_artifact_from_cmd(filepaths, filepath_types, artifact_id):
    """Updates the artifact `artifact_id` with the given files

    Parameters
    ----------
    filepaths : iterable of str
        Paths to the artifact files
    filepath_types : iterable of str
        Describes the contents of the files
    artifact_id : int
        The id of the artifact to be updated

    Returns
    -------
    qiita_db.artifact.Artifact

    Raises
    ------
    ValueError
        If 'filepaths' and 'filepath_types' do not have the same length
    """
    if len(filepaths) != len(filepath_types):
        raise ValueError("Please provide exactly one filepath_type for each "
                         "and every filepath")
    with qdb.sql_connection.TRN:
        artifact = qdb.artifact.Artifact(artifact_id)
        fp_types_dict = qdb.util.get_filepath_types()
        fps = [(fp, fp_types_dict[ftype])
               for fp, ftype in zip(filepaths, filepath_types)]
        old_fps = artifact.filepaths
        sql = "DELETE FROM qiita.artifact_filepath WHERE artifact_id = %s"
        qdb.sql_connection.TRN.add(sql, [artifact.id])
        qdb.sql_connection.TRN.execute()
        qdb.util.move_filepaths_to_upload_folder(artifact.study.id, old_fps)
        fp_ids = qdb.util.insert_filepaths(
            fps, artifact.id, artifact.artifact_type, "filepath")
        sql = """INSERT INTO qiita.artifact_filepath (artifact_id, filepath_id)
                 VALUES (%s, %s)"""
        sql_args = [[artifact.id, fp_id] for fp_id in fp_ids]
        qdb.sql_connection.TRN.add(sql, sql_args, many=True)
        qdb.sql_connection.TRN.execute()

    return artifact


def complete_job_cmd(job_id, payload):
    """Completes the given job

    Parameters
    ----------
    job_id : str
        The job id
    payload : str
        JSON string with the payload to complete the job
    """
    payload = loads(payload)
    if payload['success']:
        artifacts = payload['artifacts']
        error = None
    else:
        artifacts = None
        error = payload['error']
    job = qdb.processing_job.ProcessingJob(job_id)
    try:
        job.complete(payload['success'], artifacts, error)
    except:
        job._set_error(traceback.format_exception(*exc_info()))
