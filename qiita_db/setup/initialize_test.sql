-- Insert some users in the system. Passwords are 'password' for all users
INSERT INTO qiita.qiita_user (email, user_level_id, password, name,
	affiliation, address, phone, salt) VALUES
	('test@foo.bar', 3,
	'$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe', 'Dude',
	'Nowhere University', '123 fake st, Apt 0, Faketown, CO 80302',
	'111-222-3344', '$2a$12$VEcWB1J9BbMZvoNOZXaBwu'),
	('shared@foo.bar', 3,
	'$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe', 'Shared',
	'Nowhere University', '123 fake st, Apt 0, Faketown, CO 80302',
	'111-222-3344', '$2a$12$VEcWB1J9BbMZvoNOZXaBwu'),
	('admin@foo.bar', 3,
	'$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe', 'Admin',
	'Owner University', '312 noname st, Apt K, Nonexistantown, CO 80302',
	'222-444-6789', '$2a$12$VEcWB1J9BbMZvoNOZXaBwu');

-- Insert some study persons
INSERT INTO qiita.study_person (name, email, address, phone) VALUES
	('LabDude', 'lab_dude@foo.bar', '123 lab street', NULL),
	('empDude', 'emp_dude@foo.bar', '123 emp street', NULL),
	('PIDude', 'PI_dude@foo.bar', '123 PI street', NULL),;

-- Insert a study: EMP 1001
INSERT INTO qiita.study (email, study_status_id, emp_person_id, first_contact,
	funding, timeseries_type_id, lab_person_id, metadata_complete,
	mixs_compliant, most_recent_contact, number_samples_collected,
	number_samples_promised, portal_type_id, principal_investigator_id, reprocess,
	spatial_series, study_title, study_alias, study_description,
	study_abstract, vamps_id) VALUES
	('test@foo.bar', 1, 1, '2014-05-19 16:10', NULL, 0, 0, 1, 1,
	'2014-05-19 16:11', 27, 27, 1, 2, 0, 0,
	'Identification of the Microbiomes for Cannabis Soils', 'Cannabis Soils', 'Analysis of the Cannabis Plant Microbiome',
	'This is a preliminary study to examine the microbiota associated with the Cannabis plant. Soils samples from the bulk soil, soil associated with the roots, and the rhizosphere were extracted and the DNA sequenced. Roots from three independent plants of different strains were examined. These roots were obtained November 11, 2011 from plants that had been harvested in the summer. Future studies will attempt to analyze the soils and rhizospheres from the same location at different time points in the plant lifecycle.',
	NULL);

-- Insert study_users (share study 0 with shared user)
INSERT INTO qiita.study_users (study_id, email) VALUES (0, 'shared@foo.bar');

-- Insert an investigation
INSERT INTO qiita.investigation (name, description, contac_person_id) VALUES
	('TestInvestigation', 'An investigation for testing purposes', 2);

-- Insert investigation_study (link study 0 with investigation 0)
INSERT INTO qiita.investigation_study (investigation_id, study_id) VALUES (0, 0);

-- Insert the study experimental factor for study 0
INSERT INTO qiita.experimental_factor (study_id, efo_id) VALUES (0, 'EFO:Weed');

-- TODO: Add raw data

-- TODO: Add study_raw_data

