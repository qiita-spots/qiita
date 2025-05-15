--
-- PostgreSQL database dump
--
-- Dumped from database version 13.9
-- Dumped by pg_dump version 13.9
-- SET statement_timeout = 0;
-- SET lock_timeout = 0;
-- SET idle_in_transaction_session_timeout = 0;
-- SET client_encoding = 'UTF8';
-- SET standard_conforming_strings = on;
-- SELECT pg_catalog.set_config('search_path', '', false);
-- SET check_function_bodies = false;
-- SET xmloption = content;
-- SET client_min_messages = warning;
-- SET row_security = off;
--
-- Data for Name: severity; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.severity
VALUES
    (1, 'Warning');

INSERT INTO
    qiita.severity
VALUES
    (2, 'Runtime');

INSERT INTO
    qiita.severity
VALUES
    (3, 'Fatal');

--
-- Data for Name: logging; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.logging
VALUES
    (
        1,
        '2015-11-22 21:29:30',
        2,
        'Error message',
        NULL
    );

INSERT INTO
    qiita.logging
VALUES
    (
        2,
        '2015-11-22 21:29:30',
        2,
        'Error message',
        '{}'
    );

--
-- Data for Name: user_level; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.user_level
VALUES
    (
        2,
        'dev',
        'Can access all data and info about errors',
        '--nice=10000'
    );

INSERT INTO
    qiita.user_level
VALUES
    (
        3,
        'superuser',
        'Can see all studies, can run analyses',
        '--nice=10000'
    );

INSERT INTO
    qiita.user_level
VALUES
    (
        4,
        'user',
        'Can see own and public data, can run analyses',
        '--nice=10000'
    );

INSERT INTO
    qiita.user_level
VALUES
    (
        5,
        'unverified',
        'Email not verified',
        '--nice=10000'
    );

INSERT INTO
    qiita.user_level
VALUES
    (
        6,
        'guest',
        'Can view & download public data',
        '--nice=10000'
    );

INSERT INTO
    qiita.user_level
VALUES
    (
        1,
        'admin',
        'Can access and do all the things',
        '--nice=5000'
    );

INSERT INTO
    qiita.user_level
VALUES
    (
        7,
        'wet-lab admin',
        'Can access the private jobs',
        ''
    );

--
-- Data for Name: qiita_user; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.qiita_user
VALUES
    (
        'test@foo.bar',
        4,
        '$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe',
        'Dude',
        'Nowhere University',
        '123 fake st, Apt 0, Faketown, CO 80302',
        '111-222-3344',
        NULL,
        NULL,
        NULL
    );

INSERT INTO
    qiita.qiita_user
VALUES
    (
        'shared@foo.bar',
        4,
        '$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe',
        'Shared',
        'Nowhere University',
        '123 fake st, Apt 0, Faketown, CO 80302',
        '111-222-3344',
        NULL,
        NULL,
        NULL
    );

INSERT INTO
    qiita.qiita_user
VALUES
    (
        'admin@foo.bar',
        1,
        '$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe',
        'Admin',
        'Owner University',
        '312 noname st, Apt K, Nonexistantown, CO 80302',
        '222-444-6789',
        NULL,
        NULL,
        NULL
    );

INSERT INTO
    qiita.qiita_user
VALUES
    (
        'demo@microbio.me',
        4,
        '$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe',
        'Demo',
        'Qiita Dev',
        '1345 Colorado Avenue',
        '303-492-1984',
        NULL,
        NULL,
        NULL
    );

--
-- Data for Name: analysis; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.analysis
VALUES
    (
        1,
        'test@foo.bar',
        'SomeAnalysis',
        'A test analysis',
        '121112',
        '2018-12-03 13:52:42.751331-07',
        false,
        NULL,
        ''
    );

INSERT INTO
    qiita.analysis
VALUES
    (
        2,
        'admin@foo.bar',
        'SomeSecondAnalysis',
        'Another test analysis',
        '22221112',
        '2018-12-03 13:52:42.751331-07',
        false,
        NULL,
        ''
    );

INSERT INTO
    qiita.analysis
VALUES
    (
        3,
        'test@foo.bar',
        'test@foo.bar-dflt-1',
        'dflt',
        NULL,
        '2018-12-03 13:52:42.751331-07',
        true,
        NULL,
        ''
    );

INSERT INTO
    qiita.analysis
VALUES
    (
        4,
        'admin@foo.bar',
        'admin@foo.bar-dflt-1',
        'dflt',
        NULL,
        '2018-12-03 13:52:42.751331-07',
        true,
        NULL,
        ''
    );

INSERT INTO
    qiita.analysis
VALUES
    (
        5,
        'shared@foo.bar',
        'shared@foo.bar-dflt-1',
        'dflt',
        NULL,
        '2018-12-03 13:52:42.751331-07',
        true,
        NULL,
        ''
    );

INSERT INTO
    qiita.analysis
VALUES
    (
        6,
        'demo@microbio.me',
        'demo@microbio.me-dflt-1',
        'dflt',
        NULL,
        '2018-12-03 13:52:42.751331-07',
        true,
        NULL,
        ''
    );

INSERT INTO
    qiita.analysis
VALUES
    (
        7,
        'test@foo.bar',
        'test@foo.bar-dflt-2',
        'dflt',
        NULL,
        '2018-12-03 13:52:42.751331-07',
        true,
        NULL,
        ''
    );

INSERT INTO
    qiita.analysis
VALUES
    (
        8,
        'admin@foo.bar',
        'admin@foo.bar-dflt-2',
        'dflt',
        NULL,
        '2018-12-03 13:52:42.751331-07',
        true,
        NULL,
        ''
    );

INSERT INTO
    qiita.analysis
VALUES
    (
        9,
        'shared@foo.bar',
        'shared@foo.bar-dflt-2',
        'dflt',
        NULL,
        '2018-12-03 13:52:42.751331-07',
        true,
        NULL,
        ''
    );

INSERT INTO
    qiita.analysis
VALUES
    (
        10,
        'demo@microbio.me',
        'demo@microbio.me-dflt-2',
        'dflt',
        NULL,
        '2018-12-03 13:52:42.751331-07',
        true,
        NULL,
        ''
    );

--
-- Data for Name: artifact_type; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.artifact_type
VALUES
    (1, 'SFF', NULL, false, false, false);

INSERT INTO
    qiita.artifact_type
VALUES
    (4, 'FASTA', NULL, false, false, false);

INSERT INTO
    qiita.artifact_type
VALUES
    (2, 'FASTA_Sanger', NULL, false, false, false);

INSERT INTO
    qiita.artifact_type
VALUES
    (
        6,
        'Demultiplexed',
        'Demultiplexed and QC sequences',
        true,
        true,
        false
    );

INSERT INTO
    qiita.artifact_type
VALUES
    (
        8,
        'beta_div_plots',
        'Qiime 1 beta diversity results',
        false,
        false,
        false
    );

INSERT INTO
    qiita.artifact_type
VALUES
    (
        9,
        'rarefaction_curves',
        'Rarefaction curves',
        false,
        false,
        false
    );

INSERT INTO
    qiita.artifact_type
VALUES
    (
        10,
        'taxa_summary',
        'Taxa summary plots',
        false,
        false,
        false
    );

INSERT INTO
    qiita.artifact_type
VALUES
    (3, 'FASTQ', NULL, false, false, true);

INSERT INTO
    qiita.artifact_type
VALUES
    (5, 'per_sample_FASTQ', NULL, true, false, true);

INSERT INTO
    qiita.artifact_type
VALUES
    (7, 'BIOM', 'BIOM table', false, false, true);

--
-- Data for Name: data_type; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.data_type
VALUES
    (1, '16S');

INSERT INTO
    qiita.data_type
VALUES
    (2, '18S');

INSERT INTO
    qiita.data_type
VALUES
    (3, 'ITS');

INSERT INTO
    qiita.data_type
VALUES
    (4, 'Proteomic');

INSERT INTO
    qiita.data_type
VALUES
    (5, 'Metabolomic');

INSERT INTO
    qiita.data_type
VALUES
    (6, 'Metagenomic');

INSERT INTO
    qiita.data_type
VALUES
    (7, 'Multiomic');

INSERT INTO
    qiita.data_type
VALUES
    (8, 'Metatranscriptomics');

INSERT INTO
    qiita.data_type
VALUES
    (9, 'Viromics');

INSERT INTO
    qiita.data_type
VALUES
    (10, 'Genomics');

INSERT INTO
    qiita.data_type
VALUES
    (11, 'Transcriptomics');

INSERT INTO
    qiita.data_type
VALUES
    (12, 'Job Output Folder');

--
-- Data for Name: software_type; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.software_type
VALUES
    (
        1,
        'artifact transformation',
        'A plugin that performs some kind of processing/transformation/manipulation over an artifact.'
    );

INSERT INTO
    qiita.software_type
VALUES
    (
        2,
        'artifact definition',
        'A plugin that defines new artifact types.'
    );

INSERT INTO
    qiita.software_type
VALUES
    (3, 'private', 'Internal Qiita jobs');

--
-- Data for Name: software; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.software
VALUES
    (
        2,
        'BIOM type',
        '2.1.4 - Qiime2',
        'The Biological Observation Matrix format',
        'source ~/virtualenv/python2.7/bin/activate; export PATH=$HOME/miniconda3/bin/:$PATH; . activate qtp-biom',
        'start_biom',
        2,
        false,
        false
    );

INSERT INTO
    qiita.software
VALUES
    (
        3,
        'Target Gene type',
        '0.1.0',
        'Target gene artifact types plugin',
        'source ~/virtualenv/python2.7/bin/activate; export PATH=$HOME/miniconda3/bin/:$PATH; source activate qiita',
        'start_target_gene_types',
        2,
        false,
        false
    );

INSERT INTO
    qiita.software
VALUES
    (
        4,
        'Qiita',
        'alpha',
        'Internal Qiita jobs',
        'source /home/runner/.profile; conda activate qiita',
        'qiita-private-plugin',
        3,
        true,
        false
    );

INSERT INTO
    qiita.software
VALUES
    (
        1,
        'QIIMEq2',
        '1.9.1',
        'Quantitative Insights Into Microbial Ecology (QIIME) is an open-source bioinformatics pipeline for performing microbiome analysis from raw DNA sequencing data',
        'source activate qiita',
        'start_target_gene',
        1,
        false,
        false
    );

--
-- Data for Name: software_command; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.software_command
VALUES
    (
        1,
        'Split libraries FASTQ',
        1,
        'Demultiplexes and applies quality control to FASTQ data',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        2,
        'Split libraries',
        1,
        'Demultiplexes and applies quality control to FASTA data',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        3,
        'Pick closed-reference OTUs',
        1,
        'OTU picking using a closed reference approach',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        4,
        'Validate',
        2,
        'Validates a new artifact of type BIOM',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        5,
        'Generate HTML summary',
        2,
        'Generates the HTML summary of a BIOM artifact',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        6,
        'Validate',
        3,
        'Validates a new artifact of the given target gene type',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        7,
        'Generate HTML summary',
        3,
        'Generates the HTML summary of a given target gene type artifact',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        8,
        'build_analysis_files',
        4,
        'Builds the files needed for the analysis',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        9,
        'Summarize Taxa',
        1,
        'Plots taxonomy summaries at different taxonomy levels',
        true,
        true,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        10,
        'Beta Diversity',
        1,
        'Computes and plots beta diversity results',
        true,
        true,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        11,
        'Alpha Rarefaction',
        1,
        'Computes and plots alpha rarefaction results',
        true,
        true,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        12,
        'Single Rarefaction',
        1,
        'Rarefies the input table by random sampling without replacement',
        true,
        true,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        13,
        'release_validators',
        4,
        'Releases the job validators',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        14,
        'submit_to_VAMPS',
        4,
        'submits an artifact to VAMPS',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        15,
        'copy_artifact',
        4,
        'Creates a copy of an artifact',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        16,
        'submit_to_EBI',
        4,
        'submits an artifact to EBI',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        17,
        'delete_artifact',
        4,
        'Delete an artifact',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        18,
        'create_sample_template',
        4,
        'Create a sample template',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        19,
        'update_sample_template',
        4,
        'Updates the sample template',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        20,
        'delete_study',
        4,
        'Deletes a full study',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        21,
        'delete_sample_template',
        4,
        'Deletes a sample template',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        22,
        'update_prep_template',
        4,
        'Updates the prep template',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        23,
        'delete_sample_or_column',
        4,
        'Deletes a sample or a columns from the metadata',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        24,
        'complete_job',
        4,
        'Completes a given job',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        25,
        'delete_analysis',
        4,
        'Deletes a full analysis',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        26,
        'list_remote_files',
        4,
        'retrieves list of valid study files from remote dir',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        27,
        'download_remote_files',
        4,
        'downloads valid study files from remote dir',
        true,
        false,
        false,
        NULL
    );

INSERT INTO
    qiita.software_command
VALUES
    (
        28,
        'INSDC_download',
        4,
        'Downloads an accession from a given INSDC',
        true,
        false,
        false,
        NULL
    );

--
-- Data for Name: visibility; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.visibility
VALUES
    (
        1,
        'awaiting_approval',
        'Awaiting approval of metadata'
    );

INSERT INTO
    qiita.visibility
VALUES
    (
        4,
        'sandbox',
        'Only available to the owner. No sharing'
    );

INSERT INTO
    qiita.visibility
VALUES
    (
        3,
        'private',
        'Only visible to the owner and shared users'
    );

INSERT INTO
    qiita.visibility
VALUES
    (2, 'public', 'Visible to everybody');

INSERT INTO
    qiita.visibility
VALUES
    (5, 'archived', 'Archived artifact');

--
-- Data for Name: artifact; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.artifact
VALUES
    (
        1,
        '2012-10-01 09:30:27',
        NULL,
        NULL,
        3,
        3,
        2,
        false,
        'Raw data 1',
        NULL
    );

INSERT INTO
    qiita.artifact
VALUES
    (
        2,
        '2012-10-01 10:30:27',
        1,
        '{"max_barcode_errors": "1.5", "max_bad_run_length": "3", "phred_offset": "auto", "rev_comp": "False", "phred_quality_threshold": "3", "input_data": "1", "rev_comp_barcode": "False", "sequence_max_n": "0", "rev_comp_mapping_barcodes": "False", "min_per_read_length_fraction": "0.75", "barcode_type": "golay_12"}',
        3,
        6,
        2,
        false,
        'Demultiplexed 1',
        NULL
    );

