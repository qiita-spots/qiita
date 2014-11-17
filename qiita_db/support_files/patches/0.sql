-- Nov 14, 2014
-- This patch initializes the controlled values for some of the tables in the database

-- Populate user_level table
INSERT INTO qiita.user_level (name, description) VALUES ('admin', 'Can access and do all the things'), ('dev', 'Can access all data and info about errors'), ('superuser', 'Can see all studies, can run analyses'), ('user', 'Can see own and public data, can run analyses'), ('unverified', 'Email not verified'), ('guest', 'Can view & download public data');

-- Populate analysis_status table
INSERT INTO qiita.analysis_status (status) VALUES ('in_construction'), ('queued'), ('running'), ('completed'), ('error'), ('public');

-- Populate job_status table
INSERT INTO qiita.job_status (status) VALUES ('queued'), ('running'), ('completed'), ('error');

-- Populate data_type table
INSERT INTO qiita.data_type (data_type) VALUES ('16S'), ('18S'), ('ITS'), ('Proteomic'), ('Metabolomic'), ('Metagenomic');

-- Populate filetype table
INSERT INTO qiita.filetype (type) VALUES ('SFF'), ('FASTA-Sanger'), ('FASTQ');

-- Populate emp_status table
INSERT INTO qiita.emp_status (emp_status) VALUES ('EMP'), ('EMP_Processed'), ('NOT_EMP');

-- Populate study_status table
INSERT INTO qiita.study_status (status, description) VALUES ('awaiting_approval', 'Awaiting approval of metadata'), ('public', 'Anyone can see this study'), ('private', 'Only owner and shared users can see this study');

-- Populate timeseries_type table
INSERT INTO qiita.timeseries_type (timeseries_type) VALUES ('NOT_TIMESERIES'), ('TIMESERIES_1'), ('TIMESERIES_2'), ('TIMESERIES_3');

-- Populate severity table
INSERT INTO qiita.severity (severity) VALUES ('Warning'), ('Runtime'), ('Fatal');

-- Populate portal_type table
INSERT INTO qiita.portal_type (portal, description) VALUES ('QIIME', 'QIIME portal'), ('EMP', 'EMP portal'), ('QIIME_EMP', 'QIIME and EMP portals');

-- Populate sample_status table
INSERT INTO qiita.required_sample_info_status (status) VALUES ('received'), ('in_preparation'), ('running'), ('completed');

-- Populate filepath_type table
INSERT INTO qiita.filepath_type (filepath_type) VALUES ('raw_forward_seqs'), ('raw_reverse_seqs'), ('raw_barcodes'), ('preprocessed_fasta'), ('preprocessed_fastq'), ('preprocessed_demux'), ('biom'), ('directory'), ('plain_text'), ('reference_seqs'), ('reference_tax'), ('reference_tree'), ('log');

-- Populate data_directory table
INSERT INTO qiita.data_directory (data_type, mountpoint, subdirectory, active) VALUES ('analysis', 'analysis', '', true), ('job', 'job', '', true), ('preprocessed_data', 'preprocessed_data', '', true), ('processed_data', 'processed_data', '', true), ('raw_data', 'raw_data', '', true), ('reference', 'reference', '', true), ('uploads', 'uploads', '', true), ('working_dir', 'working_dir', '', true);

-- Populate checksum_algorithm table
INSERT INTO qiita.checksum_algorithm (name) VALUES ('crc32');

-- Populate commands available
INSERT INTO qiita.command (name, command, input, required, optional, output) VALUES
('Summarize Taxa', 'summarize_taxa_through_plots.py', '{"--otu_table_fp":null}', '{}', '{"--mapping_category":null, "--mapping_fp":null,"--sort":null}', '{"--output_dir":null}'),
('Beta Diversity', 'beta_diversity_through_plots.py', '{"--otu_table_fp":null,"--mapping_fp":null}', '{}', '{"--tree_fp":null,"--color_by_all_fields":null,"--seqs_per_sample":null}', '{"--output_dir":null}'),
('Alpha Rarefaction', 'alpha_rarefaction.py', '{"--otu_table_fp":null,"--mapping_fp":null}', '{}', '{"--tree_fp":null,"--num_steps":null,"--min_rare_depth":null,"--max_rare_depth":null,"--retain_intermediate_files":false}', '{"--output_dir":null}');

-- Populate command_data_type table
INSERT INTO qiita.command_data_type (command_id, data_type_id) VALUES (1,1), (1,2), (2,1), (2,2),  (2,3),  (2,4),  (2,5), (2,6), (3,1), (3,2),  (3,3),  (3,4),  (3,5), (3,6);

-- Set the autoincrementing study_id column to start at 10,000 so we don't overlap with existing (QIIME database) study IDs, which should be maintained
SELECT setval('qiita.study_study_id_seq', 10000, false);

-- Initializing preprocessed_sequence_illumina_params to have 2 rows
-- The first row has the default values on QIIME
-- The second row has the default values on QIIME but rev_comp_mapping_barcodes is set to true
INSERT INTO qiita.preprocessed_sequence_illumina_params (rev_comp_mapping_barcodes) VALUES (false), (true);
