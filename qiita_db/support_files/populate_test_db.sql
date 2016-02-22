-- Populate.sql sets the increment to begin at 10000, but all tests expect it to start at 1, so set it back to 1 for the test DB population
SELECT setval('qiita.study_study_id_seq', 1, false);

-- Patch 33.sql sets the increment to begin at 2000, but all tests expect it to start at 1, so set it back to 1 for the test DB population
SELECT setval('qiita.artifact_artifact_id_seq', 1, false);

-- Add an ontology
INSERT INTO qiita.ontology (ontology_id, ontology, fully_loaded, fullname, query_url, source_url, definition, load_date) VALUES (999999999, E'ENA', E'1', E'European Nucleotide Archive Submission Ontology', NULL, E'http://www.ebi.ac.uk/embl/Documentation/ENA-Reads.html', E'The ENA CV is to be used to annotate XML submissions to the ENA.', '2009-02-23 00:00:00');

-- Add some ontology values
INSERT INTO qiita.term (term_id, ontology_id, term, identifier, definition, namespace, is_obsolete, is_root_term, is_leaf) VALUES (2052508974, 999999999, E'Whole Genome Sequencing', E'ENA:0000059', NULL, NULL, NULL, NULL, NULL);
INSERT INTO qiita.term (term_id, ontology_id, term, identifier, definition, namespace, is_obsolete, is_root_term, is_leaf) VALUES (2052508975, 999999999, E'Metagenomics', E'ENA:0000060', NULL, NULL, NULL, NULL, NULL);
INSERT INTO qiita.term (term_id, ontology_id, term, identifier, definition, namespace, is_obsolete, is_root_term, is_leaf) VALUES (2052508976, 999999999, E'Transcriptome Analysis', E'ENA:0000061', NULL, NULL, NULL, NULL, NULL);
INSERT INTO qiita.term (term_id, ontology_id, term, identifier, definition, namespace, is_obsolete, is_root_term, is_leaf) VALUES (2052508977, 999999999, E'Resequencing', E'ENA:0000062', NULL, NULL, NULL, NULL, NULL);
INSERT INTO qiita.term (term_id, ontology_id, term, identifier, definition, namespace, is_obsolete, is_root_term, is_leaf) VALUES (2052508978, 999999999, E'Epigenetics', E'ENA:0000066', NULL, NULL, NULL, NULL, NULL);
INSERT INTO qiita.term (term_id, ontology_id, term, identifier, definition, namespace, is_obsolete, is_root_term, is_leaf) VALUES (2052508979, 999999999, E'Synthetic Genomics', E'ENA:0000067', NULL, NULL, NULL, NULL, NULL);
INSERT INTO qiita.term (term_id, ontology_id, term, identifier, definition, namespace, is_obsolete, is_root_term, is_leaf) VALUES (2052508980, 999999999, E'Forensic or Paleo-genomics', E'ENA:0000065', NULL, NULL, NULL, NULL, NULL);
INSERT INTO qiita.term (term_id, ontology_id, term, identifier, definition, namespace, is_obsolete, is_root_term, is_leaf) VALUES (2052508981, 999999999, E'Gene Regulation Study', E'ENA:0000068', NULL, NULL, NULL, NULL, NULL);
INSERT INTO qiita.term (term_id, ontology_id, term, identifier, definition, namespace, is_obsolete, is_root_term, is_leaf) VALUES (2052508982, 999999999, E'Cancer Genomics', E'ENA:0000063', NULL, NULL, NULL, NULL, NULL);
INSERT INTO qiita.term (term_id, ontology_id, term, identifier, definition, namespace, is_obsolete, is_root_term, is_leaf) VALUES (2052508983, 999999999, E'Population Genomics', E'ENA:0000064', NULL, NULL, NULL, NULL, NULL);
INSERT INTO qiita.term (term_id, ontology_id, term, identifier, definition, namespace, is_obsolete, is_root_term, is_leaf) VALUES (2052508984, 999999999, E'RNASeq', E'ENA:0000070', NULL, NULL, NULL, NULL, NULL);
INSERT INTO qiita.term (term_id, ontology_id, term, identifier, definition, namespace, is_obsolete, is_root_term, is_leaf) VALUES (2052508985, 999999999, E'Exome Sequencing', E'ENA:0000071', NULL, NULL, NULL, NULL, NULL);
INSERT INTO qiita.term (term_id, ontology_id, term, identifier, definition, namespace, is_obsolete, is_root_term, is_leaf) VALUES (2052508986, 999999999, E'Pooled Clone Sequencing', E'ENA:0000072', NULL, NULL, NULL, NULL, NULL);
INSERT INTO qiita.term (term_id, ontology_id, term, identifier, definition, namespace, is_obsolete, is_root_term, is_leaf) VALUES (2052508987, 999999999, E'Other', E'ENA:0000069', NULL, NULL, NULL, NULL, NULL);