INSERT INTO
    qiita.artifact
VALUES
    (
        3,
        '2012-10-01 11:30:27',
        1,
        '{"max_barcode_errors": "1.5", "max_bad_run_length": "3", "phred_offset": "auto", "rev_comp": "False", "phred_quality_threshold": "3", "input_data": "1", "rev_comp_barcode": "False", "sequence_max_n": "0", "rev_comp_mapping_barcodes": "True", "min_per_read_length_fraction": "0.75", "barcode_type": "golay_12"}',
        3,
        6,
        2,
        false,
        'Demultiplexed 2',
        NULL
    );

INSERT INTO
    qiita.artifact
VALUES
    (
        4,
        '2012-10-02 17:30:00',
        3,
        '{"reference": "1", "similarity": "0.97", "sortmerna_e_value": "1", "sortmerna_max_pos": "10000", "input_data": "2", "threads": "1", "sortmerna_coverage": "0.97"}',
        3,
        7,
        2,
        false,
        'BIOM',
        NULL
    );

INSERT INTO
    qiita.artifact
VALUES
    (
        5,
        '2012-10-02 17:30:00',
        3,
        '{"reference": "1", "similarity": "0.97", "sortmerna_e_value": "1", "sortmerna_max_pos": "10000", "input_data": "2", "threads": "1", "sortmerna_coverage": "0.97"}',
        3,
        7,
        2,
        false,
        'BIOM',
        NULL
    );

INSERT INTO
    qiita.artifact
VALUES
    (
        6,
        '2012-10-02 17:30:00',
        3,
        '{"reference": "2", "similarity": "0.97", "sortmerna_e_value": "1", "sortmerna_max_pos": "10000", "input_data": "2", "threads": "1", "sortmerna_coverage": "0.97"}',
        3,
        7,
        1,
        false,
        'BIOM',
        NULL
    );

INSERT INTO
    qiita.artifact
VALUES
    (
        7,
        '2012-10-02 17:30:00',
        NULL,
        NULL,
        3,
        7,
        1,
        false,
        'BIOM',
        NULL
    );

INSERT INTO
    qiita.artifact
VALUES
    (
        8,
        '2018-12-03 14:06:45.117389',
        NULL,
        NULL,
        4,
        7,
        2,
        false,
        'noname',
        NULL
    );

INSERT INTO
    qiita.artifact
VALUES
    (
        9,
        '2018-12-03 14:06:45.117389',
        12,
        '{"biom_table": "8", "depth": "9000", "subsample_multinomial": "False"}',
        4,
        7,
        2,
        false,
        'noname',
        NULL
    );

--
-- Data for Name: analysis_artifact; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.analysis_artifact
VALUES
    (1, 8);

INSERT INTO
    qiita.analysis_artifact
VALUES
    (1, 9);

--
-- Data for Name: checksum_algorithm; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.checksum_algorithm
VALUES
    (1, 'crc32');

--
-- Data for Name: data_directory; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.data_directory
VALUES
    (1, 'analysis', 'analysis', false, true);

INSERT INTO
    qiita.data_directory
VALUES
    (2, 'job', 'job', false, true);

INSERT INTO
    qiita.data_directory
VALUES
    (
        3,
        'preprocessed_data',
        'preprocessed_data',
        false,
        true
    );

INSERT INTO
    qiita.data_directory
VALUES
    (
        4,
        'processed_data',
        'processed_data',
        false,
        true
    );

INSERT INTO
    qiita.data_directory
VALUES
    (5, 'raw_data', 'raw_data', false, true);

INSERT INTO
    qiita.data_directory
VALUES
    (6, 'reference', 'reference', false, true);

INSERT INTO
    qiita.data_directory
VALUES
    (7, 'uploads', 'uploads', false, true);

INSERT INTO
    qiita.data_directory
VALUES
    (8, 'working_dir', 'working_dir', false, true);

INSERT INTO
    qiita.data_directory
VALUES
    (9, 'templates', 'templates', false, true);

INSERT INTO
    qiita.data_directory
VALUES
    (10, 'SFF', 'SFF', true, true);

INSERT INTO
    qiita.data_directory
VALUES
    (11, 'FASTQ', 'FASTQ', true, true);

INSERT INTO
    qiita.data_directory
VALUES
    (12, 'FASTA', 'FASTA', true, true);

INSERT INTO
    qiita.data_directory
VALUES
    (13, 'FASTA_Sanger', 'FASTA_Sanger', true, true);

INSERT INTO
    qiita.data_directory
VALUES
    (
        14,
        'per_sample_FASTQ',
        'per_sample_FASTQ',
        true,
        true
    );

INSERT INTO
    qiita.data_directory
VALUES
    (15, 'Demultiplexed', 'Demultiplexed', true, true);

INSERT INTO
    qiita.data_directory
VALUES
    (16, 'BIOM', 'BIOM', true, true);

--
-- Data for Name: filepath_type; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.filepath_type
VALUES
    (1, 'raw_forward_seqs');

INSERT INTO
    qiita.filepath_type
VALUES
    (2, 'raw_reverse_seqs');

INSERT INTO
    qiita.filepath_type
VALUES
    (3, 'raw_barcodes');

INSERT INTO
    qiita.filepath_type
VALUES
    (4, 'preprocessed_fasta');

INSERT INTO
    qiita.filepath_type
VALUES
    (5, 'preprocessed_fastq');

INSERT INTO
    qiita.filepath_type
VALUES
    (6, 'preprocessed_demux');

INSERT INTO
    qiita.filepath_type
VALUES
    (7, 'biom');

INSERT INTO
    qiita.filepath_type
VALUES
    (8, 'directory');

INSERT INTO
    qiita.filepath_type
VALUES
    (9, 'plain_text');

INSERT INTO
    qiita.filepath_type
VALUES
    (10, 'reference_seqs');

INSERT INTO
    qiita.filepath_type
VALUES
    (11, 'reference_tax');

INSERT INTO
    qiita.filepath_type
VALUES
    (12, 'reference_tree');

INSERT INTO
    qiita.filepath_type
VALUES
    (13, 'log');

INSERT INTO
    qiita.filepath_type
VALUES
    (14, 'sample_template');

INSERT INTO
    qiita.filepath_type
VALUES
    (15, 'prep_template');

INSERT INTO
    qiita.filepath_type
VALUES
    (16, 'qiime_map');

INSERT INTO
    qiita.filepath_type
VALUES
    (17, 'raw_sff');

INSERT INTO
    qiita.filepath_type
VALUES
    (18, 'raw_fasta');

INSERT INTO
    qiita.filepath_type
VALUES
    (19, 'raw_qual');

INSERT INTO
    qiita.filepath_type
VALUES
    (20, 'html_summary');

INSERT INTO
    qiita.filepath_type
VALUES
    (21, 'tgz');

INSERT INTO
    qiita.filepath_type
VALUES
    (22, 'html_summary_dir');

INSERT INTO
    qiita.filepath_type
VALUES
    (23, 'qzv');

INSERT INTO
    qiita.filepath_type
VALUES
    (24, 'qza');

INSERT INTO
    qiita.filepath_type
VALUES
    (25, 'bam');

--
-- Data for Name: filepath; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.filepath
VALUES
    (
        1,
        '1_s_G1_L001_sequences.fastq.gz',
        1,
        '2125826711',
        1,
        5,
        58
    );

INSERT INTO
    qiita.filepath
VALUES
    (
        2,
        '1_s_G1_L001_sequences_barcodes.fastq.gz',
        3,
        '2125826711',
        1,
        5,
        58
    );

INSERT INTO
    qiita.filepath
VALUES
    (3, '1_seqs.fna', 4, '', 1, 3, 0);

INSERT INTO
    qiita.filepath
VALUES
    (4, '1_seqs.qual', 5, '', 1, 3, 0);

INSERT INTO
    qiita.filepath
VALUES
    (5, '1_seqs.demux', 6, '', 1, 3, 0);

INSERT INTO
    qiita.filepath
VALUES
    (
        6,
        'GreenGenes_13_8_97_otus.fasta',
        10,
        '852952723',
        1,
        6,
        1
    );

INSERT INTO
    qiita.filepath
VALUES
    (
        7,
        'GreenGenes_13_8_97_otu_taxonomy.txt',
        11,
        '852952723',
        1,
        6,
        1
    );

INSERT INTO
    qiita.filepath
VALUES
    (
        8,
        'GreenGenes_13_8_97_otus.tree',
        12,
        '852952723',
        1,
        6,
        1
    );

INSERT INTO
    qiita.filepath
VALUES
    (
        9,
        '1_study_1001_closed_reference_otu_table.biom',
        7,
        '1579715020',
        1,
        4,
        1256812
    );

INSERT INTO
    qiita.filepath
VALUES
    (10, 'Silva_97_otus.fasta', 10, '', 1, 6, 0);

INSERT INTO
    qiita.filepath
VALUES
    (11, 'Silva_97_otu_taxonomy.txt', 11, '', 1, 6, 0);

INSERT INTO
    qiita.filepath
VALUES
    (
        12,
        '1_study_1001_closed_reference_otu_table_Silva.biom',
        7,
        '1579715020',
        1,
        4,
        1256812
    );

INSERT INTO
    qiita.filepath
VALUES
    (13, '1_job_result.txt', 9, '0', 1, 2, 0);

INSERT INTO
    qiita.filepath
VALUES
    (14, '2_test_folder', 8, '', 1, 2, 0);

INSERT INTO
    qiita.filepath
VALUES
    (
        15,
        '1_analysis_18S.biom',
        7,
        '1756512010',
        1,
        1,
        1093210
    );

INSERT INTO
    qiita.filepath
VALUES
    (
        16,
        '1_analysis_mapping.txt',
        9,
        '291340704',
        1,
        1,
        7813
    );

INSERT INTO
    qiita.filepath
VALUES
    (
        17,
        '1_19700101-000000.txt',
        14,
        '1486964984',
        1,
        9,
        10309
    );

INSERT INTO
    qiita.filepath
VALUES
    (
        18,
        '1_prep_1_19700101-000000.txt',
        15,
        '3703494589',
        1,
        9,
        26051
    );

INSERT INTO
    qiita.filepath
VALUES
    (
        19,
        '1_prep_1_qiime_19700101-000000.txt',
        16,
        '3053485441',
        1,
        9,
        36780
    );

INSERT INTO
    qiita.filepath
VALUES
    (
        20,
        '1_prep_1_19700101-000000.txt',
        15,
        '3703494589',
        1,
        9,
        26051
    );

INSERT INTO
    qiita.filepath
VALUES
    (
        21,
        '1_prep_1_qiime_19700101-000000.txt',
        16,
        '3053485441',
        1,
        9,
        36780
    );

INSERT INTO
    qiita.filepath
VALUES
    (
        22,
        'biom_table.biom',
        7,
        '1756512010',
        1,
        16,
        1093210
    );

--
-- Data for Name: analysis_filepath; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.analysis_filepath
VALUES
    (1, 15, 2);

INSERT INTO
    qiita.analysis_filepath
VALUES
    (1, 16, NULL);

--
-- Data for Name: portal_type; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.portal_type
VALUES
    (2, 'EMP', 'EMP portal');

INSERT INTO
    qiita.portal_type
VALUES
    (
        1,
        'QIITA',
        'QIITA portal. Access to all data stored in database.'
    );

--
-- Data for Name: analysis_portal; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.analysis_portal
VALUES
    (1, 1);

INSERT INTO
    qiita.analysis_portal
VALUES
    (2, 1);

INSERT INTO
    qiita.analysis_portal
VALUES
    (3, 1);

INSERT INTO
    qiita.analysis_portal
VALUES
    (4, 1);

INSERT INTO
    qiita.analysis_portal
VALUES
    (5, 1);

INSERT INTO
    qiita.analysis_portal
VALUES
    (6, 1);

INSERT INTO
    qiita.analysis_portal
VALUES
    (7, 2);

INSERT INTO
    qiita.analysis_portal
VALUES
    (8, 2);

INSERT INTO
    qiita.analysis_portal
VALUES
    (9, 2);

INSERT INTO
    qiita.analysis_portal
VALUES
    (10, 2);

--
-- Data for Name: processing_job_status; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.processing_job_status
VALUES
    (1, 'queued', 'The job is waiting to be run');

INSERT INTO
    qiita.processing_job_status
VALUES
    (2, 'running', 'The job is running');

INSERT INTO
    qiita.processing_job_status
VALUES
    (3, 'success', 'The job completed successfully');

INSERT INTO
    qiita.processing_job_status
VALUES
    (4, 'error', 'The job failed');

INSERT INTO
    qiita.processing_job_status
VALUES
    (
        5,
        'in_construction',
        'The job is one of the source nodes of a workflow that is in construction'
    );

INSERT INTO
    qiita.processing_job_status
VALUES
    (
        6,
        'waiting',
        'The job is waiting for a previous job in the workflow to be completed in order to be executed.'
    );

--
-- Data for Name: processing_job; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.processing_job
VALUES
    (
        '6d368e16-2242-4cf8-87b4-a5dc40bb890b',
        'test@foo.bar',
        1,
        '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5,"input_data":1,"phred_offset":"auto"}',
        3,
        NULL,
        NULL,
        NULL,
        NULL,
        false,
        1284411757
    );

INSERT INTO
    qiita.processing_job
VALUES
    (
        '4c7115e8-4c8e-424c-bf25-96c292ca1931',
        'test@foo.bar',
        1,
        '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":true,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5,"input_data":1,"phred_offset":"auto"}',
        3,
        NULL,
        NULL,
        NULL,
        NULL,
        false,
        1287244546
    );

INSERT INTO
    qiita.processing_job
VALUES
    (
        '3c9991ab-6c14-4368-a48c-841e8837a79c',
        'test@foo.bar',
        3,
        '{"reference":1,"sortmerna_e_value":1,"sortmerna_max_pos":10000,"similarity":0.97,"sortmerna_coverage":0.97,"threads":1,"input_data":2}',
        3,
        NULL,
        NULL,
        NULL,
        NULL,
        false,
        1284411377
    );

INSERT INTO
    qiita.processing_job
VALUES
    (
        'b72369f9-a886-4193-8d3d-f7b504168e75',
        'shared@foo.bar',
        1,
        '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":true,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5,"input_data":1,"phred_offset":"auto"}',
        3,
        NULL,
        '2015-11-22 21:15:00',
        NULL,
        NULL,
        false,
        128552986
    );

INSERT INTO
    qiita.processing_job
