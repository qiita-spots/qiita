# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

# The code is commented with details on the changes implemented here,
# but here is an overview of the changes needed to transfer the analysis
# data to the plugins structure:
# 1) Create a new type plugin to define the diversity types
# 2) Create the new commands on the existing QIIME plugin to execute the
#    existing analyses (beta div, taxa summaries and alpha rarefaction)
# 3) Transfer all the data in the old structures to the plugin structures
# 4) Delete old structures

from string import ascii_letters, digits
from random import SystemRandom
from os.path import join, exists, basename
from os import makedirs
from json import loads

from biom import load_table, Table
from biom.util import biom_open

from qiita_db.sql_connection import TRN
from qiita_db.util import (get_db_files_base_dir, purge_filepaths,
                           get_mountpoint, compute_checksum)
from qiita_db.artifact import Artifact

# Create some aux functions that are going to make the code more modular
# and easier to understand, since there is a fair amount of work to do to
# trasnfer the data from the old structure to the new one


def get_random_string(length):
    """Creates a random string of the given length with alphanumeric chars

    Parameters
    ----------
    length : int
        The desired length of the string

    Returns
    -------
    str
        The new random string
    """
    sr = SystemRandom()
    chars = ascii_letters + digits
    return ''.join(sr.choice(chars) for i in range(length))


def create_non_rarefied_biom_artifact(analysis, biom_data, rarefied_table):
    """Creates the initial non-rarefied BIOM artifact of the analysis

    Parameters
    ----------
    analysis : dict
        Dictionary with the analysis information
    biom_data : dict
        Dictionary with the biom file information
    rarefied_table : biom.Table
        The rarefied BIOM table

    Returns
    -------
    int
        The id of the new artifact
    """
    # The non rarefied biom artifact is the initial biom table of the analysis.
    # This table does not currently exist anywhere, so we need to actually
    # create the BIOM file. To create this BIOM file we need: (1) the samples
    # and artifacts they come from and (2) whether the samples where
    # renamed or not. (1) is on the database, but we need to inferr (2) from
    # the existing rarefied BIOM table. Fun, fun...

    with TRN:
        # Get the samples included in the BIOM table grouped by artifact id
        # Note that the analysis contains a BIOM table per data type included
        # in it, and the table analysis_sample does not differentiate between
        # datatypes, so we need to check the data type in the artifact table
        sql = """SELECT artifact_id, array_agg(sample_id)
                 FROM qiita.analysis_sample
                    JOIN qiita.artifact USING (artifact_id)
                 WHERE analysis_id = %s AND data_type_id = %s
                 GROUP BY artifact_id"""
        TRN.add(sql, [analysis['analysis_id'], biom_data['data_type_id']])
        samples_by_artifact = TRN.execute_fetchindex()

        # Create an empty BIOM table to be the new master table
        new_table = Table([], [], [])
        ids_map = {}
        for a_id, samples in samples_by_artifact:
            # Get the filepath of the BIOM table from the artifact
            artifact = Artifact(a_id)
            biom_fp = None
            for x in artifact.filepaths:
                if x['fp_type'] == 'biom':
                    biom_fp = x['fp']
            # Note that we are sure that the biom table exists for sure, so
            # no need to check if biom_fp is undefined
            biom_table = load_table(biom_fp)
            samples = set(samples).intersection(biom_table.ids())
            biom_table.filter(samples, axis='sample', inplace=True)
            # we need to check if the table has samples left before merging
            if biom_table.shape[0] != 0 and biom_table.shape[1] != 0:
                new_table = new_table.merge(biom_table)
                ids_map.update({sid: "%d.%s" % (a_id, sid)
                                for sid in biom_table.ids()})

        # Check if we need to rename the sample ids in the biom table
        new_table_ids = set(new_table.ids())
        if not new_table_ids.issuperset(rarefied_table.ids()):
            # We need to rename the sample ids
            new_table.update_ids(ids_map, 'sample', True, True)

        sql = """INSERT INTO qiita.artifact
                    (generated_timestamp, data_type_id, visibility_id,
                     artifact_type_id, submitted_to_vamps)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING artifact_id"""
        # Magic number 4 -> visibility sandbox
        # Magix number 7 -> biom artifact type
        TRN.add(sql, [analysis['timestamp'], biom_data['data_type_id'],
                      4, 7, False])
        artifact_id = TRN.execute_fetchlast()

        # Associate the artifact with the analysis
        sql = """INSERT INTO qiita.analysis_artifact
                    (analysis_id, artifact_id)
                 VALUES (%s, %s)"""
        TRN.add(sql, [analysis['analysis_id'], artifact_id])
        # Link the artifact with its file
        dd_id, mp = get_mountpoint('BIOM')[0]
        dir_fp = join(get_db_files_base_dir(), mp, str(artifact_id))
        if not exists(dir_fp):
            makedirs(dir_fp)
        new_table_fp = join(dir_fp, "biom_table.biom")
        with biom_open(new_table_fp, 'w') as f:
            new_table.to_hdf5(f, "Generated by Qiita")

        sql = """INSERT INTO qiita.filepath
                    (filepath, filepath_type_id, checksum,
                     checksum_algorithm_id, data_directory_id)
                 VALUES (%s, %s, %s, %s, %s)
                 RETURNING filepath_id"""
        # Magic number 7 -> filepath_type_id = 'biom'
        # Magic number 1 -> the checksum algorithm id
        TRN.add(sql, [basename(new_table_fp), 7,
                      compute_checksum(new_table_fp), 1, dd_id])
        fp_id = TRN.execute_fetchlast()
        sql = """INSERT INTO qiita.artifact_filepath
                    (artifact_id, filepath_id)
                 VALUES (%s, %s)"""
        TRN.add(sql, [artifact_id, fp_id])
        TRN.execute()

    return artifact_id


