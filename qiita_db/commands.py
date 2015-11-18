# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os import remove
from os.path import join, exists
from functools import partial
from future import standard_library
from future.utils import viewitems
from collections import defaultdict
from shutil import move

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
                       'metadata_complete', 'efo_ids',
                       'principal_investigator']
    optional_fields = ['funding', 'most_recent_contact', 'spatial_series',
                       'number_samples_collected', 'number_samples_promised',
                       'vamps_id', 'study_id']
    infodict = {}
    for value in required_fields:
        infodict[value] = get_required(value)

    # this will eventually change to using the Experimental Factory Ontolgoy
    # names
    efo_ids = infodict.pop('efo_ids')
    efo_ids = [x.strip() for x in efo_ids.split(',')]

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

        return qdb.study.Study.create(
            qdb.user.User(owner), title, efo_ids, infodict)


def load_artifact_from_cmd(filepaths, filepath_types, artifact_type,
                           prep_template=None, parents=None,
                           processing_command_id=None,
                           processing_parameters_id=None,
                           can_be_submitted_to_ebi=False,
                           can_be_submitted_to_vamps=False):
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
    processing_command_id : int, optional
        The id of the command used to process the artifact
    processing_parameters_id : int, optional
        The id of the parameter set used to process the artifact
    can_be_submitted_to_ebi : bool, optional
        Whether the artifact can be submitted to EBI or not
    can_be_submitted_to_vamps : bool, optional
        Whether the artifact can be submitted to VAMPS or not

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
            parents = [qdb.artifact.Artifact(pid) for pid in parents]

        params = None
        if processing_command_id:
            params = qdb.software.Parameters(
                processing_parameters_id,
                qdb.software.Command(processing_command_id))

        return qdb.artifact.Artifact.create(
            fps, artifact_type, prep_template=prep_template, parents=parents,
            processing_parameters=params,
            can_be_submitted_to_ebi=can_be_submitted_to_ebi,
            can_be_submitted_to_vamps=can_be_submitted_to_vamps)


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