VALUES
    (
        '46b76f74-e100-47aa-9bf2-c0208bcea52d',
        'test@foo.bar',
        1,
        '{"max_barcode_errors": "1.5", "sequence_max_n": "0", "max_bad_run_length": "3", "phred_offset": "auto", "rev_comp": "False", "phred_quality_threshold": "3", "input_data": "1", "rev_comp_barcode": "False", "rev_comp_mapping_barcodes": "True", "min_per_read_length_fraction": "0.75", "barcode_type": "golay_12"}',
        3,
        NULL,
        NULL,
        NULL,
        NULL,
        false,
        1279011391
    );

INSERT INTO
    qiita.processing_job
VALUES
    (
        '80bf25f3-5f1d-4e10-9369-315e4244f6d5',
        'test@foo.bar',
        3,
        '{"reference": "2", "similarity": "0.97", "sortmerna_e_value": "1", "sortmerna_max_pos": "10000", "input_data": "2", "threads": "1", "sortmerna_coverage": "0.97"}',
        3,
        NULL,
        NULL,
        NULL,
        NULL,
        false,
        1286151876
    );

INSERT INTO
    qiita.processing_job
VALUES
    (
        '9ba5ae7a-41e1-4202-b396-0259aeaac366',
        'test@foo.bar',
        3,
        '{"reference": "1", "similarity": "0.97", "sortmerna_e_value": "1", "sortmerna_max_pos": "10000", "input_data": "2", "threads": "1", "sortmerna_coverage": "0.97"}',
        3,
        NULL,
        NULL,
        NULL,
        NULL,
        false,
        1283300404
    );

INSERT INTO
    qiita.processing_job
VALUES
    (
        'e5609746-a985-41a1-babf-6b3ebe9eb5a9',
        'test@foo.bar',
        3,
        '{"reference": "1", "similarity": "0.97", "sortmerna_e_value": "1", "sortmerna_max_pos": "10000", "input_data": "2", "threads": "1", "sortmerna_coverage": "0.97"}',
        3,
        NULL,
        NULL,
        NULL,
        NULL,
        false,
        1275827198
    );

INSERT INTO
    qiita.processing_job
VALUES
    (
        '6ad4d590-4fa3-44d3-9a8f-ddbb472b1b5f',
        'test@foo.bar',
        1,
        '{"max_barcode_errors": "1.5", "sequence_max_n": "0", "max_bad_run_length": "3", "phred_offset": "auto", "rev_comp": "False", "phred_quality_threshold": "3", "input_data": "1", "rev_comp_barcode": "False", "rev_comp_mapping_barcodes": "False", "min_per_read_length_fraction": "0.75", "barcode_type": "golay_12"}',
        3,
        NULL,
        NULL,
        NULL,
        NULL,
        false,
        1266027
    );

INSERT INTO
    qiita.processing_job
VALUES
    (
        '8a7a8461-e8a1-4b4e-a428-1bc2f4d3ebd0',
        'test@foo.bar',
        12,
        '{"biom_table": "8", "depth": "9000", "subsample_multinomial": "False"}',
        3,
        NULL,
        NULL,
        NULL,
        NULL,
        false,
        126652530
    );

INSERT INTO
    qiita.processing_job
VALUES
    (
        '063e553b-327c-4818-ab4a-adfe58e49860',
        'test@foo.bar',
        1,
        '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5,"input_data":1,"phred_offset":"auto"}',
        1,
        NULL,
        NULL,
        NULL,
        NULL,
        true,
        NULL
    );

INSERT INTO
    qiita.processing_job
VALUES
    (
        'bcc7ebcd-39c1-43e4-af2d-822e3589f14d',
        'test@foo.bar',
        2,
        '{"min_seq_len":100,"max_seq_len":1000,"trim_seq_length":false,"min_qual_score":25,"max_ambig":6,"max_homopolymer":6,"max_primer_mismatch":0,"barcode_type":"golay_12","max_barcode_errors":1.5,"disable_bc_correction":false,"qual_score_window":0,"disable_primers":false,"reverse_primers":"disable","reverse_primer_mismatches":0,"truncate_ambi_bases":false,"input_data":1}',
        2,
        NULL,
        '2015-11-22 21:00:00',
        'demultiplexing',
        NULL,
        true,
        NULL
    );

INSERT INTO
    qiita.processing_job
VALUES
    (
        'd19f76ee-274e-4c1b-b3a2-a12d73507c55',
        'shared@foo.bar',
        3,
        '{"reference":1,"sortmerna_e_value":1,"sortmerna_max_pos":10000,"similarity":0.97,"sortmerna_coverage":0.97,"threads":1,"input_data":2}',
        4,
        1,
        '2015-11-22 21:30:00',
        'generating demux file',
        NULL,
        true,
        NULL
    );

INSERT INTO
    qiita.processing_job
VALUES
    (
        'ac653cb5-76a6-4a45-929e-eb9b2dee6b63',
        'test@foo.bar',
        1,
        '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5,"input_data":1}',
        5,
        NULL,
        NULL,
        NULL,
        NULL,
        true,
        NULL
    );

--
-- Data for Name: analysis_processing_job; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
--
-- Data for Name: study_person; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.study_person
VALUES
    (
        1,
        'LabDude',
        'lab_dude@foo.bar',
        'knight lab',
        '123 lab street',
        '121-222-3333'
    );

INSERT INTO
    qiita.study_person
VALUES
    (
        2,
        'empDude',
        'emp_dude@foo.bar',
        'broad',
        NULL,
        '444-222-3333'
    );

INSERT INTO
    qiita.study_person
VALUES
    (
        3,
        'PIDude',
        'PI_dude@foo.bar',
        'Wash U',
        '123 PI street',
        NULL
    );

--
-- Data for Name: timeseries_type; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.timeseries_type
VALUES
    (1, 'None', 'None');

INSERT INTO
    qiita.timeseries_type
VALUES
    (2, 'real', 'single intervention');

INSERT INTO
    qiita.timeseries_type
VALUES
    (3, 'real', 'multiple intervention');

INSERT INTO
    qiita.timeseries_type
VALUES
    (4, 'real', 'combo intervention');

INSERT INTO
    qiita.timeseries_type
VALUES
    (5, 'pseudo', 'single intervention');

INSERT INTO
    qiita.timeseries_type
VALUES
    (6, 'pseudo', 'multiple intervention');

INSERT INTO
    qiita.timeseries_type
VALUES
    (7, 'pseudo', 'combo intervention');

INSERT INTO
    qiita.timeseries_type
VALUES
    (8, 'mixed', 'single intervention');

INSERT INTO
    qiita.timeseries_type
VALUES
    (9, 'mixed', 'multiple intervention');

INSERT INTO
    qiita.timeseries_type
VALUES
    (10, 'mixed', 'combo intervention');

--
-- Data for Name: study; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.study
VALUES
    (
        1,
        'test@foo.bar',
        '2014-05-19 16:10:00',
        NULL,
        1,
        1,
        true,
        true,
        '2014-05-19 16:11:00',
        3,
        false,
        false,
        'Identification of the Microbiomes for Cannabis Soils',
        'Cannabis Soils',
        'Analysis of the Cannabis Plant Microbiome',
        'This is a preliminary study to examine the microbiota associated with the Cannabis plant. Soils samples from the bulk soil, soil associated with the roots, and the rhizosphere were extracted and the DNA sequenced. Roots from three independent plants of different strains were examined. These roots were obtained November 11, 2011 from plants that had been harvested in the summer. Future studies will attempt to analyze the soils and rhizospheres from the same location at different time points in the plant lifecycle.',
        NULL,
        'EBI123456-BB',
        false,
        '',
        false
    );

--
-- Data for Name: study_sample; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKB8.640193', 1, 'ERS000000', 'SAMEA0000000');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKD8.640184', 1, 'ERS000001', 'SAMEA0000001');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKB7.640196', 1, 'ERS000002', 'SAMEA0000002');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKM9.640192', 1, 'ERS000003', 'SAMEA0000003');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKM4.640180', 1, 'ERS000004', 'SAMEA0000004');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKM5.640177', 1, 'ERS000005', 'SAMEA0000005');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKB5.640181', 1, 'ERS000006', 'SAMEA0000006');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKD6.640190', 1, 'ERS000007', 'SAMEA0000007');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKB2.640194', 1, 'ERS000008', 'SAMEA0000008');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKD2.640178', 1, 'ERS000009', 'SAMEA0000009');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKM7.640188', 1, 'ERS000010', 'SAMEA0000010');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKB1.640202', 1, 'ERS000011', 'SAMEA0000011');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKD1.640179', 1, 'ERS000012', 'SAMEA0000012');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKD3.640198', 1, 'ERS000013', 'SAMEA0000013');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKM8.640201', 1, 'ERS000014', 'SAMEA0000014');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKM2.640199', 1, 'ERS000015', 'SAMEA0000015');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKB9.640200', 1, 'ERS000016', 'SAMEA0000016');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKD5.640186', 1, 'ERS000017', 'SAMEA0000017');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKM3.640197', 1, 'ERS000018', 'SAMEA0000018');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKD9.640182', 1, 'ERS000019', 'SAMEA0000019');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKB4.640189', 1, 'ERS000020', 'SAMEA0000020');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKD7.640191', 1, 'ERS000021', 'SAMEA0000021');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKM6.640187', 1, 'ERS000022', 'SAMEA0000022');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKD4.640185', 1, 'ERS000023', 'SAMEA0000023');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKB3.640195', 1, 'ERS000024', 'SAMEA0000024');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKB6.640176', 1, 'ERS000025', 'SAMEA0000025');

INSERT INTO
    qiita.study_sample
VALUES
    ('1.SKM1.640183', 1, 'ERS000025', 'SAMEA0000026');

--
-- Data for Name: analysis_sample; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.analysis_sample
VALUES
    (1, '1.SKB8.640193', 4);

INSERT INTO
    qiita.analysis_sample
VALUES
    (1, '1.SKD8.640184', 4);

INSERT INTO
    qiita.analysis_sample
VALUES
    (1, '1.SKB7.640196', 4);

INSERT INTO
    qiita.analysis_sample
VALUES
    (1, '1.SKM9.640192', 4);

INSERT INTO
    qiita.analysis_sample
VALUES
    (1, '1.SKM4.640180', 4);

INSERT INTO
    qiita.analysis_sample
VALUES
    (2, '1.SKB8.640193', 4);

INSERT INTO
    qiita.analysis_sample
VALUES
    (2, '1.SKD8.640184', 4);

INSERT INTO
    qiita.analysis_sample
VALUES
    (2, '1.SKB7.640196', 4);

INSERT INTO
    qiita.analysis_sample
VALUES
    (2, '1.SKM3.640197', 4);

INSERT INTO
    qiita.analysis_sample
VALUES
    (1, '1.SKB8.640193', 5);

INSERT INTO
    qiita.analysis_sample
VALUES
    (1, '1.SKD8.640184', 5);

INSERT INTO
    qiita.analysis_sample
VALUES
    (1, '1.SKB7.640196', 5);

INSERT INTO
    qiita.analysis_sample
VALUES
    (1, '1.SKM9.640192', 5);

INSERT INTO
    qiita.analysis_sample
VALUES
    (1, '1.SKM4.640180', 5);

INSERT INTO
    qiita.analysis_sample
VALUES
    (2, '1.SKB8.640193', 5);

INSERT INTO
    qiita.analysis_sample
VALUES
    (2, '1.SKD8.640184', 5);

INSERT INTO
    qiita.analysis_sample
VALUES
    (2, '1.SKB7.640196', 5);

INSERT INTO
    qiita.analysis_sample
VALUES
    (2, '1.SKM3.640197', 5);

INSERT INTO
    qiita.analysis_sample
VALUES
    (1, '1.SKB8.640193', 6);

INSERT INTO
    qiita.analysis_sample
VALUES
    (1, '1.SKD8.640184', 6);

INSERT INTO
    qiita.analysis_sample
VALUES
    (1, '1.SKB7.640196', 6);

INSERT INTO
    qiita.analysis_sample
VALUES
    (1, '1.SKM9.640192', 6);

INSERT INTO
    qiita.analysis_sample
VALUES
    (1, '1.SKM4.640180', 6);

INSERT INTO
    qiita.analysis_sample
VALUES
    (2, '1.SKB8.640193', 6);

INSERT INTO
    qiita.analysis_sample
VALUES
    (2, '1.SKD8.640184', 6);

INSERT INTO
    qiita.analysis_sample
VALUES
    (2, '1.SKB7.640196', 6);

INSERT INTO
    qiita.analysis_sample
VALUES
    (2, '1.SKM3.640197', 6);

INSERT INTO
    qiita.analysis_sample
VALUES
    (3, '1.SKD8.640184', 4);

INSERT INTO
    qiita.analysis_sample
VALUES
    (3, '1.SKB7.640196', 4);

INSERT INTO
    qiita.analysis_sample
VALUES
    (3, '1.SKM9.640192', 4);

INSERT INTO
    qiita.analysis_sample
VALUES
    (3, '1.SKM4.640180', 4);

--
-- Data for Name: analysis_users; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.analysis_users
VALUES
    (1, 'shared@foo.bar');

--
-- Data for Name: archive_merging_scheme; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
--
-- Data for Name: archive_feature_value; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
--
-- Data for Name: artifact_filepath; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.artifact_filepath
VALUES
    (1, 1);

INSERT INTO
    qiita.artifact_filepath
VALUES
    (1, 2);

INSERT INTO
    qiita.artifact_filepath
VALUES
    (2, 3);

INSERT INTO
    qiita.artifact_filepath
VALUES
    (2, 4);

INSERT INTO
    qiita.artifact_filepath
VALUES
    (2, 5);

INSERT INTO
    qiita.artifact_filepath
VALUES
    (4, 9);

INSERT INTO
    qiita.artifact_filepath
VALUES
    (5, 9);

INSERT INTO
    qiita.artifact_filepath
VALUES
    (6, 12);

INSERT INTO
    qiita.artifact_filepath
VALUES
    (7, 22);

INSERT INTO
    qiita.artifact_filepath
VALUES
    (8, 22);

INSERT INTO
    qiita.artifact_filepath
VALUES
    (9, 15);

--
-- Data for Name: command_output; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.command_output
VALUES
    (1, 'demultiplexed', 1, 6, false);

INSERT INTO
    qiita.command_output
VALUES
    (2, 'demultiplexed', 2, 6, false);

INSERT INTO
    qiita.command_output
VALUES
    (3, 'OTU table', 3, 7, false);

