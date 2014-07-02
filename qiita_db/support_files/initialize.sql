-- Populate user_level table 
INSERT INTO qiita.user_level (name, description) VALUES ('admin', 'Can access and do all the things'), ('dev', 'Can access all data and info about errors'), ('superuser', 'Can see all studies, can run analyses'), ('user', 'Can see own and public data, can run analyses'), ('unverified', 'Email not verified'), ('guest', 'Can view & download public data');

-- Populate analysis_status table
INSERT INTO qiita.analysis_status (status) VALUES ('in_construction'), ('queued'), ('running'), ('completed'), ('error'), ('public');

-- Populate job_status table
INSERT INTO qiita.job_status (status) VALUES ('queued'), ('running'), ('completed'), ('error');

-- Populate data_type table
INSERT INTO qiita.data_type (data_type) VALUES ('16S'), ('18S'), ('ITS'), ('Proteomic'), ('Metabolomic'), ('Metagenomic');

-- Populate filetype table
INSERT INTO qiita.filetype (type) VALUES ('FASTA'), ('FASTQ'), ('SPECTRA');

-- Populate emp_status table
INSERT INTO qiita.emp_status (emp_status) VALUES ('EMP'), ('EMP_Processed'), ('NOT_EMP');

-- Populate study_status table
INSERT INTO qiita.study_status (status, description) VALUES ('waiting_approval', 'Awaiting approval of metadata'), ('public', 'Anyone can see this study'), ('private', 'Only owner and shared users can see this study');

-- Populate timeseries_type table
INSERT INTO qiita.timeseries_type (timeseries_type) VALUES ('NOT_TIMESERIES'), ('TIMESERIES_1'), ('TIMESERIES_2');

-- Populate severity table
INSERT INTO qiita.severity (severity) VALUES ('Warning'), ('Runtime'), ('Fatal');

-- Populate portal_type table
INSERT INTO qiita.portal_type (portal, description) VALUES ('QIIME', 'QIIME portal'), ('EMP', 'EMP portal'), ('QIIME_EMP', 'QIIME and EMP portals');

-- Populate sample_status table
INSERT INTO qiita.required_sample_info_status (status) VALUES ('received'), ('in_preparation'), ('running'), ('completed');

-- Populate filepath_type table
INSERT INTO qiita.filepath_type (filepath_type) VALUES ('raw_sequences'), ('raw_barcodes'), ('raw_spectra'), ('preprocessed_sequences'), ('preprocessed_sequences_qual'), ('biom'), ('directory'), ('plain_text');

-- Populate checksum_algorithm table
INSERT INTO qiita.checksum_algorithm (name) VALUES ('crc32');

-- Populate commands available
INSERT INTO qiita.command (name, command, input, required, optional, output) VALUES 
('Summarize Taxa', 'summarize_taxa_through_plots.py', '{"--otu_table_fp":null}', '{}', '{"--mapping_category":null, "--mapping_fp":null,"--sort":null}', '{"--output_dir":null}'),
('Beta Diversity', 'beta_diversity_through_plots.py', '{"--otu_table_fp":null,"--mapping_fp":null}', '{}', '{"--tree_fp":null,"--color_by_all_fields":null,"--seqs_per_sample":null}', '{"--output_dir":null}'),
('Alpha Rarefaction', 'alpha_rarefaction.py', '{"--otu_table_fp":null,"--mapping_fp":null}', '{}', '{"--tree_fp":null,"--num_steps":null,"--min_rare_depth":null,"--max_rare_depth":null,"--retain_intermediate_files":false}', '{"--output_dir":null}');

-- Populate command_data_type table
INSERT INTO qiita.command_data_type (command_id, data_type_id) VALUES (1,1), (1,2), (2,1), (2,2),  (2,3),  (2,4),  (2,5), (2,6), (3,1), (3,3),  (3,3),  (3,4),  (3,5), (3,6);