def load_parameters_from_cmd(name, fp, table):
    """Add a new parameters entry on `table`

    Parameters
    ----------
    fp : str
        The filepath to the parameters file
    table : str
        The name of the table to add the parameters

    Returns
    -------
    qiita_db.BaseParameters
        The newly `qiita_db.BaseParameters` object

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
    if table not in SUPPORTED_PARAMS:
        raise ValueError("Table %s not supported. Choose from: %s"
                         % (table, ', '.join(SUPPORTED_PARAMS)))

    # Build the dictionary to get the parameter constructor
    constructor_dict = {}
    constructor_dict['preprocessed_sequence_illumina_params'] = \
        qdb.parameters.PreprocessedIlluminaParams
    constructor_dict['preprocessed_sequence_454_params'] = \
        qdb.parameters.Preprocessed454Params
    constructor_dict['processed_params_sortmerna'] = \
        qdb.parameters.ProcessedSortmernaParams

    constructor = constructor_dict[table]

    try:
        params = dict(tuple(l.strip().split('\t')) for l in open(fp, 'U'))
    except ValueError:
        raise ValueError("The format of the parameters files is not correct. "
                         "The format is PARAMETER_NAME<tab>VALUE")

    return constructor.create(name, **params)


def update_raw_data_from_cmd(filepaths, filepath_types, study_id, rd_id=None):
    """Updates the raw data of the study 'study_id'

    Parameters
    ----------
    filepaths : iterable of str
        Paths to the raw data files
    filepath_types : iterable of str
        Describes the contents of the files
    study_id : int
        The study_id of the study to be updated
    rd_id : int, optional
        The id of the raw data to be updated. If not provided, the raw data
        with lowest id in the study will be updated

    Returns
    -------
    qiita_db.data.RawData

    Raises
    ------
    ValueError
        If 'filepaths' and 'filepath_types' do not have the same length
        If the study does not have any raw data
        If rd_id is provided and it does not belong to the given study
    """
    if len(filepaths) != len(filepath_types):
        raise ValueError("Please provide exactly one filepath_type for each "
                         "and every filepath")
    with qdb.sql_connection.TRN:
        study = qdb.study.Study(study_id)
        raw_data_ids = study.raw_data()
        if not raw_data_ids:
            raise ValueError("Study %d does not have any raw data" % study_id)

        if rd_id:
            if rd_id not in raw_data_ids:
                raise ValueError(
                    "The raw data %d does not exist in the study %d. Available"
                    " raw data: %s"
                    % (rd_id, study_id, ', '.join(map(str, raw_data_ids))))
            raw_data = qdb.data.RawData(rd_id)
        else:
            raw_data = qdb.data.RawData(sorted(raw_data_ids)[0])

        filepath_types_dict = qdb.util.get_filepath_types()
        try:
            filepath_types = [filepath_types_dict[x] for x in filepath_types]
        except KeyError:
            supported_types = filepath_types_dict.keys()
            unsupported_types = set(filepath_types).difference(supported_types)
            raise ValueError(
                "Some filepath types provided are not recognized (%s). "
                "Please choose from: %s"
                % (', '.join(unsupported_types), ', '.join(supported_types)))

        fps = raw_data.get_filepaths()
        sql = "DELETE FROM qiita.raw_filepath WHERE raw_data_id = %s"
        qdb.sql_connection.TRN.add(sql, [raw_data.id])
        qdb.sql_connection.TRN.execute()
        qdb.util.move_filepaths_to_upload_folder(study_id, fps)

        raw_data.add_filepaths(list(zip(filepaths, filepath_types)))

    return raw_data


def update_preprocessed_data_from_cmd(sl_out_dir, study_id, ppd_id=None):
    """Updates the preprocessed data of the study 'study_id'

    Parameters
    ----------
    sl_out_dir : str
        The path to the split libraries output directory
    study_id : int
        The study_id of the study to be updated
    ppd_id : int, optional
        The id of the preprocessed_data to be updated. If not provided, the
        preprocessed data with the lowest id in the study will be updated.

    Returns
    -------
    qiita_db.PreprocessedData
        The updated preprocessed data

    Raises
    ------
    IOError
        If sl_out_dir does not contain all the required files
    ValueError
        If the study does not have any preprocessed data
        If ppd_id is provided and it does not belong to the given study
    """
    # Check that we have all the required files
    path_builder = partial(join, sl_out_dir)
    new_fps = {'preprocessed_fasta': path_builder('seqs.fna'),
               'preprocessed_fastq': path_builder('seqs.fastq'),
               'preprocessed_demux': path_builder('seqs.demux'),
               'log': path_builder('split_library_log.txt')}

    missing_files = [key for key, val in viewitems(new_fps) if not exists(val)]
    if missing_files:
        raise IOError(
            "The directory %s does not contain the following required files: "
            "%s" % (sl_out_dir, ', '.join(missing_files)))

    # Get the preprocessed data to be updated
    with qdb.sql_connection.TRN:
        study = qdb.study.Study(study_id)
        ppds = study.preprocessed_data()
        if not ppds:
            raise ValueError("Study %s does not have any preprocessed data",
                             study_id)

        if ppd_id:
            if ppd_id not in ppds:
                raise ValueError(
                    "The preprocessed data %d does not exist in "
                    "study %d. Available preprocessed data: %s"
                    % (ppd_id, study_id, ', '.join(map(str, ppds))))
            ppd = qdb.data.PreprocessedData(ppd_id)
        else:
            ppd = qdb.data.PreprocessedData(sorted(ppds)[0])

        # We need to loop through the fps list to get the db filepaths that we
        # need to modify
        fps = defaultdict(list)
        for fp_id, fp, fp_type in sorted(ppd.get_filepaths()):
            fps[fp_type].append((fp_id, fp))

        fps_to_add = []
        fps_to_modify = []
        keys = ['preprocessed_fasta', 'preprocessed_fastq',
                'preprocessed_demux', 'log']

        for key in keys:
            if key in fps:
                db_id, db_fp = fps[key][0]
                fp_checksum = qdb.util.compute_checksum(new_fps[key])
                fps_to_modify.append((db_id, db_fp, new_fps[key], fp_checksum))
            else:
                fps_to_add.append(
                    (new_fps[key],
                     qdb.util.convert_to_id(key, 'filepath_type')))

        # Insert the new files in the database, if any
        if fps_to_add:
            ppd.add_filepaths(fps_to_add)

        sql = "UPDATE qiita.filepath SET checksum=%s WHERE filepath_id=%s"
        for db_id, db_fp, new_fp, checksum in fps_to_modify:
            # Move the db_file in case something goes wrong
            bkp_fp = "%s.bkp" % db_fp
            move(db_fp, bkp_fp)

            # Start the update for the current file
            # Move the file to the database location
            move(new_fp, db_fp)
            # Add the SQL instruction to the DB
            qdb.sql_connection.TRN.add(sql, [checksum, db_id])

            # In case that a rollback occurs, we need to restore the files
            qdb.sql_connection.TRN.add_post_rollback_func(move, bkp_fp, db_fp)
            # In case of commit, we can remove the backup files
            qdb.sql_connection.TRN.add_post_commit_func(remove, bkp_fp)

        qdb.sql_connection.TRN.execute()

        return ppd