INSERT INTO
    qiita.command_output
VALUES
    (4, 'taxa_summary', 9, 10, false);

INSERT INTO
    qiita.command_output
VALUES
    (5, 'distance_matrix', 10, 8, false);

INSERT INTO
    qiita.command_output
VALUES
    (6, 'rarefaction_curves', 11, 9, false);

INSERT INTO
    qiita.command_output
VALUES
    (7, 'rarefied_table', 12, 7, false);

--
-- Data for Name: artifact_output_processing_job; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.artifact_output_processing_job
VALUES
    (3, '46b76f74-e100-47aa-9bf2-c0208bcea52d', 1);

INSERT INTO
    qiita.artifact_output_processing_job
VALUES
    (6, '80bf25f3-5f1d-4e10-9369-315e4244f6d5', 3);

INSERT INTO
    qiita.artifact_output_processing_job
VALUES
    (5, '9ba5ae7a-41e1-4202-b396-0259aeaac366', 3);

INSERT INTO
    qiita.artifact_output_processing_job
VALUES
    (4, 'e5609746-a985-41a1-babf-6b3ebe9eb5a9', 3);

INSERT INTO
    qiita.artifact_output_processing_job
VALUES
    (2, '6ad4d590-4fa3-44d3-9a8f-ddbb472b1b5f', 1);

INSERT INTO
    qiita.artifact_output_processing_job
VALUES
    (9, '8a7a8461-e8a1-4b4e-a428-1bc2f4d3ebd0', 7);

--
-- Data for Name: artifact_processing_job; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.artifact_processing_job
VALUES
    (1, '6d368e16-2242-4cf8-87b4-a5dc40bb890b');

INSERT INTO
    qiita.artifact_processing_job
VALUES
    (1, '4c7115e8-4c8e-424c-bf25-96c292ca1931');

INSERT INTO
    qiita.artifact_processing_job
VALUES
    (2, '3c9991ab-6c14-4368-a48c-841e8837a79c');

INSERT INTO
    qiita.artifact_processing_job
VALUES
    (1, '063e553b-327c-4818-ab4a-adfe58e49860');

INSERT INTO
    qiita.artifact_processing_job
VALUES
    (1, 'bcc7ebcd-39c1-43e4-af2d-822e3589f14d');

INSERT INTO
    qiita.artifact_processing_job
VALUES
    (1, 'b72369f9-a886-4193-8d3d-f7b504168e75');

INSERT INTO
    qiita.artifact_processing_job
VALUES
    (2, 'd19f76ee-274e-4c1b-b3a2-a12d73507c55');

INSERT INTO
    qiita.artifact_processing_job
VALUES
    (1, '46b76f74-e100-47aa-9bf2-c0208bcea52d');

INSERT INTO
    qiita.artifact_processing_job
VALUES
    (2, '80bf25f3-5f1d-4e10-9369-315e4244f6d5');

INSERT INTO
    qiita.artifact_processing_job
VALUES
    (2, '9ba5ae7a-41e1-4202-b396-0259aeaac366');

INSERT INTO
    qiita.artifact_processing_job
VALUES
    (2, 'e5609746-a985-41a1-babf-6b3ebe9eb5a9');

INSERT INTO
    qiita.artifact_processing_job
VALUES
    (1, '6ad4d590-4fa3-44d3-9a8f-ddbb472b1b5f');

INSERT INTO
    qiita.artifact_processing_job
VALUES
    (8, '8a7a8461-e8a1-4b4e-a428-1bc2f4d3ebd0');

--
-- Data for Name: artifact_type_filepath_type; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (1, 17, true);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (2, 18, true);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (3, 1, true);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (3, 2, false);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (3, 3, true);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (4, 18, true);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (4, 19, true);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (5, 1, true);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (5, 2, false);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (6, 4, true);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (6, 5, true);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (6, 6, false);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (6, 13, false);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (7, 7, true);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (7, 8, false);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (7, 13, false);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (8, 8, true);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (9, 8, true);

INSERT INTO
    qiita.artifact_type_filepath_type
VALUES
    (10, 8, true);