def create_rarefaction_job(depth, biom_artifact_id, analysis, srare_cmd_id):
    """Create a new rarefaction job

    Parameters
    ----------
    depth : int
        The rarefaction depth
    biom_artifact_id : int
        The artifact id of the input rarefaction biom table
    analysis : dict
        Dictionary with the analysis information
    srare_cmd_id : int
        The command id of the single rarefaction command

    Returns
    -------
    job_id : str
        The job id
    params : str
        The job parameters
    """
    # Add the row in the procesisng job table
    params = ('{"depth":%d,"subsample_multinomial":false,"biom_table":%s}'
              % (depth, biom_artifact_id))
    with TRN:
        # magic number 3: status -> success
        sql = """INSERT INTO qiita.processing_job
                    (email, command_id, command_parameters,
                     processing_job_status_id)
                 VALUES (%s, %s, %s, %s)
                 RETURNING processing_job_id"""
        TRN.add(sql, [analysis['email'], srare_cmd_id, params, 3])
        job_id = TRN.execute_fetchlast()
        # Step 1.2.b: Link the job with the input artifact
        sql = """INSERT INTO qiita.artifact_processing_job
                    (artifact_id, processing_job_id)
                 VALUES (%s, %s)"""
        TRN.add(sql, [biom_artifact_id, job_id])
        TRN.execute()
    return job_id, params


def transfer_file_to_artifact(analysis_id, a_timestamp, command_id,
                              data_type_id, params, artifact_type_id,
                              filepath_id):
    """Creates a new artifact with the given filepath id

    Parameters
    ----------
    analysis_id : int
        The analysis id to attach the artifact
    a_timestamp : datetime.datetime
        The generated timestamp of the artifact
    command_id : int
        The command id of the artifact
    data_type_id : int
        The data type id of the artifact
    params : str
        The parameters of the artifact
    artifact_type_id : int
        The artifact type
    filepath_id : int
        The filepath id

    Returns
    -------
    int
        The artifact id
    """
    with TRN:
        # Add the row in the artifact table
        # Magic number 4: Visibility -> sandbox
        sql = """INSERT INTO qiita.artifact
                    (generated_timestamp, command_id, data_type_id,
                     command_parameters, visibility_id, artifact_type_id,
                     submitted_to_vamps)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)
                 RETURNING artifact_id"""
        TRN.add(sql, [a_timestamp, command_id, data_type_id, params, 4,
                      artifact_type_id, False])
        artifact_id = TRN.execute_fetchlast()
        # Link the artifact with its file
        sql = """INSERT INTO qiita.artifact_filepath (artifact_id, filepath_id)
                 VALUES (%s, %s)"""
        TRN.add(sql, [artifact_id, filepath_id])
        # Link the artifact with the analysis
        sql = """INSERT INTO qiita.analysis_artifact
                    (analysis_id, artifact_id)
                 VALUES (%s, %s)"""
        TRN.add(sql, [analysis_id, artifact_id])

    return artifact_id


