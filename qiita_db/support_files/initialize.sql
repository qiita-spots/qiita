-- Populate user_level table 
INSERT INTO qiita.user_level (name, description) VALUES ('admin', 'Can access and do all the things'), ('dev', 'Can access all data and info about errors'), ('superuser', 'Can see all studies, can run analyses'), ('user', 'Can see own and public data, can run analyses'), ('unverified', 'Email not verified'), ('guest', 'Can view & download public data');

-- Populate analysis_status table
INSERT INTO qiita.analysis_status (status) VALUES ('in_construction'), ('queued'), ('running'), ('completed'), ('error'), ('public');

-- Populate job_status table
INSERT INTO qiita.job_status (status) VALUES ('queued'), ('running'), ('completed'), ('error');

-- Populate data_type table
INSERT INTO qiita.data_type (data_type) VALUES ('16S'), ('18S'), ('ITS'), ('Proteomic'), ('Metabolomic');

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
INSERT INTO qiita.filepath_type (filepath_type) VALUES ('raw_sequences'), ('raw_barcodes'), ('raw_spectra'), ('preprocessed_sequences'), ('preprocessed_sequences_qual'), ('biom'), ('tar'), ('plain_text');

-- Populate checksum_algorithm table
INSERT INTO qiita.checksum_algorithm (name) VALUES ('crc32');

-- Populate commands available
INSERT INTO qiita.command (name, command) VALUES ('Summarize taxa through plots', 'summarize_taxa_through_plots.py'), ('Beta diversity through plots', 'beta_diversity_through_plots.py');