--
-- Data for Name: controlled_vocab; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
--
-- Data for Name: mixs_field_description; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
--
-- Data for Name: column_controlled_vocabularies; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
--
-- Data for Name: column_ontology; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
--
-- Data for Name: command_parameter; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.command_parameter
VALUES
    (
        1,
        'input_data',
        'artifact',
        true,
        NULL,
        1,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        1,
        'max_bad_run_length',
        'integer',
        false,
        '3',
        2,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        1,
        'min_per_read_length_fraction',
        'float',
        false,
        '0.75',
        3,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        1,
        'sequence_max_n',
        'integer',
        false,
        '0',
        4,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        1,
        'rev_comp_barcode',
        'bool',
        false,
        'False',
        5,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        1,
        'rev_comp_mapping_barcodes',
        'bool',
        false,
        'False',
        6,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        1,
        'rev_comp',
        'bool',
        false,
        'False',
        7,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        1,
        'phred_quality_threshold',
        'integer',
        false,
        '3',
        8,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        1,
        'barcode_type',
        'string',
        false,
        'golay_12',
        9,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        1,
        'max_barcode_errors',
        'float',
        false,
        '1.5',
        10,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        2,
        'input_data',
        'artifact',
        true,
        NULL,
        11,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        2,
        'min_seq_len',
        'integer',
        false,
        '200',
        12,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        2,
        'max_seq_len',
        'integer',
        false,
        '1000',
        13,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        2,
        'trim_seq_length',
        'bool',
        false,
        'False',
        14,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        2,
        'min_qual_score',
        'integer',
        false,
        '25',
        15,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        2,
        'max_ambig',
        'integer',
        false,
        '6',
        16,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        2,
        'max_homopolymer',
        'integer',
        false,
        '6',
        17,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        2,
        'max_primer_mismatch',
        'integer',
        false,
        '0',
        18,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        2,
        'barcode_type',
        'string',
        false,
        'golay_12',
        19,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        2,
        'max_barcode_errors',
        'float',
        false,
        '1.5',
        20,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        2,
        'disable_bc_correction',
        'bool',
        false,
        'False',
        21,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        2,
        'qual_score_window',
        'integer',
        false,
        '0',
        22,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        2,
        'disable_primers',
        'bool',
        false,
        'False',
        23,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        2,
        'reverse_primers',
        'choice:["disable", "truncate_only", "truncate_remove"]',
        false,
        'disable',
        24,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        2,
        'reverse_primer_mismatches',
        'integer',
        false,
        '0',
        25,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        2,
        'truncate_ambi_bases',
        'bool',
        false,
        'False',
        26,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        3,
        'input_data',
        'artifact',
        true,
        NULL,
        27,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        3,
        'reference',
        'reference',
        false,
        '1',
        28,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        3,
        'sortmerna_e_value',
        'float',
        false,
        '1',
        29,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        3,
        'sortmerna_max_pos',
        'integer',
        false,
        '10000',
        30,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        3,
        'similarity',
        'float',
        false,
        '0.97',
        31,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        3,
        'sortmerna_coverage',
        'float',
        false,
        '0.97',
        32,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        3,
        'threads',
        'integer',
        false,
        '1',
        33,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (4, 'files', 'string', true, NULL, 35, NULL, false);

INSERT INTO
    qiita.command_parameter
VALUES
    (
        4,
        'artifact_type',
        'string',
        true,
        NULL,
        36,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        5,
        'input_data',
        'artifact',
        true,
        NULL,
        37,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        6,
        'template',
        'prep_template',
        true,
        NULL,
        38,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (6, 'files', 'string', true, NULL, 39, NULL, false);

INSERT INTO
    qiita.command_parameter
VALUES
    (
        6,
        'artifact_type',
        'string',
        true,
        NULL,
        40,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        7,
        'input_data',
        'artifact',
        true,
        NULL,
        41,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        1,
        'phred_offset',
        'choice:["auto", "33", "64"]',
        false,
        'auto',
        42,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        4,
        'provenance',
        'string',
        false,
        NULL,
        43,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        6,
        'provenance',
        'string',
        false,
        NULL,
        44,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        4,
        'analysis',
        'analysis',
        false,
        NULL,
        45,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        4,
        'template',
        'prep_template',
        false,
        NULL,
        34,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        8,
        'analysis',
        'analysis',
        true,
        NULL,
        46,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        8,
        'merge_dup_sample_ids',
        'bool',
        false,
        'False',
        47,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        9,
        'metadata_category',
        'string',
        false,
        '',
        48,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        9,
        'sort',
        'bool',
        false,
        'False',
        49,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (10, 'tree', 'string', false, '', 50, NULL, false);

INSERT INTO
    qiita.command_parameter
VALUES
    (
        10,
        'metric',
        'choice:["abund_jaccard","binary_chisq","binary_chord","binary_euclidean","binary_hamming","binary_jaccard","binary_lennon","binary_ochiai","binary_otu_gain","binary_pearson","binary_sorensen_dice","bray_curtis","bray_curtis_faith","bray_curtis_magurran","canberra","chisq","chord","euclidean","gower","hellinger","kulczynski","manhattan","morisita_horn","pearson","soergel","spearman_approx","specprof","unifrac","unifrac_g","unifrac_g_full_tree","unweighted_unifrac","unweighted_unifrac_full_tree","weighted_normalized_unifrac","weighted_unifrac"]',
        false,
        '"binary_jaccard"',
        51,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (11, 'tree', 'string', false, '', 52, NULL, false);

INSERT INTO
    qiita.command_parameter
VALUES
    (
        11,
        'num_steps',
        'integer',
        false,
        '10',
        53,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        11,
        'min_rare_depth',
        'integer',
        false,
        '10',
        54,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        11,
        'max_rare_depth',
        'integer',
        false,
        'Default',
        55,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        11,
        'metrics',
        'mchoice:["ace","berger_parker_d","brillouin_d","chao1","chao1_ci","dominance","doubles","enspie","equitability","esty_ci","fisher_alpha","gini_index","goods_coverage","heip_e","kempton_taylor_q","margalef","mcintosh_d","mcintosh_e","menhinick","michaelis_menten_fit","observed_otus","observed_species","osd","simpson_reciprocal","robbins","shannon","simpson","simpson_e","singles","strong","PD_whole_tree"]',
        false,
        '["chao1","observed_otus"]',
        56,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        12,
        'depth',
        'integer',
        true,
        NULL,
        57,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        12,
        'subsample_multinomial',
        'bool',
        false,
        'False',
        58,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        9,
        'biom_table',
        'artifact',
        true,
        NULL,
        59,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        10,
        'biom_table',
        'artifact',
        true,
        NULL,
        60,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        11,
        'biom_table',
        'artifact',
        true,
        NULL,
        61,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        12,
        'biom_table',
        'artifact',
        true,
        NULL,
        62,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (13, 'job', 'string', true, NULL, 63, NULL, false);

INSERT INTO
    qiita.command_parameter
VALUES
    (
        14,
        'artifact',
        'integer',
        true,
        NULL,
        64,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        15,
        'artifact',
        'integer',
        true,
        NULL,
        65,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        15,
        'prep_template',
        'prep_template',
        true,
        NULL,
        66,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        16,
        'artifact',
        'integer',
        true,
        NULL,
        67,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        16,
        'submission_type',
        'choice:["ADD", "MODIFY"]',
        false,
        'ADD',
        68,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        17,
        'artifact',
        'integer',
        true,
        NULL,
        69,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (18, 'fp', 'string', true, NULL, 70, NULL, false);

INSERT INTO
    qiita.command_parameter
VALUES
    (
        18,
        'study_id',
        'integer',
        true,
        NULL,
        71,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        18,
        'is_mapping_file',
        'boolean',
        false,
        'true',
        72,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        18,
        'data_type',
        'string',
        true,
        NULL,
        73,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        19,
        'study',
        'integer',
        true,
        NULL,
        74,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        19,
        'template_fp',
        'string',
        true,
        NULL,
        75,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        20,
        'study',
        'integer',
        true,
        NULL,
        76,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        21,
        'study',
        'integer',
        true,
        NULL,
        77,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        22,
        'prep_template',
        'integer',
        true,
        NULL,
        78,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        22,
        'template_fp',
        'string',
        true,
        NULL,
        79,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        23,
        'obj_class',
        'choice:["SampleTemplate", "PrepTemplate"]',
        true,
        NULL,
        80,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        23,
        'obj_id',
        'integer',
        true,
        NULL,
        81,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        23,
        'sample_or_col',
        'choice:["samples", "columns"]',
        true,
        NULL,
        82,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (23, 'name', 'string', true, NULL, 83, NULL, false);

INSERT INTO
    qiita.command_parameter
VALUES
    (
        24,
        'job_id',
        'string',
        true,
        NULL,
        84,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        24,
        'payload',
        'string',
        true,
        NULL,
        85,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        4,
        'name',
        'string',
        false,
        'default_name',
        86,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        6,
        'name',
        'string',
        false,
        'default_name',
        87,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        25,
        'analysis_id',
        'integer',
        true,
        NULL,
        88,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        6,
        'analysis',
        'analysis',
        false,
        NULL,
        89,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (26, 'url', 'string', true, NULL, 90, NULL, false);

INSERT INTO
    qiita.command_parameter
VALUES
    (
        26,
        'private_key',
        'string',
        true,
        NULL,
        91,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        26,
        'study_id',
        'integer',
        true,
        NULL,
        92,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (27, 'url', 'string', true, NULL, 93, NULL, false);

INSERT INTO
    qiita.command_parameter
VALUES
    (
        27,
        'destination',
        'string',
        true,
        NULL,
        94,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        27,
        'private_key',
        'string',
        true,
        NULL,
        95,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        28,
        'download_source',
        'choice:["EBI-ENA", "SRA"]',
        false,
        'EBI-ENA',
        96,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        28,
        'accession',
        'string',
        false,
        'None',
        97,
        NULL,
        false
    );

INSERT INTO
    qiita.command_parameter
VALUES
    (
        8,
        'categories',
        'mchoice',
        true,
        NULL,
        98,
        NULL,
        false
    );

--
-- Data for Name: controlled_vocab_values; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
--
-- Data for Name: default_parameter_set; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.default_parameter_set
VALUES
    (
        8,
        2,
        'Defaults with Golay 12 barcodes',
        '{"min_seq_len":200,"max_seq_len":1000,"trim_seq_length":false,"min_qual_score":25,"max_ambig":6,"max_homopolymer":6,"max_primer_mismatch":0,"barcode_type":"golay_12","max_barcode_errors":1.5,"disable_bc_correction":false,"qual_score_window":0,"disable_primers":false,"reverse_primers":"disable","reverse_primer_mismatches":0,"truncate_ambi_bases":false}'
    );

INSERT INTO
    qiita.default_parameter_set
VALUES
    (
        9,
        2,
        'Defaults with Hamming 8 barcodes',
        '{"min_seq_len":200,"max_seq_len":1000,"trim_seq_length":false,"min_qual_score":25,"max_ambig":6,"max_homopolymer":6,"max_primer_mismatch":0,"barcode_type":"hamming_8","max_barcode_errors":1.5,"disable_bc_correction":false,"qual_score_window":0,"disable_primers":false,"reverse_primers":"disable","reverse_primer_mismatches":0,"truncate_ambi_bases":false}'
    );

INSERT INTO
    qiita.default_parameter_set
VALUES
    (
        10,
        3,
        'Defaults',
        '{"reference":1,"sortmerna_e_value":1,"sortmerna_max_pos":10000,"similarity":0.97,"sortmerna_coverage":0.97,"threads":1}'
    );

INSERT INTO
    qiita.default_parameter_set
VALUES
    (
        11,
        1,
        'per sample FASTQ defaults, phred_offset 33',
        '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"not-barcoded","max_barcode_errors":1.5,"phred_offset":"33"}'
    );

INSERT INTO
    qiita.default_parameter_set
VALUES
    (
        12,
        1,
        'per sample FASTQ defaults, phred_offset 64',
        '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"not-barcoded","max_barcode_errors":1.5,"phred_offset":"64"}'
    );

INSERT INTO
    qiita.default_parameter_set
VALUES
    (
        1,
        1,
        'Defaults',
        '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5,"phred_offset":"auto"}'
    );

INSERT INTO
    qiita.default_parameter_set
VALUES
    (
        2,
        1,
        'Defaults with reverse complement mapping file barcodes',
        '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":true,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5,"phred_offset":"auto"}'
    );

INSERT INTO
    qiita.default_parameter_set
VALUES
    (
        3,
        1,
        'barcode_type 8, defaults',
        '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"8","max_barcode_errors":1.5,"phred_offset":"auto"}'
    );

INSERT INTO
    qiita.default_parameter_set
VALUES
    (
        4,
        1,
        'barcode_type 8, reverse complement mapping file barcodes',
        '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":true,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"8","max_barcode_errors":1.5,"phred_offset":"auto"}'
    );

INSERT INTO
    qiita.default_parameter_set
VALUES
    (
        5,
        1,
        'barcode_type 6, defaults',
        '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"6","max_barcode_errors":1.5,"phred_offset":"auto"}'
    );

INSERT INTO
    qiita.default_parameter_set
VALUES
    (
        6,
        1,
        'barcode_type 6, reverse complement mapping file barcodes',
        '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":true,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"6","max_barcode_errors":1.5,"phred_offset":"auto"}'
    );

INSERT INTO
    qiita.default_parameter_set
VALUES
    (
        7,
        1,
        'per sample FASTQ defaults',
        '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"not-barcoded","max_barcode_errors":1.5,"phred_offset":"auto"}'
    );

INSERT INTO
    qiita.default_parameter_set
VALUES
    (
        13,
        9,
        'Defaults',
        '{"sort": false, "metadata_category": ""}'
    );

INSERT INTO
    qiita.default_parameter_set
VALUES
    (
        14,
        10,
        'Unweighted UniFrac',
        '{"metric": "unweighted_unifrac", "tree": ""}'
    );

INSERT INTO
    qiita.default_parameter_set
VALUES
    (
        15,
        11,
        'Defaults',
        '{"max_rare_depth": "Default", "tree": "", "num_steps": 10, "min_rare_depth": 10, "metrics": ["chao1", "observed_otus"]}'
    );

INSERT INTO
    qiita.default_parameter_set
VALUES
    (
        16,
        12,
        'Defaults',
        '{"subsample_multinomial": "False"}'
    );

--
-- Data for Name: default_workflow; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.default_workflow
VALUES
    (
        3,
        'Per sample FASTQ upstream workflow',
        true,
        NULL,
        3,
        '{"prep": {}, "sample": {}}'
    );

INSERT INTO
    qiita.default_workflow
VALUES
    (
        1,
        'FASTQ upstream workflow',
        true,
        'This accepts html <a href="https://qiita.ucsd.edu">Qiita!</a><br/><br/><b>BYE!</b>',
        3,
        '{"prep": {}, "sample": {}}'
    );

INSERT INTO
    qiita.default_workflow
VALUES
    (
        2,
        'FASTA upstream workflow',
        true,
        'This is another description',
        3,
        '{"prep": {}, "sample": {}}'
    );

--
-- Data for Name: default_workflow_data_type; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.default_workflow_data_type
VALUES
    (1, 1);

INSERT INTO
    qiita.default_workflow_data_type
VALUES
    (1, 2);

INSERT INTO
    qiita.default_workflow_data_type
VALUES
    (2, 2);

INSERT INTO
    qiita.default_workflow_data_type
VALUES
    (3, 3);

--
-- Data for Name: default_workflow_node; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.default_workflow_node
VALUES
    (1, 1, 1);

INSERT INTO
    qiita.default_workflow_node
VALUES
    (2, 1, 10);

INSERT INTO
    qiita.default_workflow_node
VALUES
    (3, 2, 8);

INSERT INTO
    qiita.default_workflow_node
VALUES
    (4, 2, 10);

INSERT INTO
    qiita.default_workflow_node
VALUES
    (5, 3, 7);

INSERT INTO
    qiita.default_workflow_node
VALUES
    (6, 3, 10);

--
-- Data for Name: default_workflow_edge; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.default_workflow_edge
VALUES
    (1, 1, 2);

INSERT INTO
    qiita.default_workflow_edge
VALUES
    (2, 3, 4);

INSERT INTO
    qiita.default_workflow_edge
VALUES
    (3, 5, 6);

--
-- Data for Name: default_workflow_edge_connections; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.default_workflow_edge_connections
VALUES
    (1, 1, 27);

INSERT INTO
    qiita.default_workflow_edge_connections
VALUES
    (2, 2, 27);

INSERT INTO
    qiita.default_workflow_edge_connections
VALUES
    (3, 1, 27);

--
-- Data for Name: download_link; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
--
-- Data for Name: ebi_run_accession; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKB1.640202', 'ERR0000001', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKB2.640194', 'ERR0000002', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKB3.640195', 'ERR0000003', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKB4.640189', 'ERR0000004', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKB5.640181', 'ERR0000005', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKB6.640176', 'ERR0000006', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKB7.640196', 'ERR0000007', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKB8.640193', 'ERR0000008', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKB9.640200', 'ERR0000009', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKD1.640179', 'ERR0000010', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKD2.640178', 'ERR0000011', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKD3.640198', 'ERR0000012', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKD4.640185', 'ERR0000013', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKD5.640186', 'ERR0000014', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKD6.640190', 'ERR0000015', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKD7.640191', 'ERR0000016', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKD8.640184', 'ERR0000017', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKD9.640182', 'ERR0000018', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKM1.640183', 'ERR0000019', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKM2.640199', 'ERR0000020', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKM3.640197', 'ERR0000021', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKM4.640180', 'ERR0000022', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKM5.640177', 'ERR0000023', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKM6.640187', 'ERR0000024', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKM7.640188', 'ERR0000025', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKM8.640201', 'ERR0000026', 2);

INSERT INTO
    qiita.ebi_run_accession
VALUES
    ('1.SKM9.640192', 'ERR0000027', 2);

--
-- Data for Name: environmental_package; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.environmental_package
VALUES
    ('air', 'ep_air');

INSERT INTO
    qiita.environmental_package
VALUES
    ('built environment', 'ep_built_environment');

INSERT INTO
    qiita.environmental_package
VALUES
    ('host-associated', 'ep_host_associated');

INSERT INTO
    qiita.environmental_package
VALUES
    ('human-amniotic-fluid', 'ep_human_amniotic_fluid');

INSERT INTO
    qiita.environmental_package
VALUES
    ('human-associated', 'ep_human_associated');

INSERT INTO
    qiita.environmental_package
VALUES
    ('human-blood', 'ep_human_blood');

INSERT INTO
    qiita.environmental_package
VALUES
    ('human-gut', 'ep_human_gut');

INSERT INTO
    qiita.environmental_package
VALUES
    ('human-oral', 'ep_human_oral');

INSERT INTO
    qiita.environmental_package
VALUES
    ('human-skin', 'ep_human_skin');

INSERT INTO
    qiita.environmental_package
VALUES
    ('human-urine', 'ep_human_urine');

INSERT INTO
    qiita.environmental_package
VALUES
    ('human-vaginal', 'ep_human_vaginal');

INSERT INTO
    qiita.environmental_package
VALUES
    (
        'microbial mat/biofilm',
        'ep_microbial_mat_biofilm'
    );

INSERT INTO
    qiita.environmental_package
VALUES
    (
        'miscellaneous natural or artificial environment',
        'ep_misc_artif'
    );

INSERT INTO
    qiita.environmental_package
VALUES
    ('plant-associated', 'ep_plant_associated');

INSERT INTO
    qiita.environmental_package
VALUES
    ('sediment', 'ep_sediment');

INSERT INTO
    qiita.environmental_package
VALUES
    ('soil', 'ep_soil');

INSERT INTO
    qiita.environmental_package
VALUES
    ('wastewater/sludge', 'ep_wastewater_sludge');

INSERT INTO
    qiita.environmental_package
VALUES
    ('water', 'ep_water');

--
-- Data for Name: investigation; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.investigation
VALUES
    (
        1,
        'TestInvestigation',
        'An investigation for testing purposes',
        3
    );

--
-- Data for Name: investigation_study; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.investigation_study
VALUES
    (1, 1);

--
-- Data for Name: message; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.message
VALUES
    (
        1,
        'message 1',
        '2024-05-03 12:08:36.627074',
        NULL
    );

INSERT INTO
    qiita.message
VALUES
    (
        2,
        'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque sed auctor ex, non placerat sapien. Vestibulum vestibulum massa ut sapien condimentum, cursus consequat diam sodales. Nulla aliquam arcu ut massa auctor, et vehicula mauris tempor. In lacinia viverra ante quis pellentesque. Nunc vel mi accumsan, porttitor eros ut, pharetra elit. Nulla ac nisi quis dui egestas malesuada vitae ut mauris. Morbi blandit non nisl a finibus. In erat velit, congue at ipsum sit amet, venenatis bibendum sem. Curabitur vel odio sed est rutrum rutrum. Quisque efficitur ut purus in ultrices. Pellentesque eu auctor justo.',
        '2024-05-03 12:08:36.627074',
        NULL
    );

INSERT INTO
    qiita.message
VALUES
    (
        3,
        'message <a href="#">3</a>',
        '2024-05-03 12:08:36.627074',
        NULL
    );

--
-- Data for Name: message_user; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.message_user
VALUES
    ('test@foo.bar', 1, false);

INSERT INTO
    qiita.message_user
VALUES
    ('shared@foo.bar', 1, false);

INSERT INTO
    qiita.message_user
VALUES
    ('test@foo.bar', 2, false);

INSERT INTO
    qiita.message_user
VALUES
    ('test@foo.bar', 3, false);

--
-- Data for Name: oauth_identifiers; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.oauth_identifiers
VALUES
    (
        '8mL2V1gX1kK0gXuKpEhIhzaiVxrhLvJ0OjHkeqJHKjG3d6abU2',
        'qbQolcKEJ64I4jUbMxILwuTFb7IOXlYMG78QnqgtvlpIEQdiGWLUmKplz2qfnZwy7d7hqjc73qntzKTONhY27wT6cKohnNuPuKMCTLOQgrJvD6eJ2lKWH1pZeGM2zMLucZcSzlTQjYhiZruUbMeZ13GjsuFBjyVOzF8HP4cQ4xQuA1Fr8N4Yf9yQn5VqcA1byCnMWaPV95FFokdUlFCUGGEeJVRKbEn5t7qAgUlwz0B6quZICHtpiKuVDl8lNZm'
    );

INSERT INTO
    qiita.oauth_identifiers
VALUES
    (
        'ROeSvinuTLAggxQLrsa6ycCw0ZvbYaPk8DYHB5fb8J6CM3CavA',
        'vvbBSxs2su0Vcx4Qt4pwgCGkiq7bOemXnxDhsntSTxj9PAIFyDFOG1rNxj9xPhF8ugPxacilgs5PrRj93mYhnKHSTvMM9ksfQ6GmV3GvtCX0gAAjtE29ChyT0DZzOhwumke2ip9lumyZbYZhWAgWyyuzCmsKqvNjAXJfY70juQaGn3ySTmNXtqnVT7HYmSJYsqY07FLuL0CV696dsrbEOBja8Xi6nlhkiQ4g6d2UI55PdqMEz1J0zKnLNiQirGL'
    );

INSERT INTO
    qiita.oauth_identifiers
VALUES
    (
        'CTjfltNkjT7zpR9zvXqyhmaFPsaK4kml2x1gEuxfbv5oBCbFvn',
        'uvkbakS8Zwdcd4LQUiC5rUbwAgvN6WIY8wex12Ve3sFEkeplwjxb3lTid76tpPfSGKmm3gGmfXberwtQ9Qjns82NC3x9qXZ1E85M3IXXP7DZQC1kHY24V6ftx7pJCFfTjSJEhHeZLV5Uigz08Oclo3uQCkDBWBeE42QHg9XHgIy7yeW90Z9OFPfucEWnMdodSuGAhoxtkpCK6t1QsVO1cXOrY0Vk3Yay3TrAqOpfW6008FFRzakbOqKRfTVTlrg'
    );

INSERT INTO
    qiita.oauth_identifiers
VALUES
    (
        'DWelYzEYJYcZ4wlqUp0bHGXojrvZVz0CNBJvOqUKcrPQ5p4UqE',
        NULL
    );

INSERT INTO
    qiita.oauth_identifiers
VALUES
    (
        '19ndkO3oMKsoChjVVWluF7QkxHRfYhTKSFbAVt8IhK7gZgDaO4',
        'J7FfQ7CQdOxuKhQAf1eoGgBAE81Ns8Gu3EKaWFm3IO2JKhAmmCWZuabe0O5Mp28s1'
    );

INSERT INTO
    qiita.oauth_identifiers
VALUES
    (
        'yKDgajoKn5xlOA8tpo48Rq8mWJkH9z4LBCx2SvqWYLIryaan2u',
        '9xhU5rvzq8dHCEI5sSN95jesUULrZi6pT6Wuc71fDbFbsrnWarcSq56TJLN4kP4hH'
    );

INSERT INTO
    qiita.oauth_identifiers
VALUES
    (
        'dHgaXDwq665ksFPqfIoD3Jt8KRXdSioTRa4lGa5mGDnz6JTIBf',
        'xqx61SD4M2EWbaS0WYv3H1nIemkvEAMIn16XMLjy5rTCqi7opCcWbfLINEwtV48bQ'
    );

INSERT INTO
    qiita.oauth_identifiers
VALUES
    (
        '4MOBzUBHBtUmwhaC258H7PS0rBBLyGQrVxGPgc9g305bvVhf6h',
        'rFb7jwAb3UmSUN57Bjlsi4DTl2owLwRpwCc0SggRNEVb2Ebae2p5Umnq20rNMhmqN'
    );

--
-- Data for Name: oauth_software; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.oauth_software
VALUES
    (
        1,
        'yKDgajoKn5xlOA8tpo48Rq8mWJkH9z4LBCx2SvqWYLIryaan2u'
    );

INSERT INTO
    qiita.oauth_software
VALUES
    (
        2,
        'dHgaXDwq665ksFPqfIoD3Jt8KRXdSioTRa4lGa5mGDnz6JTIBf'
    );

INSERT INTO
    qiita.oauth_software
VALUES
    (
        3,
        '4MOBzUBHBtUmwhaC258H7PS0rBBLyGQrVxGPgc9g305bvVhf6h'
    );

--
-- Data for Name: ontology; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.ontology
VALUES
    (
        999999999,
        'ENA',
        true,
        'European Nucleotide Archive Submission Ontology',
        NULL,
        'http://www.ebi.ac.uk/embl/Documentation/ENA-Reads.html',
        'The ENA CV is to be used to annotate XML submissions to the ENA.',
        '2009-02-23'
    );

--
-- Data for Name: parameter_artifact_type; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.parameter_artifact_type
VALUES
    (1, 3);

INSERT INTO
    qiita.parameter_artifact_type
VALUES
    (1, 5);

INSERT INTO
    qiita.parameter_artifact_type
VALUES
    (11, 1);

INSERT INTO
    qiita.parameter_artifact_type
VALUES
    (11, 2);

INSERT INTO
    qiita.parameter_artifact_type
VALUES
    (11, 4);

INSERT INTO
    qiita.parameter_artifact_type
VALUES
    (27, 6);

INSERT INTO
    qiita.parameter_artifact_type
VALUES
    (59, 7);

INSERT INTO
    qiita.parameter_artifact_type
VALUES
    (60, 7);

INSERT INTO
    qiita.parameter_artifact_type
VALUES
    (61, 7);

INSERT INTO
    qiita.parameter_artifact_type
VALUES
    (62, 7);

--
-- Data for Name: parent_artifact; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.parent_artifact
VALUES
    (2, 1);

INSERT INTO
    qiita.parent_artifact
VALUES
    (3, 1);

INSERT INTO
    qiita.parent_artifact
VALUES
    (4, 2);

INSERT INTO
    qiita.parent_artifact
VALUES
    (5, 2);

INSERT INTO
    qiita.parent_artifact
VALUES
    (6, 2);

INSERT INTO
    qiita.parent_artifact
VALUES
    (9, 8);

--
-- Data for Name: parent_processing_job; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.parent_processing_job
VALUES
    (
        'b72369f9-a886-4193-8d3d-f7b504168e75',
        'd19f76ee-274e-4c1b-b3a2-a12d73507c55'
    );

--
-- Data for Name: study_tags; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
--
-- Data for Name: per_study_tags; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
--
-- Data for Name: prep_1; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.prep_1
VALUES
    (
        'qiita_sample_column_names',
        '{"columns": ["barcode", "library_construction_protocol", "primer", "target_subfragment", "target_gene", "run_center", "run_prefix", "run_date", "experiment_center", "experiment_design_description", "experiment_title", "platform", "instrument_model", "samp_size", "sequencing_meth", "illumina_technology", "sample_center", "pcr_primers", "study_center", "center_name", "center_project_name", "emp_status"]}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKB1.640202',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "GTCCGCAAGTTA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKB2.640194',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CGTAGAGCTCTC", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKB3.640195',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CCTCTGAGAGCT", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKB4.640189',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CCTCGATGCAGT", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKB5.640181',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "GCGGACTATTCA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKB6.640176',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CGTGCACAATTG", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKB7.640196',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CGGCCTAAGTTC", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKB8.640193',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "AGCGCTCACATC", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKB9.640200',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "TGGTTATGGCAC", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKD1.640179',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CGAGGTTCTGAT", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKD2.640178',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "AACTCCTGTGGA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKD3.640198',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "TAATGGTCGTAG", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKD4.640185',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "TTGCACCGTCGA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKD5.640186',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "TGCTACAGACGT", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKD6.640190',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "ATGGCCTGACTA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKD7.640191',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "ACGCACATACAA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKD8.640184',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "TGAGTGGTCTGT", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKD9.640182',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "GATAGCACTCGT", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKM1.640183',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "TAGCGCGAACTT", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKM2.640199',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CATACACGCACC", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKM3.640197',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "ACCTCAGTCAAG", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKM4.640180',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "TCGACCAAACAC", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKM5.640177',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CCACCCAGTAAC", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKM6.640187',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "ATATCGCGATGA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKM7.640188',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CGCCGGTAATCT", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKM8.640201',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CCGATGCCTTGA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_1
VALUES
    (
        '1.SKM9.640192',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "AGCAGGCACGAA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

--
-- Data for Name: prep_2; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.prep_2
VALUES
    (
        'qiita_sample_column_names',
        '{"columns": ["barcode", "library_construction_protocol", "primer", "target_subfragment", "target_gene", "run_center", "run_prefix", "run_date", "experiment_center", "experiment_design_description", "experiment_title", "platform", "instrument_model", "samp_size", "sequencing_meth", "illumina_technology", "sample_center", "pcr_primers", "study_center", "center_name", "center_project_name", "emp_status"]}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKB1.640202',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "GTCCGCAAGTTA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKB2.640194',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CGTAGAGCTCTC", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKB3.640195',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CCTCTGAGAGCT", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKB4.640189',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CCTCGATGCAGT", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKB5.640181',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "GCGGACTATTCA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKB6.640176',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CGTGCACAATTG", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKB7.640196',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CGGCCTAAGTTC", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKB8.640193',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "AGCGCTCACATC", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKB9.640200',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "TGGTTATGGCAC", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKD1.640179',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CGAGGTTCTGAT", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKD2.640178',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "AACTCCTGTGGA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKD3.640198',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "TAATGGTCGTAG", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKD4.640185',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "TTGCACCGTCGA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKD5.640186',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "TGCTACAGACGT", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKD6.640190',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "ATGGCCTGACTA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKD7.640191',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "ACGCACATACAA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKD8.640184',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "TGAGTGGTCTGT", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKD9.640182',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "GATAGCACTCGT", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKM1.640183',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "TAGCGCGAACTT", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKM2.640199',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CATACACGCACC", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKM3.640197',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "ACCTCAGTCAAG", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKM4.640180',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "TCGACCAAACAC", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKM5.640177',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CCACCCAGTAAC", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKM6.640187',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "ATATCGCGATGA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKM7.640188',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CGCCGGTAATCT", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKM8.640201',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "CCGATGCCTTGA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

INSERT INTO
    qiita.prep_2
VALUES
    (
        '1.SKM9.640192',
        '{"primer": "GTGCCAGCMGCCGCGGTAA", "barcode": "AGCAGGCACGAA", "platform": "Illumina", "run_date": "8/1/12", "samp_size": ".25,g", "emp_status": "EMP", "run_center": "ANL", "run_prefix": "s_G1_L001_sequences", "center_name": "ANL", "pcr_primers": "FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT", "target_gene": "16S rRNA", "study_center": "CCME", "sample_center": "ANL", "sequencing_meth": "Sequencing by synthesis", "experiment_title": "Cannabis Soil Microbiome", "instrument_model": "Illumina MiSeq", "experiment_center": "ANL", "target_subfragment": "V4", "center_project_name": null, "illumina_technology": "MiSeq", "experiment_design_description": "micro biome of soil and rhizosphere of cannabis plants from CA", "library_construction_protocol": "This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions."}'
    );

--
-- Data for Name: prep_template; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.prep_template
VALUES
    (
        2,
        2,
        'success',
        'Metagenomics',
        7,
        'Prep information 2',
        false,
        '2024-05-03 12:08:37.549542',
        '2024-05-03 12:08:37.549542',
        NULL
    );

INSERT INTO
    qiita.prep_template
VALUES
    (
        1,
        2,
        'success',
        'Metagenomics',
        1,
        'Prep information 1',
        false,
        '1970-01-01 00:00:00',
        '1970-01-01 00:00:00',
        NULL
    );

--
-- Data for Name: prep_template_filepath; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.prep_template_filepath
VALUES
    (1, 18);

INSERT INTO
    qiita.prep_template_filepath
VALUES
    (1, 19);

INSERT INTO
    qiita.prep_template_filepath
VALUES
    (1, 20);

INSERT INTO
    qiita.prep_template_filepath
VALUES
    (1, 21);

--
-- Data for Name: prep_template_processing_job; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
--
-- Data for Name: prep_template_sample; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKB8.640193', 'ERX0000000');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKD8.640184', 'ERX0000001');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKB7.640196', 'ERX0000002');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKM9.640192', 'ERX0000003');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKM4.640180', 'ERX0000004');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKM5.640177', 'ERX0000005');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKB5.640181', 'ERX0000006');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKD6.640190', 'ERX0000007');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKB2.640194', 'ERX0000008');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKD2.640178', 'ERX0000009');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKM7.640188', 'ERX0000010');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKB1.640202', 'ERX0000011');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKD1.640179', 'ERX0000012');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKD3.640198', 'ERX0000013');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKM8.640201', 'ERX0000014');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKM2.640199', 'ERX0000015');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKB9.640200', 'ERX0000016');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKD5.640186', 'ERX0000017');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKM3.640197', 'ERX0000018');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKD9.640182', 'ERX0000019');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKB4.640189', 'ERX0000020');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKD7.640191', 'ERX0000021');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKM6.640187', 'ERX0000022');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKD4.640185', 'ERX0000023');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKB3.640195', 'ERX0000024');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKB6.640176', 'ERX0000025');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (1, '1.SKM1.640183', 'ERX0000026');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKB8.640193', 'ERX0000000');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKD8.640184', 'ERX0000001');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKB7.640196', 'ERX0000002');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKM9.640192', 'ERX0000003');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKM4.640180', 'ERX0000004');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKM5.640177', 'ERX0000005');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKB5.640181', 'ERX0000006');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKD6.640190', 'ERX0000007');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKB2.640194', 'ERX0000008');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKD2.640178', 'ERX0000009');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKM7.640188', 'ERX0000010');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKB1.640202', 'ERX0000011');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKD1.640179', 'ERX0000012');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKD3.640198', 'ERX0000013');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKM8.640201', 'ERX0000014');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKM2.640199', 'ERX0000015');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKB9.640200', 'ERX0000016');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKD5.640186', 'ERX0000017');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKM3.640197', 'ERX0000018');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKD9.640182', 'ERX0000019');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKB4.640189', 'ERX0000020');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKD7.640191', 'ERX0000021');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKM6.640187', 'ERX0000022');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKD4.640185', 'ERX0000023');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKB3.640195', 'ERX0000024');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKB6.640176', 'ERX0000025');