def create_rarefied_biom_artifact(analysis, srare_cmd_id, biom_data, params,
                                  parent_biom_artifact_id, rarefaction_job_id,
                                  srare_cmd_out_id):
    """Creates the rarefied biom artifact

    Parameters
    ----------
    analysis : dict
        The analysis information
    srare_cmd_id : int
        The command id of "Single Rarefaction"
    biom_data : dict
        The biom information
    params : str
        The processing parameters
    parent_biom_artifact_id : int
        The parent biom artifact id
    rarefaction_job_id : str
        The job id of the rarefaction job
    srare_cmd_out_id : int
        The id of the single rarefaction output

    Returns
    -------
    int
        The artifact id
    """
    with TRN:
        # Transfer the file to an artifact
        # Magic number 7: artifact type -> biom
        artifact_id = transfer_file_to_artifact(
            analysis['analysis_id'], analysis['timestamp'], srare_cmd_id,
            biom_data['data_type_id'], params, 7, biom_data['filepath_id'])
        # Link the artifact with its parent
        sql = """INSERT INTO qiita.parent_artifact (artifact_id, parent_id)
                 VALUES (%s, %s)"""
        TRN.add(sql, [artifact_id, parent_biom_artifact_id])
        # Link the artifact as the job output
        sql = """INSERT INTO qiita.artifact_output_processing_job
                    (artifact_id, processing_job_id, command_output_id)
                 VALUES (%s, %s, %s)"""
        TRN.add(sql, [artifact_id, rarefaction_job_id, srare_cmd_out_id])
    return artifact_id


def transfer_job(analysis, command_id, params, input_artifact_id, job_data,
                 cmd_out_id, biom_data, output_artifact_type_id):
    """Transfers the job from the old structure to the plugin structure

    Parameters
    ----------
    analysis : dict
        The analysis information
    command_id : int
        The id of the command executed
    params : str
        The parameters used in the job
    input_artifact_id : int
        The id of the input artifact
    job_data : dict
        The job information
    cmd_out_id : int
        The id of the command's output
    biom_data : dict
        The biom information
    output_artifact_type_id : int
        The type of the output artifact
    """
    with TRN:
        # Create the job
        # Add the row in the processing job table
        # Magic number 3: status -> success
        sql = """INSERT INTO qiita.processing_job
                    (email, command_id, command_parameters,
                     processing_job_status_id)
                 VALUES (%s, %s, %s, %s)
                 RETURNING processing_job_id"""
        TRN.add(sql, [analysis['email'], command_id, params, 3])
        job_id = TRN.execute_fetchlast()

        # Link the job with the input artifact
        sql = """INSERT INTO qiita.artifact_processing_job
                    (artifact_id, processing_job_id)
                 VALUES (rarefied_biom_id, proc_job_id)"""
        TRN.add(sql, [input_artifact_id, job_id])

        # Check if the executed job has results and add them
        sql = """SELECT EXISTS(SELECT *
                               FROM qiita.job_results_filepath
                               WHERE job_id = %s)"""
        TRN.add(sql, [job_data['job_id']])
        if TRN.execute_fetchlast():
            # There are results for the current job.
            # Transfer the job files to a new artifact
            sql = """SELECT filepath_id
                     FROM qiita.job_results_filepath
                     WHERE job_id = %s"""
            TRN.add(sql, job_data['job_id'])
            filepath_id = TRN.execute_fetchlast()
            artifact_id = transfer_file_to_artifact(
                analysis['analysis_id'], analysis['timestamp'], command_id,
                biom_data['data_type_id'], params, output_artifact_type_id,
                filepath_id)

            # Link the artifact with its parent
            sql = """INSERT INTO qiita.parent_artifact (artifact_id, parent_id)
                     VALUES (%s, %s)"""
            TRN.add(sql, [artifact_id, input_artifact_id])
            # Link the artifact as the job output
            sql = """INSERT INTO qiita.artifact_output_processing_job
                        (artifact_id, processing_job_id, command_output_id)
                     VALUES (%s, %s, %s)"""
            TRN.add(sql, [artifact_id, job_id, cmd_out_id])
            TRN.exeucte()
        else:
            # There are no results on the current job, so mark it as
            # error
            if job_data.log_id is None:
                # Magic number 2 - we are not using any other severity
                # level, so keep using number 2
                sql = """INSERT INTO qiita.logging (time, severity_id, msg)
                    VALUES (%s, %s, %s)
                    RETURNING logging_id"""
                TRN.add(sql, [analysis['timestamp'], 2,
                              "Unknown error - patch 47"])
            else:
                log_id = job_data['log_id']

            # Magic number 4 -> status -> error
            sql = """UPDATE qiita.processing_job
                SET processing_job_status_id = 4, logging_id = %s
                WHERE processing_job_id = %s"""
            TRN.add(sql, [log_id, job_id])