-- Add client ids and secrets
INSERT INTO qiita.oauth_identifiers (client_id) VALUES ('DWelYzEYJYcZ4wlqUp0bHGXojrvZVz0CNBJvOqUKcrPQ5p4UqE');
INSERT INTO qiita.oauth_identifiers (client_id, client_secret) VALUES ('19ndkO3oMKsoChjVVWluF7QkxHRfYhTKSFbAVt8IhK7gZgDaO4', 'J7FfQ7CQdOxuKhQAf1eoGgBAE81Ns8Gu3EKaWFm3IO2JKhAmmCWZuabe0O5Mp28s1');

-- -- Insert filepaths for the artifacts and reference
-- INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id, data_directory_id)
--     VALUES ('1_s_G1_L001_sequences.fastq.gz', 1, '852952723', 1, 5),
--            ('1_s_G1_L001_sequences_barcodes.fastq.gz', 3, '852952723', 1, 5),
--            ('1_seqs.fna', 4, '852952723', 1, 3),
--            ('1_seqs.qual', 5, '852952723', 1, 3),
--            ('1_seqs.demux', 6, 852952723, 1, 3),
--            ('GreenGenes_13_8_97_otus.fasta', 10, '852952723', 1, 6),
--            ('GreenGenes_13_8_97_otu_taxonomy.txt', 11, '852952723', 1, 6),
--            ('GreenGenes_13_8_97_otus.tree', 12, '852952723', 1, 6),
--            ('1_study_1001_closed_reference_otu_table.biom', 7, '852952723', 1, 4),
--            ('Silva_97_otus.fasta', 10, '852952723', 1, 6),
--            ('Silva_97_otu_taxonomy.txt', 11, '852952723', 1, 6),
--            ('1_study_1001_closed_reference_otu_table_Silva.biom', 7, '852952723', 1, 4);
--
-- -- Link the artifacts with the filepaths
-- INSERT INTO qiita.artifact_filepath (artifact_id, filepath_id)
--     VALUES (1, 1), (1, 2),
--            (2, 3), (2, 4), (2, 5),
--            (4, 9), (5, 9), (6, 12);
--