INSERT INTO
    qiita.prep_template_sample
VALUES
    (2, '1.SKM1.640183', 'ERX0000026');

--
-- Data for Name: preparation_artifact; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.preparation_artifact
VALUES
    (1, 1);

INSERT INTO
    qiita.preparation_artifact
VALUES
    (1, 2);

INSERT INTO
    qiita.preparation_artifact
VALUES
    (1, 3);

INSERT INTO
    qiita.preparation_artifact
VALUES
    (1, 4);

INSERT INTO
    qiita.preparation_artifact
VALUES
    (1, 5);

INSERT INTO
    qiita.preparation_artifact
VALUES
    (1, 6);

INSERT INTO
    qiita.preparation_artifact
VALUES
    (2, 7);

--
-- Data for Name: processing_job_resource_allocation; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'REGISTER',
        'single-core-8gb',
        'REGISTER',
        '-p qiita -N 1 -n 1 --mem-per-cpu 8gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'default',
        'single-core-8gb',
        'RELEASE_VALIDATORS_RESOURCE_PARAM',
        '-p qiita -N 1 -n 1 --mem-per-cpu 8gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'default',
        'single-core-8gb',
        'COMPLETE_JOBS_RESOURCE_PARAM',
        '-p qiita -N 1 -n 1 --mem-per-cpu 8gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'default',
        'multi-core-vlow',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 5 --mem-per-cpu 8gb --time 168:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'delete_analysis',
        'single-core-8gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem-per-cpu 8gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Calculate beta correlation',
        'single-core-8gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem-per-cpu 8gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'delete_sample_template',
        'single-core-8gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem-per-cpu 8gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'delete_study',
        'single-core-8gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem-per-cpu 8gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'delete_sample_or_column',
        'single-core-8gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem-per-cpu 8gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'create_sample_template',
        'single-core-8gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem-per-cpu 8gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'update_prep_template',
        'single-core-8gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem-per-cpu 8gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'copy_artifact',
        'single-core-8gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem-per-cpu 8gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'delete_artifact',
        'single-core-8gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem-per-cpu 8gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'download_remote_files',
        'single-core-8gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem-per-cpu 8gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'list_remote_files',
        'single-core-8gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem-per-cpu 8gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'submit_to_EBI',
        'single-core-8gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem-per-cpu 8gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Generate HTML summary',
        'single-core-8gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem-per-cpu 8gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'update_sample_template',
        'single-core-16gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem 16gb --time 10:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'build_analysis_files',
        'single-core-16gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem 16gb --time 10:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Custom-axis Emperor plot',
        'single-core-16gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem 16gb --time 10:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Calculate alpha correlation',
        'single-core-16gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem 16gb --time 10:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Summarize taxa',
        'single-core-16gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem 16gb --time 10:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Perform Principal Coordinates Analysis (PCoA)',
        'single-core-16gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem 16gb --time 10:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Split libraries',
        'single-core-56gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem 60gb --time 25:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Calculate alpha diversity',
        'single-core-56gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem 60gb --time 25:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Calculate beta diversity',
        'single-core-56gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem 60gb --time 25:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Calculate beta group significance',
        'single-core-56gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem 60gb --time 25:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Filter samples by metadata',
        'single-core-56gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem 60gb --time 25:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Rarefy features',
        'single-core-56gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem 60gb --time 25:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Validate',
        'single-core-56gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem 60gb --time 25:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Trimming',
        'single-core-120gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem 120gb --time 80:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Split libraries FASTQ',
        'single-core-120gb',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 1 --mem 120gb --time 80:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Deblur',
        'multi-core-low',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 5 --mem 96gb --time 130:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Shogun',
        'multi-core-low',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 5 --mem 96gb --time 130:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Pick closed-reference OTUs',
        'multi-core-high',
        'RESOURCE_PARAMS_COMMAND',
        '-p qiita -N 1 -n 5 --mem 120gb --time 130:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Pick closed-reference OTUs',
        'single-core-24gb',
        'RELEASE_VALIDATORS_RESOURCE_PARAM',
        '-p qiita -N 1 -n 1 --mem 24gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Trimming',
        'single-core-24gb',
        'RELEASE_VALIDATORS_RESOURCE_PARAM',
        '-p qiita -N 1 -n 1 --mem 24gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Filter samples by metadata',
        'single-core-24gb',
        'RELEASE_VALIDATORS_RESOURCE_PARAM',
        '-p qiita -N 1 -n 1 --mem 24gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Rarefy features',
        'single-core-24gb',
        'RELEASE_VALIDATORS_RESOURCE_PARAM',
        '-p qiita -N 1 -n 1 --mem 24gb --time 50:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'BIOM',
        'single-core-16gb',
        'COMPLETE_JOBS_RESOURCE_PARAM',
        '-p qiita -N 1 -n 1 --mem 16gb --time 10:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'alpha_vector',
        'single-core-16gb',
        'COMPLETE_JOBS_RESOURCE_PARAM',
        '-p qiita -N 1 -n 1 --mem 16gb --time 10:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'distance_matrix',
        'single-core-16gb',
        'COMPLETE_JOBS_RESOURCE_PARAM',
        '-p qiita -N 1 -n 1 --mem 16gb --time 10:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Demultiplexed',
        'single-core-16gb',
        'COMPLETE_JOBS_RESOURCE_PARAM',
        '-p qiita -N 1 -n 1 --mem 16gb --time 10:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'ordination_results',
        'single-core-16gb',
        'COMPLETE_JOBS_RESOURCE_PARAM',
        '-p qiita -N 1 -n 1 --mem 16gb --time 10:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'q2_visualization',
        'single-core-16gb',
        'COMPLETE_JOBS_RESOURCE_PARAM',
        '-p qiita -N 1 -n 1 --mem 16gb --time 10:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'default',
        NULL,
        'VALIDATOR',
        '-p qiita -N 1 -n 1 --mem 1gb --time 4:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'per_sample_FASTQ',
        NULL,
        'VALIDATOR',
        '-p qiita -N 1 -n 5 --mem 2gb --time 10:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'ordination_results',
        NULL,
        'VALIDATOR',
        '-p qiita -N 1 -n 1 --mem 10gb --time 2:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'Demultiplexed',
        NULL,
        'VALIDATOR',
        '-p qiita -N 1 -n 5 --mem 25gb --time 150:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'distance_matrix',
        NULL,
        'VALIDATOR',
        '-p qiita -N 1 -n 1 --mem 42gb --time 150:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'BIOM',
        NULL,
        'VALIDATOR',
        '-p qiita -N 1 -n 1 --mem 90gb --time 150:00:00'
    );