-- Add the required_sample_info for study 0
INSERT INTO qiita.required_sample_info (study_id, sample_id, physical_location, has_physical_specimen, has_extracted_data, sample_type, sample_status_id, collection_date, host_subject_id, description) VALUES
	(0, 'SKB8.640193', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:M7', 'Cannabis Soil Microbiome'),
	(0, 'SKD8.640184', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:D9', 'Cannabis Soil Microbiome'),
	(0, 'SKB7.640196', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:M8', 'Cannabis Soil Microbiome'),
	(0, 'SKM9.640192', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:B8', 'Cannabis Soil Microbiome'),
	(0, 'SKM4.640180', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:D2', 'Cannabis Soil Microbiome'),
	(0, 'SKM5.640177', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:M3', 'Cannabis Soil Microbiome'),
	(0, 'SKB5.640181', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:M4', 'Cannabis Soil Microbiome'),
	(0, 'SKD6.640190', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:B9', 'Cannabis Soil Microbiome'),
	(0, 'SKB2.640194', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:B4', 'Cannabis Soil Microbiome'),
	(0, 'SKD2.640178', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:B5', 'Cannabis Soil Microbiome'),
	(0, 'SKM7.640188', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:B6', 'Cannabis Soil Microbiome'),
	(0, 'SKB1.640202', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:M2', 'Cannabis Soil Microbiome'),
	(0, 'SKD1.640179', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:M5', 'Cannabis Soil Microbiome'),
	(0, 'SKD3.640198', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:B1', 'Cannabis Soil Microbiome'),
	(0, 'SKM8.640201', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:D8', 'Cannabis Soil Microbiome'),
	(0, 'SKM2.640199', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:D4', 'Cannabis Soil Microbiome'),
	(0, 'SKB9.640200', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:B3', 'Cannabis Soil Microbiome'),
	(0, 'SKD5.640186', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:M1', 'Cannabis Soil Microbiome'),
	(0, 'SKM3.640197', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:B7', 'Cannabis Soil Microbiome'),
	(0, 'SKD9.640182', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:D3', 'Cannabis Soil Microbiome'),
	(0, 'SKB4.640189', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:D7', 'Cannabis Soil Microbiome'),
	(0, 'SKD7.640191', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:D6', 'Cannabis Soil Microbiome'),
	(0, 'SKM6.640187', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:B2', 'Cannabis Soil Microbiome'),
	(0, 'SKD4.640185', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:M9', 'Cannabis Soil Microbiome'),
	(0, 'SKB3.640195', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:M6', 'Cannabis Soil Microbiome'),
	(0, 'SKB6.640176', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:D5', 'Cannabis Soil Microbiome'),
	(0, 'SKM1.640183', 'ANL', 1, 1, 'ENVO:soil', 3, '2011-11-11', '1001:D1', 'Cannabis Soil Microbiome');

-- Add the study sample columns for study 0
INSERT INTO qiita.study_sample_columns (study_id, column_name, column_type) VALUES
	(0, 'sample_id', 'int'),
	(0, 'SEASON_ENVIRONMENT', 'str'),
	(0, 'ASSIGNED_FROM_GEO', 'str'),
	(0, 'TEXTURE', 'str'),
	(0, 'TAXON_ID', 'str'),
	(0, 'DEPTH', 'float'),
	(0, 'HOST_TAXID', 'str'),
	(0, 'COMMON_NAME', 'str'),
	(0, 'WATER_CONTENT_SOIL', 'float'),
	(0, 'ELEVATION', 'float'),
	(0, 'TEMP', 'float'),
	(0, 'TOT_NITRO', 'float'),
	(0, 'SAMP_SALINITY', 'float'),
	(0, 'ALTITUDE', 'float'),
	(0, 'ENV_BIOME', 'str'),
	(0, 'COUNTRY', 'str'),
	(0, 'PH', 'float'),
	(0, 'ANONYMIZED_NAME', 'str'),
	(0, 'TOT_ORG_CARB', 'float'),
	(0, 'LONGITUDE', 'float'),
	(0, 'Description_duplicate', 'str'),
	(0, 'ENV_FEATURE', 'str'),
	(0, 'LATITUDE', 'float');

-- TODO: Add sample_0 dynamic table

-- Add the common prep info for study 0
INSERT INTO qiita.common_prep_info (raw_data_id, sample_id, center_name, center_project_name, ebi_submission_accession, ebi_study_accession, emp_status_id, data_type_id) VALUES
	(0, 'SKB8.640193', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKD8.640184', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKB7.640196', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKM9.640192', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKM4.640180', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKM5.640177', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKB5.640181', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKD6.640190', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKB2.640194', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKD2.640178', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKM7.640188', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKB1.640202', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKD1.640179', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKD3.640198', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKM8.640201', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKM2.640199', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKB9.640200', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKD5.640186', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKM3.640197', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKD9.640182', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKB4.640189', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKD7.640191', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKM6.640187', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKD4.640185', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKB3.640195', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKB6.640176', 'ANL', NULL, NULL, NULL, 0, 1),
	(0, 'SKM1.640183', 'ANL', NULL, NULL, NULL, 0, 1);

-- TODO: Add raw data prep columns
INSERT INTO qiita.raw_data_prep_columns (raw_data_id, column_name, column_type) VALUES
	(0, 'sample_id', 'int'),
	(0, 'BarcodeSequence', 'str'),
	(0, 'LIBRARY_CONSTRUCTION_PROTOCOL', 'str'),
	(0, 'LinkerPrimerSequence', 'str'),
	(0, 'TARGET_SUBFRAGMENT', 'str'),
	(0, 'target_gene', 'str'),
	(0, 'RUN_CENTER', 'str'),
	(0, 'RUN_PREFIX', 'str'),
	(0, 'RUN_DATE', 'str'),
	(0, 'EXPERIMENT_CENTER', 'str'),
	(0, 'EXPERIMENT_DESIGN_DESCRIPTION', 'str'),
	(0, 'EXPERIMENT_TITLE', 'str'),
	(0, 'PLATFORM', 'str'),
	(0, 'SAMP_SIZE', 'str'),
	(0, 'SEQUENCING_METH', 'str'),
	(0, 'LIBRARY_CONSTRUCTION_PROTOCOL', 'str'),
	(0, 'illumina_technology', 'str'),
	(0, 'REGION', 'str'),
	(0, 'SAMPLE_CENTER', 'str'),
	(0, 'pcr_primers', 'str'),
	(0, 'STUDY_CENTER', 'str');

-- TODO: Add prep_0 dynamic table 

-- TODO: Add preprocessed data

-- TODO: Add processed data