-- -- Populate the reference table
-- INSERT INTO qiita.reference (reference_name, reference_version, sequence_filepath, taxonomy_filepath, tree_filepath) VALUES
-- ('Greengenes', '13_8', 6, 7, 8),
-- ('Silva', 'test', 10, 11, NULL);
--
-- -- Insert filepath for job results files
-- INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id, data_directory_id) VALUES
-- ('1_job_result.txt', 9, '852952723', 1, 2),
-- ('2_test_folder', 8, '852952723', 1, 2);
--
-- -- Insert jobs
-- INSERT INTO qiita.job (data_type_id, job_status_id, command_id, options) VALUES (2, 1, 1, '{"--otu_table_fp":1}'), (2, 3, 2, '{"--mapping_fp":1,"--otu_table_fp":1}'), (2, 1, 2, '{"--mapping_fp":1,"--otu_table_fp":1}');
--
-- -- Add job results
-- INSERT INTO qiita.job_results_filepath (job_id, filepath_id) VALUES (1, 13), (2, 14);
--
-- -- Attach jobs to analysis
-- INSERT INTO qiita.analysis_job (analysis_id, job_id) VALUES (1, 1), (1, 2), (2, 3);
--
-- -- Insert filepath for analysis biom files
-- INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id, data_directory_id) VALUES
-- ('1_analysis_18S.biom', 7, '852952723', 1, 1), ('1_analysis_mapping.txt', 9, '852952723', 1, 1);
--
-- -- Attach filepath to analysis
-- INSERT INTO qiita.analysis_filepath (analysis_id, filepath_id, data_type_id) VALUES (1, 15, 2), (1, 16, NULL);
--
-- -- Create the new sample_template_filepath
-- INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id, data_directory_id) VALUES ('1_19700101-000000.txt', 14, '852952723', 1, 9);
-- INSERT INTO qiita.sample_template_filepath VALUES (1, 17);
--
-- --add collection to the database
-- INSERT INTO qiita.collection (email, name, description) VALUES ('test@foo.bar', 'TEST_COLLECTION', 'collection for testing purposes');
--
-- --associate analyses and jobs with collection
-- INSERT INTO qiita.collection_analysis (collection_id, analysis_id) VALUES (1, 1);
-- INSERT INTO qiita.collection_job (collection_id, job_id) VALUES (1, 1);
--
-- --share collection with shared user
-- INSERT INTO qiita.collection_users (email, collection_id) VALUES ('shared@foo.bar', 1);
--
-- --add default analysis for users
-- INSERT INTO qiita.analysis (email, name, description, dflt, analysis_status_id) VALUES ('test@foo.bar', 'test@foo.bar-dflt-1', 'dflt', true, 1), ('admin@foo.bar', 'admin@foo.bar-dflt-1', 'dflt', true, 1), ('shared@foo.bar', 'shared@foo.bar-dflt-1', 'dflt', true, 1), ('demo@microbio.me', 'demo@microbio.me-dflt-1', 'dflt', true, 1), ('test@foo.bar', 'test@foo.bar-dflt-2', 'dflt', true, 1), ('admin@foo.bar', 'admin@foo.bar-dflt-2', 'dflt', true, 2), ('shared@foo.bar', 'shared@foo.bar-dflt-2', 'dflt', true, 2), ('demo@microbio.me', 'demo@microbio.me-dflt-2', 'dflt', true, 2);
-- INSERT INTO qiita.analysis_portal (analysis_id, portal_type_id) VALUES (3, 1), (4, 1), (5, 1), (6, 1), (7, 2), (8, 2), (9, 2), (10, 2);
--
-- -- Attach samples to analysis
-- INSERT INTO qiita.analysis_sample (analysis_id, artifact_id, sample_id)
--     VALUES (3, 4, '1.SKD8.640184'), (3, 4, '1.SKB7.640196'), (3, 4, '1.SKM9.640192'), (3, 4, '1.SKM4.640180');
--
-- -- Create some test messages
-- INSERT INTO qiita.message (message) VALUES ('message 1'), ('Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque sed auctor ex, non placerat sapien. Vestibulum vestibulum massa ut sapien condimentum, cursus consequat diam sodales. Nulla aliquam arcu ut massa auctor, et vehicula mauris tempor. In lacinia viverra ante quis pellentesque. Nunc vel mi accumsan, porttitor eros ut, pharetra elit. Nulla ac nisi quis dui egestas malesuada vitae ut mauris. Morbi blandit non nisl a finibus. In erat velit, congue at ipsum sit amet, venenatis bibendum sem. Curabitur vel odio sed est rutrum rutrum. Quisque efficitur ut purus in ultrices. Pellentesque eu auctor justo.'), ('message <a href="#">3</a>');
-- INSERT INTO qiita.message_user (message_id, email) VALUES (1, 'test@foo.bar'),(1, 'shared@foo.bar'),(2, 'test@foo.bar'),(3, 'test@foo.bar');
--
-- -- Create a loggin entry
-- INSERT INTO qiita.logging (time, severity_id, msg, information)
--     VALUES ('Sun Nov 22 21:29:30 2015', 2, 'Error message', '{}');
--
-- -- Create some processing jobs
-- INSERT INTO qiita.processing_job
--         (processing_job_id, email, command_id, command_parameters,
--          processing_job_status_id, logging_id, heartbeat, step)
--     VALUES ('063e553b-327c-4818-ab4a-adfe58e49860', 'test@foo.bar', 1, '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5,"input_data":1}'::json, 1, NULL, NULL, NULL),
--            ('bcc7ebcd-39c1-43e4-af2d-822e3589f14d', 'test@foo.bar', 2, '{"min_seq_len":100,"max_seq_len":1000,"trim_seq_length":false,"min_qual_score":25,"max_ambig":6,"max_homopolymer":6,"max_primer_mismatch":0,"barcode_type":"golay_12","max_barcode_errors":1.5,"disable_bc_correction":false,"qual_score_window":0,"disable_primers":false,"reverse_primers":"disable","reverse_primer_mismatches":0,"truncate_ambi_bases":false,"input_data":1}'::json, 2, NULL, 'Sun Nov 22 21:00:00 2015', 'demultiplexing'),
--            ('b72369f9-a886-4193-8d3d-f7b504168e75', 'shared@foo.bar', 1, '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":true,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5,"input_data":1}'::json, 3, NULL, 'Sun Nov 22 21:15:00 2015', NULL),
--            ('d19f76ee-274e-4c1b-b3a2-a12d73507c55', 'shared@foo.bar', 3, '{"reference":1,"sortmerna_e_value":1,"sortmerna_max_pos":10000,"similarity":0.97,"sortmerna_coverage":0.97,"threads":1,"input_data":2}'::json, 4, 1, 'Sun Nov 22 21:30:00 2015', 'generating demux file');
--
-- INSERT INTO qiita.artifact_processing_job (artifact_id, processing_job_id)
--     VALUES (1, '063e553b-327c-4818-ab4a-adfe58e49860'),
--            (1, 'bcc7ebcd-39c1-43e4-af2d-822e3589f14d'),
--            (1, 'b72369f9-a886-4193-8d3d-f7b504168e75'),
--            (2, 'd19f76ee-274e-4c1b-b3a2-a12d73507c55');