INSERT INTO
    qiita.processing_job_resource_allocation
VALUES
    (
        'alpha_vector',
        NULL,
        'VALIDATOR',
        '-p qiita -N 1 -n 1 --mem 10gb --time 70:00:00'
    );

--
-- Data for Name: processing_job_validator; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
--
-- Data for Name: processing_job_workflow; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.processing_job_workflow
VALUES
    (
        1,
        'shared@foo.bar',
        'Testing processing workflow'
    );

INSERT INTO
    qiita.processing_job_workflow
VALUES
    (2, 'test@foo.bar', 'Single node workflow');

--
-- Data for Name: processing_job_workflow_root; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.processing_job_workflow_root
VALUES
    (1, 'b72369f9-a886-4193-8d3d-f7b504168e75');

INSERT INTO
    qiita.processing_job_workflow_root
VALUES
    (2, 'ac653cb5-76a6-4a45-929e-eb9b2dee6b63');

--
-- Data for Name: publication; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.publication
VALUES
    ('10.1038/nmeth.f.303', '20383131');

INSERT INTO
    qiita.publication
VALUES
    ('10.1186/2047-217X-1-7', '23587224');

INSERT INTO
    qiita.publication
VALUES
    ('10.100/123456', '123456');

INSERT INTO
    qiita.publication
VALUES
    ('10.100/7891011', '7891011');

--
-- Data for Name: reference; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.reference
VALUES
    (1, 'Greengenes', '13_8', 6, 7, 8);

INSERT INTO
    qiita.reference
VALUES
    (2, 'Silva', 'test', 10, 11, NULL);

--
-- Data for Name: restrictions; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.restrictions
VALUES
    (
        'study_sample',
        'env_package',
        '{air,"built environment",host-associated,human-associated,human-skin,human-oral,human-gut,human-vaginal,"microbial mat/biofilm","misc environment",plant-associated,sediment,soil,wastewater/sludge,water}'
    );

INSERT INTO
    qiita.restrictions
VALUES
    (
        'prep_template_sample',
        'target_gene',
        '{"16S rRNA","18S rRNA",ITS1/2,LSU}'
    );

INSERT INTO
    qiita.restrictions
VALUES
    (
        'prep_template_sample',
        'target_subfragment',
        '{V3,V4,V6,V9,ITS1/2}'
    );

INSERT INTO
    qiita.restrictions
VALUES
    (
        'prep_template_sample',
        'instrument_model',
        '{"454 GS","454 GS 20","454 GS FLX","454 GS FLX+","454 GS FLX Titanium","454 GS Junior","DNBSEQ-G400","DNBSEQ-T7","DNBSEQ-G800","Illumina Genome Analyzer","Illumina Genome Analyzer II","Illumina Genome Analyzer IIx","Illumina HiScanSQ","Illumina HiSeq 1000","Illumina HiSeq 1500","Illumina HiSeq 2000","Illumina HiSeq 2500","Illumina HiSeq 3000","Illumina HiSeq 4000","Illumina MiSeq","Illumina MiniSeq","Illumina NovaSeq 6000","NextSeq 500","NextSeq 550","Ion Torrent PGM","Ion Torrent Proton","Ion Torrent S5","Ion Torrent S5 XL",MinION,GridION,PromethION,unspecified}'
    );

INSERT INTO
    qiita.restrictions
VALUES
    (
        'prep_template_sample',
        'platform',
        '{DNBSEQ,FASTA,Illumina,Ion_Torrent,LS454,"Oxford Nanopore"}'
    );