# The new commands that we are going to add generate new artifact types.
# These new artifact types are going to be added to a different plugin.
# In interest of time and given that the artifact type system is going to
# change in the near future, we feel that the easiest way to transfer
# the current analyses results is by creating 3 different types of
# artifacts: (1) distance matrix -> which will include the distance matrix,
# the principal coordinates and the emperor plots; (2) rarefaction
# curves -> which will include all the files generated by alpha rarefaction
# and (3) taxonomy summary, which will include all the files generated
# by summarize_taxa_through_plots.py

with TRN:
    # Add the new artifact types
    sql = """INSERT INTO qiita.artifact_type (
                artifact_type, description, can_be_submitted_to_ebi,
                can_be_submitted_to_vamps)
             VALUES (%s, %s, %s, %s)
             RETURNING artifact_type_id"""
    TRN.add(sql, ['beta_div_plots', 'Qiime 1 beta diversity results',
                  False, False])
    dm_atype_id = TRN.execute_fetchlast()
    TRN.add(sql, ['rarefaction_curves', 'Rarefaction curves', False, False])
    rc_atype_id = TRN.execute_fetchlast()
    TRN.add(sql, ['taxa_summary', 'Taxa summary plots', False, False])
    ts_atype_id = TRN.execute_fetchlast()

    # Associate each artifact with the filetypes that it accepts
    # At this time we are going to add them as directories, just as it is done
    # right now. We can make it fancier with the new type system.
    # Magic number 8: the filepath_type_id for the directory
    sql = """INSERT INTO qiita.artifact_type_filepath_type
                (artifact_type_id, filepath_type_id, required)
             VALUES (%s, %s, %s)"""
    sql_args = [[dm_atype_id, 8, True],
                [rc_atype_id, 8, True],
                [ts_atype_id, 8, True]]
    TRN.add(sql, sql_args, many=True)

    # Create the new commands that execute the current analyses. In qiita,
    # the only commands that where available are Summarize Taxa, Beta
    # Diversity and Alpha Rarefaction. The system was executing rarefaction
    # by default, but it should be a different step in the analysis process
    # so we are going to create a command for it too. These commands are going
    # to be part of the QIIME plugin, so we are going to first retrieve the
    # id of the QIIME 1.9.1 plugin, which for sure exists cause it was added
    # in patch 33 and there is no way of removing plugins

    # Step 1: Get the QIIME plugin id
    sql = """SELECT software_id
             FROM qiita.software
             WHERE name = 'QIIME' AND version = '1.9.1'"""
    TRN.add(sql)
    qiime_id = TRN.execute_fetchlast()

    # Step 2: Insert the new commands in the software_command table
    sql = """INSERT INTO qiita.software_command
                (software_id, name, description, is_analysis)
             VALUES (%s, %s, %s, TRUE)
             RETURNING command_id"""
    TRN.add(sql, [qiime_id, 'Summarize Taxa', 'Plots taxonomy summaries at '
                            'different taxonomy levels'])
    sum_taxa_cmd_id = TRN.execute_fetchlast()
    TRN.add(sql, [qiime_id, 'Beta Diversity',
                  'Computes and plots beta diversity results'])
    bdiv_cmd_id = TRN.execute_fetchlast()
    TRN.add(sql, [qiime_id, 'Alpha Rarefaction',
                  'Computes and plots alpha rarefaction results'])
    arare_cmd_id = TRN.execute_fetchlast()
    TRN.add(sql, [qiime_id, 'Single Rarefaction',
                  'Rarefies the input table by random sampling without '
                  'replacement'])
    srare_cmd_id = TRN.execute_fetchlast()

    # Step 3: Insert the parameters for each command
    sql = """INSERT INTO qiita.command_parameter
                (command_id, parameter_name, parameter_type, required,
                 default_value)
             VALUES (%s, %s, %s, %s, %s)
             RETURNING command_parameter_id"""
    sql_args = [
        # Summarize Taxa
        (sum_taxa_cmd_id, 'metadata_category', 'string', False, ''),
        (sum_taxa_cmd_id, 'sort', 'bool', False, 'False'),
        # Beta Diversity
        (bdiv_cmd_id, 'tree', 'string', False, ''),
        (bdiv_cmd_id, 'metric',
         'choice:["abund_jaccard","binary_chisq","binary_chord",'
         '"binary_euclidean","binary_hamming","binary_jaccard",'
         '"binary_lennon","binary_ochiai","binary_otu_gain","binary_pearson",'
         '"binary_sorensen_dice","bray_curtis","bray_curtis_faith",'
         '"bray_curtis_magurran","canberra","chisq","chord","euclidean",'
         '"gower","hellinger","kulczynski","manhattan","morisita_horn",'
         '"pearson","soergel","spearman_approx","specprof","unifrac",'
         '"unifrac_g","unifrac_g_full_tree","unweighted_unifrac",'
         '"unweighted_unifrac_full_tree","weighted_normalized_unifrac",'
         '"weighted_unifrac"]', False, '"binary_jaccard"'),
        # Alpha rarefaction
        (arare_cmd_id, 'tree', 'string', False, ''),
        (arare_cmd_id, 'num_steps', 'integer', False, 10),
        (arare_cmd_id, 'min_rare_depth', 'integer', False, 10),
        (arare_cmd_id, 'max_rare_depth', 'integer', False, 'Default'),
        (arare_cmd_id, 'metrics',
         'mchoice:["ace","berger_parker_d","brillouin_d","chao1","chao1_ci",'
         '"dominance","doubles","enspie","equitability","esty_ci",'
         '"fisher_alpha","gini_index","goods_coverage","heip_e",'
         '"kempton_taylor_q","margalef","mcintosh_d","mcintosh_e",'
         '"menhinick","michaelis_menten_fit","observed_otus",'
         '"observed_species","osd","simpson_reciprocal","robbins",'
         '"shannon","simpson","simpson_e","singles","strong","PD_whole_tree"]',
         False, '["chao1","observed_otus"]'),
        # Single rarefaction
        (srare_cmd_id, 'depth', 'integer', True, None),
        (srare_cmd_id, 'subsample_multinomial', 'bool', False, 'False')
    ]
    TRN.add(sql, sql_args, many=True)

    TRN.add(sql, [sum_taxa_cmd_id, 'biom_table', 'artifact', True, None])
    sum_taxa_cmd_param_id = TRN.execute_fetchlast()
    TRN.add(sql, [bdiv_cmd_id, 'biom_table', 'artifact', True, None])
    bdiv_cmd_param_id = TRN.execute_fetchlast()
    TRN.add(sql, [arare_cmd_id, 'biom_table', 'artifact', True, None])
    arare_cmd_param_id = TRN.execute_fetchlast()
    TRN.add(sql, [srare_cmd_id, 'biom_table', 'artifact', True, None])
    srare_cmd_param_id = TRN.execute_fetchlast()

    # Step 4: Connect the artifact parameters with the artifact types that
    # they accept
    sql = """SELECT artifact_type_id
             FROM qiita.artifact_type
             WHERE artifact_type = 'BIOM'"""
    TRN.add(sql)
    biom_atype_id = TRN.execute_fetchlast()

    sql = """INSERT INTO qiita.parameter_artifact_type
                (command_parameter_id, artifact_type_id)
             VALUES (%s, %s)"""
    sql_args = [[sum_taxa_cmd_param_id, biom_atype_id],
                [bdiv_cmd_param_id, biom_atype_id],
                [arare_cmd_param_id, biom_atype_id],
                [srare_cmd_param_id, biom_atype_id]]
    TRN.add(sql, sql_args, many=True)

    # Step 5: Add the outputs of the command.
    sql = """INSERT INTO qiita.command_output
                (name, command_id, artifact_type_id)
             VALUES (%s, %s, %s)
             RETURNING command_output_id"""
    TRN.add(sql, ['taxa_summary', sum_taxa_cmd_id, ts_atype_id])
    sum_taxa_cmd_out_id = TRN.execute_fetchlast()
    TRN.add(sql, ['distance_matrix', bdiv_cmd_id, dm_atype_id])
    bdiv_cmd_out_id = TRN.execute_fetchlast()
    TRN.add(sql, ['rarefaction_curves', arare_cmd_id, rc_atype_id])
    arare_cmd_out_id = TRN.execute_fetchlast()
    TRN.add(sql, ['rarefied_table', srare_cmd_id, biom_atype_id])
    srare_cmd_out_id = TRN.execute_fetchlast()

    # Step 6: Add default parameter sets
    sql = """INSERT INTO qiita.default_parameter_set
                (command_id, parameter_set_name, parameter_set)
             VALUES (%s, %s, %s)"""
    sql_args = [
        [sum_taxa_cmd_id, 'Defaults',
         '{"sort": false, "metadata_category": ""}'],
        [bdiv_cmd_id, 'Unweighted UniFrac',
         '{"metric": "unweighted_unifrac", "tree": ""}'],
        [arare_cmd_id, 'Defaults',
         '{"max_rare_depth": "Default", "tree": "", "num_steps": 10, '
         '"min_rare_depth": 10, "metrics": ["chao1", "observed_otus"]}'],
        [srare_cmd_id, 'Defaults',
         '{"subsample_multinomial": "False"}']]
    TRN.add(sql, sql_args, many=True)

# At this point we are ready to start transferring the data from the old
# structures to the new structures. Overview of the procedure:
# Step 1: Add initial set of artifacts up to rarefied table
# Step 2: Transfer the "analysis jobs" to processing jobs and create
#         the analysis artifacts
db_dir = get_db_files_base_dir()
with TRN:
    sql = "SELECT * FROM qiita.analysis"
    TRN.add(sql)
    analysis_info = TRN.execute_fetchindex()

    # Loop through all the analysis
    for analysis in analysis_info:
        # Step 1: Add the inital set of artifacts. An analysis starts with
        # a set of BIOM artifacts.
        sql = """SELECT *
                 FROM qiita.analysis_filepath
                    JOIN qiita.filepath USING (filepath_id)
                    JOIN qiita.filepath_type USING (filepath_type_id)
                WHERE analysis_id = %s AND filepath_type = 'biom'"""
        TRN.add(sql, [analysis['analysis_id']])
        analysis_bioms = TRN.execute_fetchindex()

        # Loop through all the biom tables associated with the current analysis
        # so we can create the initial set of artifacts
        for biom_data in analysis_bioms:
            # Get the path of the BIOM table
            sql = """SELECT filepath, mountpoint
                     FROM qiita.filepath
                        JOIN qiita.data_directory USING (data_directory_id)
                     WHERE filepath_id = %s"""
            TRN.add(sql, [biom_data['filepath_id']])
            # Magic number 0: There is only a single row in the query result
            fp_info = TRN.execute_fetchindex()[0]
            filepath = join(db_dir, fp_info['mountpoint'], fp_info['filepath'])

            # We need to check if the BIOM table has been rarefied or not
            table = load_table(filepath)
            depths = set(table.sum(axis='sample'))
            if len(depths) == 1:
                # The BIOM table was rarefied
                # Create the initial unrarefied artifact
                initial_biom_artifact_id = create_non_rarefied_biom_artifact(
                    analysis, biom_data, table)
                # Create the rarefaction job
                rarefaction_job_id, params = create_rarefaction_job(
                    depths.pop(), initial_biom_artifact_id, analysis,
                    srare_cmd_id)
                # Create the rarefied artifact
                rarefied_biom_artifact_id = create_rarefied_biom_artifact(
                    analysis, srare_cmd_id, biom_data, params,
                    initial_biom_artifact_id, rarefaction_job_id,
                    srare_cmd_out_id)
            else:
                # The BIOM table was not rarefied, use current table as initial
                initial_biom_id = transfer_file_to_artifact(
                    analysis['analysis_id'], analysis['timestamp'], None,
                    biom_data['data_type_id'], None, 7,
                    biom_data['filepath_id'])

            # Loop through all the jobs that used this biom table as input
            sql = """SELECT *
                     FROM qiita.job
                     WHERE reverse(split_part(reverse(
                        options::json->>'--otu_table_fp'), '/', 1)) = %s"""
            TRN.add(sql, [filepath])
            analysis_jobs = TRN.execute_fetchindex()
            for job_data in analysis_jobs:
                # Identify which command the current job exeucted
                if job_data['command_id'] == 1:
                    # Taxa summaries
                    cmd_id = sum_taxa_cmd_id
                    params = ('{"biom_table":%d,"metadata_category":"",'
                              '"sort":false}' % initial_biom_id)
                    output_artifact_type_id = ts_atype_id
                    cmd_out_id = sum_taxa_cmd_out_id
                elif job_data['command_id'] == 2:
                    # Beta diversity
                    cmd_id = bdiv_cmd_id
                    tree_fp = loads(job_data['options'])['--tree_fp']
                    if tree_fp:
                        params = ('{"biom_table":%d,"tree":"%s","metrics":'
                                  '["unweighted_unifrac","weighted_unifrac"]}'
                                  % (initial_biom_id, tree_fp))
                    else:
                        params = ('{"biom_table":%d,"metrics":["bray_curtis",'
                                  '"gower","canberra","pearson"]}'
                                  % initial_biom_id)
                    output_artifact_type_id = dm_atype_id
                    cmd_out_id = bdiv_cmd_out_id
                else:
                    # Alpha rarefaction
                    cmd_id = arare_cmd_id
                    tree_fp = loads(job_data['options'])['--tree_fp']
                    params = ('{"biom_table":%d,"tree":"%s","num_steps":"10",'
                              '"min_rare_depth":"10",'
                              '"max_rare_depth":"Default"}'
                              % (initial_biom_id, tree_fp))
                    output_artifact_type_id = rc_atype_id
                    cmd_out_id = arare_cmd_out_id

                transfer_job(analysis, cmd_id, params, initial_biom_id,
                             job_data, cmd_out_id, biom_data,
                             output_artifact_type_id)

errors = []
with TRN:
    # Unlink the analysis from the biom table filepaths
    # Magic number 7 -> biom filepath type
    sql = """DELETE FROM qiita.analysis_filepath
             WHERE filepath_id IN (SELECT filepath_id
                                   FROM qiita.filepath
                                   WHERE filepath_type_id = 7)"""
    TRN.add(sql)
    TRN.execute()

    # Delete old structures that are not used anymore
    tables = ["collection_job", "collection_analysis", "collection_users",
              "collection", "collection_status", "analysis_workflow",
              "analysis_chain", "analysis_job", "job_results_filepath", "job",
              "job_status", "command_data_type", "command", "analysis_status"]
    for table in tables:
        TRN.add("DROP TABLE qiita.%s" % table)
        try:
            TRN.execute()
        except Exception as e:
            errors.append("Error deleting table %s: %s" % (table, str(e)))

# Purge filepaths
try:
    purge_filepaths(False)
except Exception as e:
    errors.append("Error purging filepaths: %s" % str(e))

if errors:
    print("\n".join(errors))