--
-- Data for Name: sample_1; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.sample_1
VALUES
    (
        'qiita_sample_column_names',
        '{"columns": ["season_environment", "assigned_from_geo", "texture", "taxon_id", "depth", "host_taxid", "common_name", "water_content_soil", "elevation", "temp", "tot_nitro", "samp_salinity", "altitude", "env_biome", "country", "ph", "anonymized_name", "tot_org_carb", "description_duplicate", "env_feature", "physical_specimen_location", "physical_specimen_remaining", "dna_extracted", "sample_type", "env_package", "collection_timestamp", "host_subject_id", "description", "latitude", "longitude", "scientific_name"]}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKM7.640188',
        '{"ph": "6.82", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "63.1 sand, 17.7 silt, 19.2 clay", "altitude": "0", "latitude": "60.1102854322", "taxon_id": "1118232", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "74.7123248382", "tot_nitro": "1.3", "host_taxid": "3483", "common_name": "root metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "3.31", "dna_extracted": "true", "samp_salinity": "7.44", "anonymized_name": "SKM7", "host_subject_id": "1001:B6", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.101", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Bucu Roots", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKD9.640182',
        '{"ph": "6.82", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "66 sand, 16.3 silt, 17.7 clay", "altitude": "0", "latitude": "23.1218032799", "taxon_id": "1118232", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "42.838497795", "tot_nitro": "1.51", "host_taxid": "3483", "common_name": "root metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "4.32", "dna_extracted": "true", "samp_salinity": "7.1", "anonymized_name": "SKD9", "host_subject_id": "1001:D3", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.178", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Diesel Root", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKM8.640201',
        '{"ph": "6.82", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "63.1 sand, 17.7 silt, 19.2 clay", "altitude": "0", "latitude": "3.21190859967", "taxon_id": "1118232", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "26.8138925876", "tot_nitro": "1.3", "host_taxid": "3483", "common_name": "root metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "3.31", "dna_extracted": "true", "samp_salinity": "7.44", "anonymized_name": "SKM8", "host_subject_id": "1001:D8", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.101", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Bucu Roots", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKB8.640193',
        '{"ph": "6.94", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "64.6 sand, 17.6 silt, 17.8 clay", "altitude": "0", "latitude": "74.0894932572", "taxon_id": "1118232", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "65.3283470202", "tot_nitro": "1.41", "host_taxid": "3483", "common_name": "root metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "5", "dna_extracted": "true", "samp_salinity": "7.15", "anonymized_name": "SKB8", "host_subject_id": "1001:M7", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.164", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Burmese root", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKD2.640178',
        '{"ph": "6.8", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "66 sand, 16.3 silt, 17.7 clay", "altitude": "0", "latitude": "53.5050692395", "taxon_id": "410658", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "31.6056761814", "tot_nitro": "1.51", "host_taxid": "3483", "common_name": "soil metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "4.32", "dna_extracted": "true", "samp_salinity": "7.1", "anonymized_name": "SKD2", "host_subject_id": "1001:B5", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.178", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Diesel bulk", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKM3.640197',
        '{"ph": "6.82", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "63.1 sand, 17.7 silt, 19.2 clay", "altitude": "0", "latitude": "Not applicable", "taxon_id": "410658", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "31.2003474585", "tot_nitro": "1.3", "host_taxid": "3483", "common_name": "soil metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "3.31", "dna_extracted": "true", "samp_salinity": "7.44", "anonymized_name": "SKM3", "host_subject_id": "1001:B7", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.101", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Bucu bulk", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKM4.640180',
        '{"ph": "6.82", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "63.1 sand, 17.7 silt, 19.2 clay", "altitude": "0", "latitude": "Not applicable", "taxon_id": "939928", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "Not applicable", "tot_nitro": "1.3", "host_taxid": "3483", "common_name": "rhizosphere metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "3.31", "dna_extracted": "true", "samp_salinity": "7.44", "anonymized_name": "SKM4", "host_subject_id": "1001:D2", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.101", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Bucu Rhizo", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKB9.640200',
        '{"ph": "6.8", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "64.6 sand, 17.6 silt, 17.8 clay", "altitude": "0", "latitude": "12.6245524972", "taxon_id": "1118232", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "96.0693176066", "tot_nitro": "1.41", "host_taxid": "3483", "common_name": "root metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "5", "dna_extracted": "true", "samp_salinity": "7.15", "anonymized_name": "SKB9", "host_subject_id": "1001:B3", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.164", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Burmese root", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKB4.640189',
        '{"ph": "6.94", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "64.6 sand, 17.6 silt, 17.8 clay", "altitude": "0", "latitude": "43.9614715197", "taxon_id": "939928", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "82.8516734159", "tot_nitro": "1.41", "host_taxid": "3483", "common_name": "rhizosphere metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "5", "dna_extracted": "true", "samp_salinity": "7.15", "anonymized_name": "SKB4", "host_subject_id": "1001:D7", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.164", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Burmese Rhizo", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKB5.640181',
        '{"ph": "6.94", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "64.6 sand, 17.6 silt, 17.8 clay", "altitude": "0", "latitude": "10.6655599093", "taxon_id": "939928", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "70.784770579", "tot_nitro": "1.41", "host_taxid": "3483", "common_name": "rhizosphere metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "5", "dna_extracted": "true", "samp_salinity": "7.15", "anonymized_name": "SKB5", "host_subject_id": "1001:M4", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.164", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Burmese Rhizo", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKB6.640176',
        '{"ph": "6.94", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "64.6 sand, 17.6 silt, 17.8 clay", "altitude": "0", "latitude": "78.3634273709", "taxon_id": "939928", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "74.423907894", "tot_nitro": "1.41", "host_taxid": "3483", "common_name": "rhizosphere metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "5", "dna_extracted": "true", "samp_salinity": "7.15", "anonymized_name": "SKB6", "host_subject_id": "1001:D5", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.164", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Burmese Rhizo", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKM2.640199',
        '{"ph": "6.82", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "63.1 sand, 17.7 silt, 19.2 clay", "altitude": "0", "latitude": "82.8302905615", "taxon_id": "410658", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "86.3615778099", "tot_nitro": "1.3", "host_taxid": "3483", "common_name": "soil metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "3.31", "dna_extracted": "true", "samp_salinity": "7.44", "anonymized_name": "SKM2", "host_subject_id": "1001:D4", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.101", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Bucu bulk", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKM5.640177',
        '{"ph": "6.82", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "63.1 sand, 17.7 silt, 19.2 clay", "altitude": "0", "latitude": "44.9725384282", "taxon_id": "939928", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "66.1920014699", "tot_nitro": "1.3", "host_taxid": "3483", "common_name": "rhizosphere metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "3.31", "dna_extracted": "true", "samp_salinity": "7.44", "anonymized_name": "SKM5", "host_subject_id": "1001:M3", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.101", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Bucu Rhizo", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKB1.640202',
        '{"ph": "6.94", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "64.6 sand, 17.6 silt, 17.8 clay", "altitude": "0", "latitude": "4.59216095574", "taxon_id": "410658", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "63.5115213108", "tot_nitro": "1.41", "host_taxid": "3483", "common_name": "soil metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "5", "dna_extracted": "true", "samp_salinity": "7.15", "anonymized_name": "SKB1", "host_subject_id": "1001:M2", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.164", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Burmese bulk", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKD8.640184',
        '{"ph": "6.8", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "66 sand, 16.3 silt, 17.7 clay", "altitude": "0", "latitude": "57.571893782", "taxon_id": "1118232", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "32.5563076447", "tot_nitro": "1.51", "host_taxid": "3483", "common_name": "root metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "4.32", "dna_extracted": "true", "samp_salinity": "7.1", "anonymized_name": "SKD8", "host_subject_id": "1001:D9", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.178", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Diesel Root", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKD4.640185',
        '{"ph": "6.8", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "66 sand, 16.3 silt, 17.7 clay", "altitude": "0", "latitude": "40.8623799474", "taxon_id": "939928", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "6.66444220187", "tot_nitro": "1.51", "host_taxid": "3483", "common_name": "rhizosphere metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "4.32", "dna_extracted": "true", "samp_salinity": "7.1", "anonymized_name": "SKD4", "host_subject_id": "1001:M9", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.178", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Diesel Rhizo", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKB3.640195',
        '{"ph": "6.94", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "64.6 sand, 17.6 silt, 17.8 clay", "altitude": "0", "latitude": "95.2060749748", "taxon_id": "410658", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "27.3592668624", "tot_nitro": "1.41", "host_taxid": "3483", "common_name": "soil metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "5", "dna_extracted": "true", "samp_salinity": "7.15", "anonymized_name": "SKB3", "host_subject_id": "1001:M6", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.164", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Burmese bulk", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKM1.640183',
        '{"ph": "6.82", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "63.1 sand, 17.7 silt, 19.2 clay", "altitude": "0", "latitude": "38.2627021402", "taxon_id": "410658", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "3.48274264219", "tot_nitro": "1.3", "host_taxid": "3483", "common_name": "soil metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "3.31", "dna_extracted": "true", "samp_salinity": "7.44", "anonymized_name": "SKM1", "host_subject_id": "1001:D1", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.101", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Bucu bulk", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKB7.640196',
        '{"ph": "6.94", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "64.6 sand, 17.6 silt, 17.8 clay", "altitude": "0", "latitude": "13.089194595", "taxon_id": "1118232", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "92.5274472082", "tot_nitro": "1.41", "host_taxid": "3483", "common_name": "root metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "5", "dna_extracted": "true", "samp_salinity": "7.15", "anonymized_name": "SKB7", "host_subject_id": "1001:M8", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.164", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Burmese root", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKD3.640198',
        '{"ph": "6.8", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "66 sand, 16.3 silt, 17.7 clay", "altitude": "0", "latitude": "84.0030227585", "taxon_id": "410658", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "66.8954849864", "tot_nitro": "1.51", "host_taxid": "3483", "common_name": "soil metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "4.32", "dna_extracted": "true", "samp_salinity": "7.1", "anonymized_name": "SKD3", "host_subject_id": "1001:B1", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.178", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Diesel bulk", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKD7.640191',
        '{"ph": "6.8", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "66 sand, 16.3 silt, 17.7 clay", "altitude": "0", "latitude": "68.51099627", "taxon_id": "1118232", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "2.35063674718", "tot_nitro": "1.51", "host_taxid": "3483", "common_name": "root metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "4.32", "dna_extracted": "true", "samp_salinity": "7.1", "anonymized_name": "SKD7", "host_subject_id": "1001:D6", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.178", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Diesel Root", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKD6.640190',
        '{"ph": "6.8", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "66 sand, 16.3 silt, 17.7 clay", "altitude": "0", "latitude": "29.1499460692", "taxon_id": "939928", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "82.1270418227", "tot_nitro": "1.51", "host_taxid": "3483", "common_name": "rhizosphere metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "4.32", "dna_extracted": "true", "samp_salinity": "7.1", "anonymized_name": "SKD6", "host_subject_id": "1001:B9", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.178", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Diesel Rhizo", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKB2.640194',
        '{"ph": "6.94", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "64.6 sand, 17.6 silt, 17.8 clay", "altitude": "0", "latitude": "35.2374368957", "taxon_id": "410658", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "68.5041623253", "tot_nitro": "1.41", "host_taxid": "3483", "common_name": "soil metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "5", "dna_extracted": "true", "samp_salinity": "7.15", "anonymized_name": "SKB2", "host_subject_id": "1001:B4", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.164", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Burmese bulk", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKM9.640192',
        '{"ph": "6.82", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "63.1 sand, 17.7 silt, 19.2 clay", "altitude": "0", "latitude": "12.7065957714", "taxon_id": "1118232", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "84.9722975792", "tot_nitro": "1.3", "host_taxid": "3483", "common_name": "root metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "3.31", "dna_extracted": "true", "samp_salinity": "7.44", "anonymized_name": "SKM9", "host_subject_id": "1001:B8", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.101", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Bucu Roots", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKM6.640187',
        '{"ph": "6.82", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "63.1 sand, 17.7 silt, 19.2 clay", "altitude": "0", "latitude": "0.291867635913", "taxon_id": "939928", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "68.5945325743", "tot_nitro": "1.3", "host_taxid": "3483", "common_name": "rhizosphere metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "3.31", "dna_extracted": "true", "samp_salinity": "7.44", "anonymized_name": "SKM6", "host_subject_id": "1001:B2", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.101", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Bucu Rhizo", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKD5.640186',
        '{"ph": "6.8", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "66 sand, 16.3 silt, 17.7 clay", "altitude": "0", "latitude": "85.4121476399", "taxon_id": "939928", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "15.6526750776", "tot_nitro": "1.51", "host_taxid": "3483", "common_name": "rhizosphere metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "4.32", "dna_extracted": "true", "samp_salinity": "7.1", "anonymized_name": "SKD5", "host_subject_id": "1001:M1", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.178", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Diesel Rhizo", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

INSERT INTO
    qiita.sample_1
VALUES
    (
        '1.SKD1.640179',
        '{"ph": "6.8", "temp": "15", "depth": "0.15", "country": "GAZ:United States of America", "texture": "66 sand, 16.3 silt, 17.7 clay", "altitude": "0", "latitude": "68.0991287718", "taxon_id": "410658", "elevation": "114", "env_biome": "ENVO:Temperate grasslands, savannas, and shrubland biome", "longitude": "34.8360987059", "tot_nitro": "1.51", "host_taxid": "3483", "common_name": "soil metagenome", "description": "Cannabis Soil Microbiome", "env_feature": "ENVO:plant-associated habitat", "env_package": "soil", "sample_type": "ENVO:soil", "tot_org_carb": "4.32", "dna_extracted": "true", "samp_salinity": "7.1", "anonymized_name": "SKD1", "host_subject_id": "1001:M5", "scientific_name": "1118232", "assigned_from_geo": "n", "season_environment": "winter", "water_content_soil": "0.178", "collection_timestamp": "2011-11-11 13:00:00", "description_duplicate": "Diesel bulk", "physical_specimen_location": "ANL", "physical_specimen_remaining": "true"}'
    );

--
-- Data for Name: sample_template_filepath; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.sample_template_filepath
VALUES
    (1, 17);

--
-- Data for Name: software_artifact_type; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.software_artifact_type
VALUES
    (2, 7);

INSERT INTO
    qiita.software_artifact_type
VALUES
    (3, 1);

INSERT INTO
    qiita.software_artifact_type
VALUES
    (3, 3);

INSERT INTO
    qiita.software_artifact_type
VALUES
    (3, 4);

INSERT INTO
    qiita.software_artifact_type
VALUES
    (3, 2);

INSERT INTO
    qiita.software_artifact_type
VALUES
    (3, 5);

INSERT INTO
    qiita.software_artifact_type
VALUES
    (3, 6);

--
-- Data for Name: software_publication; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.software_publication
VALUES
    (1, '10.1038/nmeth.f.303');

INSERT INTO
    qiita.software_publication
VALUES
    (2, '10.1186/2047-217X-1-7');

--
-- Data for Name: stats_daily; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
--
-- Data for Name: study_artifact; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.study_artifact
VALUES
    (1, 1);

INSERT INTO
    qiita.study_artifact
VALUES
    (1, 2);

INSERT INTO
    qiita.study_artifact
VALUES
    (1, 3);

INSERT INTO
    qiita.study_artifact
VALUES
    (1, 4);

INSERT INTO
    qiita.study_artifact
VALUES
    (1, 5);

INSERT INTO
    qiita.study_artifact
VALUES
    (1, 6);

INSERT INTO
    qiita.study_artifact
VALUES
    (1, 7);

--
-- Data for Name: study_environmental_package; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.study_environmental_package
VALUES
    (1, 'soil');

INSERT INTO
    qiita.study_environmental_package
VALUES
    (1, 'plant-associated');

--
-- Data for Name: study_portal; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.study_portal
VALUES
    (1, 1);

--
-- Data for Name: study_prep_template; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.study_prep_template
VALUES
    (1, 1);

INSERT INTO
    qiita.study_prep_template
VALUES
    (1, 2);

--
-- Data for Name: study_publication; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.study_publication
VALUES
    (1, '10.100/123456', true);

INSERT INTO
    qiita.study_publication
VALUES
    (1, '123456', false);

INSERT INTO
    qiita.study_publication
VALUES
    (1, '10.100/7891011', true);

INSERT INTO
    qiita.study_publication
VALUES
    (1, '7891011', false);

--
-- Data for Name: study_users; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.study_users
VALUES
    (1, 'shared@foo.bar');

--
-- Data for Name: term; Type: TABLE DATA; Schema: qiita; Owner: antoniog
--
INSERT INTO
    qiita.term
VALUES
    (
        2052508974,
        999999999,
        NULL,
        'WGS',
        'ENA:0000059',
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        false
    );

INSERT INTO
    qiita.term
VALUES
    (
        2052508975,
        999999999,
        NULL,
        'Metagenomics',
        'ENA:0000060',
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        false
    );

INSERT INTO
    qiita.term
VALUES
    (
        2052508976,
        999999999,
        NULL,
        'AMPLICON',
        'ENA:0000061',
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        false
    );

INSERT INTO
    qiita.term
VALUES
    (
        2052508984,
        999999999,
        NULL,
        'RNA-Seq',
        'ENA:0000070',
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        false
    );

INSERT INTO
    qiita.term
VALUES
    (
        2052508987,
        999999999,
        NULL,
        'Other',
        'ENA:0000069',
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        false
    );

--
-- Name: analysis_analysis_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.analysis_analysis_id_seq', 10, true);

--
-- Name: archive_merging_scheme_archive_merging_scheme_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.archive_merging_scheme_archive_merging_scheme_id_seq',
        1,
        false
    );

--
-- Name: artifact_artifact_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.artifact_artifact_id_seq', 9, true);

--
-- Name: checksum_algorithm_checksum_algorithm_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.checksum_algorithm_checksum_algorithm_id_seq',
        1,
        true
    );

--
-- Name: column_controlled_vocabularies_controlled_vocab_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.column_controlled_vocabularies_controlled_vocab_id_seq',
        1,
        false
    );

--
-- Name: command_output_command_output_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.command_output_command_output_id_seq',
        7,
        true
    );

--
-- Name: command_parameter_command_parameter_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.command_parameter_command_parameter_id_seq',
        98,
        true
    );

--
-- Name: controlled_vocab_controlled_vocab_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.controlled_vocab_controlled_vocab_id_seq',
        1,
        false
    );

--
-- Name: controlled_vocab_values_vocab_value_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.controlled_vocab_values_vocab_value_id_seq',
        1,
        false
    );

--
-- Name: data_directory_data_directory_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.data_directory_data_directory_id_seq',
        16,
        true
    );

--
-- Name: data_type_data_type_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.data_type_data_type_id_seq', 12, true);

--
-- Name: default_parameter_set_default_parameter_set_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.default_parameter_set_default_parameter_set_id_seq',
        16,
        true
    );

--
-- Name: default_workflow_default_workflow_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.default_workflow_default_workflow_id_seq',
        3,
        true
    );

--
-- Name: default_workflow_edge_default_workflow_edge_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.default_workflow_edge_default_workflow_edge_id_seq',
        3,
        true
    );

--
-- Name: default_workflow_node_default_workflow_node_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.default_workflow_node_default_workflow_node_id_seq',
        6,
        true
    );

--
-- Name: filepath_data_directory_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.filepath_data_directory_id_seq', 1, false);

--
-- Name: filepath_filepath_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.filepath_filepath_id_seq', 22, true);

--
-- Name: filepath_type_filepath_type_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.filepath_type_filepath_type_id_seq',
        25,
        true
    );

--
-- Name: filetype_filetype_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.filetype_filetype_id_seq', 10, true);

--
-- Name: investigation_investigation_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.investigation_investigation_id_seq',
        1,
        true
    );

--
-- Name: logging_logging_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.logging_logging_id_seq', 2, true);

--
-- Name: message_message_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.message_message_id_seq', 3, true);

--
-- Name: parameter_artifact_type_command_parameter_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.parameter_artifact_type_command_parameter_id_seq',
        1,
        false
    );

--
-- Name: portal_type_portal_type_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.portal_type_portal_type_id_seq', 3, true);

--
-- Name: prep_template_prep_template_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.prep_template_prep_template_id_seq',
        2,
        true
    );

--
-- Name: processing_job_status_processing_job_status_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.processing_job_status_processing_job_status_id_seq',
        6,
        true
    );

--
-- Name: processing_job_workflow_processing_job_workflow_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.processing_job_workflow_processing_job_workflow_id_seq',
        2,
        true
    );

--
-- Name: reference_reference_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.reference_reference_id_seq', 2, true);

--
-- Name: severity_severity_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.severity_severity_id_seq', 3, true);

--
-- Name: software_command_command_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.software_command_command_id_seq', 28, true);

--
-- Name: software_software_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.software_software_id_seq', 4, true);

--
-- Name: software_type_software_type_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.software_type_software_type_id_seq',
        3,
        true
    );

--
-- Name: study_person_study_person_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.study_person_study_person_id_seq', 3, true);

--
-- Name: study_status_study_status_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.study_status_study_status_id_seq', 5, true);

--
-- Name: study_study_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.study_study_id_seq', 1, true);

--
-- Name: term_term_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.term_term_id_seq', 1, false);

--
-- Name: timeseries_type_timeseries_type_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval (
        'qiita.timeseries_type_timeseries_type_id_seq',
        10,
        true
    );

--
-- Name: user_level_user_level_id_seq; Type: SEQUENCE SET; Schema: qiita; Owner: antoniog
--
SELECT
    pg_catalog.setval ('qiita.user_level_user_level_id_seq', 7, true);

--
-- PostgreSQL database dump complete
--
