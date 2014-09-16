-- Insert some users in the system. Passwords are 'password' for all users
INSERT INTO qiita.qiita_user (email, user_level_id, password, name,
	affiliation, address, phone) VALUES
	('test@foo.bar', 4,
	'$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe', 'Dude',
	'Nowhere University', '123 fake st, Apt 0, Faketown, CO 80302',
	'111-222-3344'),
	('shared@foo.bar', 4,
	'$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe', 'Shared',
	'Nowhere University', '123 fake st, Apt 0, Faketown, CO 80302',
	'111-222-3344'),
	('admin@foo.bar', 4,
	'$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe', 'Admin',
	'Owner University', '312 noname st, Apt K, Nonexistantown, CO 80302',
	'222-444-6789'),
	('demo@microbio.me', 4,
	'$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe', 'Demo',
	'Qitta Dev', '1345 Colorado Avenue', '303-492-1984');

-- Insert some study persons
INSERT INTO qiita.study_person (name, email, affiliation, address, phone) VALUES
	('LabDude', 'lab_dude@foo.bar', 'knight lab', '123 lab street', '121-222-3333'),
	('empDude', 'emp_dude@foo.bar', 'broad', NULL, '444-222-3333'),
	('PIDude', 'PI_dude@foo.bar', 'Wash U', '123 PI street', NULL);

-- Insert a study: EMP 1001
INSERT INTO qiita.study (email, study_status_id, emp_person_id, first_contact,
	funding, timeseries_type_id, lab_person_id, metadata_complete,
	mixs_compliant, most_recent_contact, number_samples_collected,
	number_samples_promised, portal_type_id, principal_investigator_id, reprocess,
	spatial_series, study_title, study_alias, study_description,
	study_abstract, vamps_id) VALUES
	('test@foo.bar', 2, 2, '2014-05-19 16:10', NULL, 1, 1, TRUE, TRUE,
	'2014-05-19 16:11', 27, 27, 2, 3, FALSE, FALSE,
	'Identification of the Microbiomes for Cannabis Soils', 'Cannabis Soils', 'Analysis of the Cannabis Plant Microbiome',
	'This is a preliminary study to examine the microbiota associated with the Cannabis plant. Soils samples from the bulk soil, soil associated with the roots, and the rhizosphere were extracted and the DNA sequenced. Roots from three independent plants of different strains were examined. These roots were obtained November 11, 2011 from plants that had been harvested in the summer. Future studies will attempt to analyze the soils and rhizospheres from the same location at different time points in the plant lifecycle.',
	NULL);

-- Insert study_users (share study 1 with shared user)
INSERT INTO qiita.study_users (study_id, email) VALUES (1, 'shared@foo.bar');
INSERT INTO qiita.study_users (study_id, email) VALUES (1, 'demo@microbio.me');

-- Insert PMIDs for study
INSERT INTO qiita.study_pmid (study_id, pmid) VALUES (1, '123456'), (1, '7891011');

-- Insert an investigation
INSERT INTO qiita.investigation (name, description, contact_person_id) VALUES
	('TestInvestigation', 'An investigation for testing purposes', 3);

-- Insert investigation_study (link study 1 with investigation 1)
INSERT INTO qiita.investigation_study (investigation_id, study_id) VALUES (1, 1);

-- Insert the study experimental factor for study 1
INSERT INTO qiita.study_experimental_factor (study_id, efo_id) VALUES (1, 1);

-- Insert the raw data filepaths for study 1
INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id) VALUES ('1_s_G1_L001_sequences.fastq.gz', 1, '852952723', 1), ('1_s_G1_L001_sequences_barcodes.fastq.gz', 2, '852952723', 1), ('2_sequences.fastq.gz', 1, '852952723', 1), ('2_sequences_barcodes.fastq.gz', 2, '852952723', 1);

-- Insert the raw data information for study 1
INSERT INTO qiita.raw_data (filetype_id) VALUES (2), (2);

-- Insert (link) the raw data with the raw filepaths
INSERT INTO qiita.raw_filepath (raw_data_id, filepath_id) VALUES (1, 1), (1, 2), (2, 3), (2, 4);

-- Insert (link) the study with the raw data
INSERT INTO qiita.study_raw_data (study_id, raw_data_id) VALUES (1, 1), (1, 2);

-- Add the required_sample_info for study 1
INSERT INTO qiita.required_sample_info (study_id, sample_id, physical_location, has_physical_specimen, has_extracted_data, sample_type, required_sample_info_status_id, collection_timestamp, host_subject_id, description) VALUES
	(1, 'SKB8.640193', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:M7', 'Cannabis Soil Microbiome'),
	(1, 'SKD8.640184', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:D9', 'Cannabis Soil Microbiome'),
	(1, 'SKB7.640196', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:M8', 'Cannabis Soil Microbiome'),
	(1, 'SKM9.640192', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:B8', 'Cannabis Soil Microbiome'),
	(1, 'SKM4.640180', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:D2', 'Cannabis Soil Microbiome'),
	(1, 'SKM5.640177', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:M3', 'Cannabis Soil Microbiome'),
	(1, 'SKB5.640181', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:M4', 'Cannabis Soil Microbiome'),
	(1, 'SKD6.640190', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:B9', 'Cannabis Soil Microbiome'),
	(1, 'SKB2.640194', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:B4', 'Cannabis Soil Microbiome'),
	(1, 'SKD2.640178', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:B5', 'Cannabis Soil Microbiome'),
	(1, 'SKM7.640188', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:B6', 'Cannabis Soil Microbiome'),
	(1, 'SKB1.640202', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:M2', 'Cannabis Soil Microbiome'),
	(1, 'SKD1.640179', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:M5', 'Cannabis Soil Microbiome'),
	(1, 'SKD3.640198', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:B1', 'Cannabis Soil Microbiome'),
	(1, 'SKM8.640201', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:D8', 'Cannabis Soil Microbiome'),
	(1, 'SKM2.640199', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:D4', 'Cannabis Soil Microbiome'),
	(1, 'SKB9.640200', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:B3', 'Cannabis Soil Microbiome'),
	(1, 'SKD5.640186', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:M1', 'Cannabis Soil Microbiome'),
	(1, 'SKM3.640197', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:B7', 'Cannabis Soil Microbiome'),
	(1, 'SKD9.640182', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:D3', 'Cannabis Soil Microbiome'),
	(1, 'SKB4.640189', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:D7', 'Cannabis Soil Microbiome'),
	(1, 'SKD7.640191', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:D6', 'Cannabis Soil Microbiome'),
	(1, 'SKM6.640187', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:B2', 'Cannabis Soil Microbiome'),
	(1, 'SKD4.640185', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:M9', 'Cannabis Soil Microbiome'),
	(1, 'SKB3.640195', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:M6', 'Cannabis Soil Microbiome'),
	(1, 'SKB6.640176', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:D5', 'Cannabis Soil Microbiome'),
	(1, 'SKM1.640183', 'ANL', TRUE, TRUE, 'ENVO:soil', 4, '2011-11-11 13:00', '1001:D1', 'Cannabis Soil Microbiome');

-- Add the study sample columns for study 1
INSERT INTO qiita.study_sample_columns (study_id, column_name, column_type) VALUES
	(1, 'sample_id', 'varchar'),
	(1, 'SEASON_ENVIRONMENT', 'varchar'),
	(1, 'ASSIGNED_FROM_GEO', 'varchar'),
	(1, 'TEXTURE', 'varchar'),
	(1, 'TAXON_ID', 'varchar'),
	(1, 'DEPTH', 'float8'),
	(1, 'HOST_TAXID', 'varchar'),
	(1, 'COMMON_NAME', 'varchar'),
	(1, 'WATER_CONTENT_SOIL', 'float8'),
	(1, 'ELEVATION', 'float8'),
	(1, 'TEMP', 'float8'),
	(1, 'TOT_NITRO', 'float8'),
	(1, 'SAMP_SALINITY', 'float8'),
	(1, 'ALTITUDE', 'float8'),
	(1, 'ENV_BIOME', 'varchar'),
	(1, 'COUNTRY', 'varchar'),
	(1, 'PH', 'float8'),
	(1, 'ANONYMIZED_NAME', 'varchar'),
	(1, 'TOT_ORG_CARB', 'float8'),
	(1, 'LONGITUDE', 'float8'),
	(1, 'Description_duplicate', 'varchar'),
	(1, 'ENV_FEATURE', 'varchar'),
	(1, 'LATITUDE', 'float8');

-- Crate the sample_1 dynamic table
CREATE TABLE qiita.sample_1 (
	sample_id				varchar,
	SEASON_ENVIRONMENT		varchar,
	ASSIGNED_FROM_GEO		varchar,
	TEXTURE					varchar,
	TAXON_ID				varchar,
	DEPTH					float8,
	HOST_TAXID				varchar,
	COMMON_NAME				varchar,
	WATER_CONTENT_SOIL		float8,
	ELEVATION				float8,
	TEMP					float8,
	TOT_NITRO				float8,
	SAMP_SALINITY			float8,
	ALTITUDE				float8,
	ENV_BIOME				varchar,
	COUNTRY					varchar,
	PH						float8,
	ANONYMIZED_NAME			varchar,
	TOT_ORG_CARB			float8,
	LONGITUDE				float8,
	Description_duplicate	varchar,
	ENV_FEATURE				varchar,
	LATITUDE				float8,
	CONSTRAINT pk_sample_1 PRIMARY KEY ( sample_id ),
	CONSTRAINT fk_sample_1_sample_id FOREIGN KEY (sample_id) REFERENCES qiita.required_sample_info( sample_id )
);

-- Populates the sample_1 dynamic table
INSERT INTO qiita.sample_1 (sample_id, SEASON_ENVIRONMENT, ASSIGNED_FROM_GEO, TEXTURE, TAXON_ID, DEPTH, HOST_TAXID, COMMON_NAME, WATER_CONTENT_SOIL, ELEVATION, TEMP, TOT_NITRO, SAMP_SALINITY, ALTITUDE, ENV_BIOME, COUNTRY, PH, ANONYMIZED_NAME, TOT_ORG_CARB, LONGITUDE, Description_duplicate, ENV_FEATURE, LATITUDE) VALUES
	('SKM7.640188', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '1118232', 0.15, '3483', 'root metagenome', 0.101, 114, 15, 1.3, 7.44, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.82, 'SKM7', 3.31, -117.241111, 'Bucu Roots', 'ENVO:plant-associated habitat', 33.193611),
	('SKD9.640182', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '1118232', 0.15, '3483', 'root metagenome', 0.178, 114, 15, 1.51, 7.1, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.82, 'SKD9', 4.32, -117.241111, 'Diesel Root', 'ENVO:plant-associated habitat', 33.193611),
	('SKM8.640201', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '1118232', 0.15, '3483', 'root metagenome', 0.101, 114, 15, 1.3, 7.44, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.82, 'SKM8', 3.31, -117.241111, 'Bucu Roots', 'ENVO:plant-associated habitat', 33.193611),
	('SKB8.640193', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '1118232', 0.15, '3483', 'root metagenome', 0.164, 114, 15, 1.41, 7.15, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.94, 'SKB8', 5, -117.241111, 'Burmese root', 'ENVO:plant-associated habitat', 33.193611),
	('SKD2.640178', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '410658', 0.15, '3483', 'soil metagenome', 0.178, 114, 15, 1.51, 7.1, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.8, 'SKD2', 4.32, -117.241111, 'Diesel bulk', 'ENVO:plant-associated habitat', 33.193611),
	('SKM3.640197', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '410658', 0.15, '3483', 'soil metagenome', 0.101, 114, 15, 1.3, 7.44, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.82, 'SKM3', 3.31, -117.241111, 'Bucu bulk', 'ENVO:plant-associated habitat', 33.193611),
	('SKM4.640180', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '939928', 0.15, '3483', 'rhizosphere metagenome', 0.101, 114, 15, 1.3, 7.44, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.82, 'SKM4', 3.31, -117.241111, 'Bucu Rhizo', 'ENVO:plant-associated habitat', 33.193611),
	('SKB9.640200', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '1118232', 0.15, '3483', 'root metagenome', 0.164, 114, 15, 1.41, 7.15, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.8, 'SKB9', 5, -117.241111, 'Burmese root', 'ENVO:plant-associated habitat', 33.193611),
	('SKB4.640189', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '939928', 0.15, '3483', 'rhizosphere metagenome', 0.164, 114, 15, 1.41, 7.15, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.94, 'SKB4', 5, -117.241111, 'Burmese Rhizo', 'ENVO:plant-associated habitat', 33.193611),
	('SKB5.640181', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '939928', 0.15, '3483', 'rhizosphere metagenome', 0.164, 114, 15, 1.41, 7.15, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.94, 'SKB5', 5, -117.241111, 'Burmese Rhizo', 'ENVO:plant-associated habitat', 33.193611),
	('SKB6.640176', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '939928', 0.15, '3483', 'rhizosphere metagenome', 0.164, 114, 15, 1.41, 7.15, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.94, 'SKB6', 5, -117.241111, 'Burmese Rhizo', 'ENVO:plant-associated habitat', 33.193611),
	('SKM2.640199', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '410658', 0.15, '3483', 'soil metagenome', 0.101, 114, 15, 1.3, 7.44, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.82, 'SKM2', 3.31, -117.241111, 'Bucu bulk', 'ENVO:plant-associated habitat', 33.193611),
	('SKM5.640177', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '939928', 0.15, '3483', 'rhizosphere metagenome', 0.101, 114, 15, 1.3, 7.44, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.82, 'SKM5', 3.31, -117.241111, 'Bucu Rhizo', 'ENVO:plant-associated habitat', 33.193611),
	('SKB1.640202', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '410658', 0.15, '3483', 'soil metagenome', 0.164, 114, 15, 1.41, 7.15, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.94, 'SKB1', 5, -117.241111, 'Burmese bulk', 'ENVO:plant-associated habitat', 33.193611),
	('SKD8.640184', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '1118232', 0.15, '3483', 'root metagenome', 0.178, 114, 15, 1.51, 7.1, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.8, 'SKD8', 4.32, -117.241111, 'Diesel Root', 'ENVO:plant-associated habitat', 33.193611),
	('SKD4.640185', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '939928', 0.15, '3483', 'rhizosphere metagenome', 0.178, 114, 15, 1.51, 7.1, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.8, 'SKD4', 4.32, -117.241111, 'Diesel Rhizo', 'ENVO:plant-associated habitat', 33.193611),
	('SKB3.640195', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '410658', 0.15, '3483', 'soil metagenome', 0.164, 114, 15, 1.41, 7.15, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.94, 'SKB3', 5, -117.241111, 'Burmese bulk', 'ENVO:plant-associated habitat', 33.193611),
	('SKM1.640183', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '410658', 0.15, '3483', 'soil metagenome', 0.101, 114, 15, 1.3, 7.44, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.82, 'SKM1', 3.31, -117.241111, 'Bucu bulk', 'ENVO:plant-associated habitat', 33.193611),
	('SKB7.640196', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '1118232', 0.15, '3483', 'root metagenome', 0.164, 114, 15, 1.41, 7.15, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.94, 'SKB7', 5, -117.241111, 'Burmese root', 'ENVO:plant-associated habitat', 33.193611),
	('SKD3.640198', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '410658', 0.15, '3483', 'soil metagenome', 0.178, 114, 15, 1.51, 7.1, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.8, 'SKD3', 4.32, -117.241111, 'Diesel bulk', 'ENVO:plant-associated habitat', 33.193611),
	('SKD7.640191', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '1118232', 0.15, '3483', 'root metagenome', 0.178, 114, 15, 1.51, 7.1, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.8, 'SKD7', 4.32, -117.241111, 'Diesel Root', 'ENVO:plant-associated habitat', 33.193611),
	('SKD6.640190', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '939928', 0.15, '3483', 'rhizosphere metagenome', 0.178, 114, 15, 1.51, 7.1, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.8, 'SKD6', 4.32, -117.241111, 'Diesel Rhizo', 'ENVO:plant-associated habitat', 33.193611),
	('SKB2.640194', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '410658', 0.15, '3483', 'soil metagenome', 0.164, 114, 15, 1.41, 7.15, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.94, 'SKB2', 5, -117.241111, 'Burmese bulk', 'ENVO:plant-associated habitat', 33.193611),
	('SKM9.640192', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '1118232', 0.15, '3483', 'root metagenome', 0.101, 114, 15, 1.3, 7.44, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.82, 'SKM9', 3.31, -117.241111, 'Bucu Roots', 'ENVO:plant-associated habitat', 33.193611),
	('SKM6.640187', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '939928', 0.15, '3483', 'rhizosphere metagenome', 0.101, 114, 15, 1.3, 7.44, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.82, 'SKM6', 3.31, -117.241111, 'Bucu Rhizo', 'ENVO:plant-associated habitat', 33.193611),
	('SKD5.640186', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '939928', 0.15, '3483', 'rhizosphere metagenome', 0.178, 114, 15, 1.51, 7.1, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.8, 'SKD5', 4.32, -117.241111, 'Diesel Rhizo', 'ENVO:plant-associated habitat', 33.193611),
	('SKD1.640179', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '410658', 0.15, '3483', 'soil metagenome', 0.178, 114, 15, 1.51, 7.1, 0, 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', 6.8, 'SKD1', 4.32, -117.241111, 'Diesel bulk', 'ENVO:plant-associated habitat', 33.193611);

-- Add the common prep info for study 1
INSERT INTO qiita.common_prep_info (raw_data_id, sample_id, center_name, center_project_name, ebi_submission_accession, ebi_study_accession, emp_status_id, data_type_id) VALUES
	(1, 'SKB8.640193', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKD8.640184', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKB7.640196', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKM9.640192', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKM4.640180', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKM5.640177', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKB5.640181', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKD6.640190', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKB2.640194', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKD2.640178', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKM7.640188', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKB1.640202', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKD1.640179', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKD3.640198', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKM8.640201', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKM2.640199', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKB9.640200', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKD5.640186', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKM3.640197', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKD9.640182', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKB4.640189', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKD7.640191', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKM6.640187', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKD4.640185', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKB3.640195', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKB6.640176', 'ANL', NULL, NULL, NULL, 1, 2),
	(1, 'SKM1.640183', 'ANL', NULL, NULL, NULL, 1, 2);

-- Add raw data prep columns
INSERT INTO qiita.raw_data_prep_columns (raw_data_id, column_name, column_type) VALUES
	(1, 'sample_id', 'varchar'),
	(1, 'BarcodeSequence', 'varchar'),
	(1, 'LIBRARY_CONSTRUCTION_PROTOCOL', 'varchar'),
	(1, 'LinkerPrimerSequence', 'varchar'),
	(1, 'TARGET_SUBFRAGMENT', 'varchar'),
	(1, 'target_gene', 'varchar'),
	(1, 'RUN_CENTER', 'varchar'),
	(1, 'RUN_PREFIX', 'varchar'),
	(1, 'RUN_DATE', 'varchar'),
	(1, 'EXPERIMENT_CENTER', 'varchar'),
	(1, 'EXPERIMENT_DESIGN_DESCRIPTION', 'varchar'),
	(1, 'EXPERIMENT_TITLE', 'varchar'),
	(1, 'PLATFORM', 'varchar'),
	(1, 'SAMP_SIZE', 'varchar'),
	(1, 'SEQUENCING_METH', 'varchar'),
	(1, 'illumina_technology', 'varchar'),
	(1, 'SAMPLE_CENTER', 'varchar'),
	(1, 'pcr_primers', 'varchar'),
	(1, 'STUDY_CENTER', 'varchar');

-- Crate the prep_1 dynamic table
CREATE TABLE qiita.prep_1 (
	sample_id						varchar,
	BarcodeSequence					varchar,
	LIBRARY_CONSTRUCTION_PROTOCOL	varchar,
	LinkerPrimerSequence			varchar,
	TARGET_SUBFRAGMENT				varchar,
	target_gene						varchar,
	RUN_CENTER						varchar,
	RUN_PREFIX						varchar,
	RUN_DATE						varchar,
	EXPERIMENT_CENTER				varchar,
	EXPERIMENT_DESIGN_DESCRIPTION	varchar,
	EXPERIMENT_TITLE				varchar,
	PLATFORM						varchar,
	SAMP_SIZE						varchar,
	SEQUENCING_METH					varchar,
	illumina_technology				varchar,
	SAMPLE_CENTER					varchar,
	pcr_primers						varchar,
	STUDY_CENTER					varchar,
	CONSTRAINT pk_prep_1 PRIMARY KEY ( sample_id ),
	CONSTRAINT fk_prep_1_sample_id FOREIGN KEY (sample_id) REFERENCES qiita.required_sample_info( sample_id )
);

-- Populates the prep_1 dynamic table
INSERT INTO qiita.prep_1 (sample_id, BarcodeSequence, LIBRARY_CONSTRUCTION_PROTOCOL, LinkerPrimerSequence, TARGET_SUBFRAGMENT, target_gene, RUN_CENTER, RUN_PREFIX, RUN_DATE, EXPERIMENT_CENTER, EXPERIMENT_DESIGN_DESCRIPTION, EXPERIMENT_TITLE, PLATFORM, SAMP_SIZE, SEQUENCING_METH, illumina_technology, SAMPLE_CENTER, pcr_primers, STUDY_CENTER) VALUES
	('SKB1.640202', 'GTCCGCAAGTTA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKB2.640194', 'CGTAGAGCTCTC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKB3.640195', 'CCTCTGAGAGCT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKB4.640189', 'CCTCGATGCAGT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKB5.640181', 'GCGGACTATTCA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKB6.640176', 'CGTGCACAATTG', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKB7.640196', 'CGGCCTAAGTTC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKB8.640193', 'AGCGCTCACATC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKB9.640200', 'TGGTTATGGCAC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKD1.640179', 'CGAGGTTCTGAT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKD2.640178', 'AACTCCTGTGGA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKD3.640198', 'TAATGGTCGTAG', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKD4.640185', 'TTGCACCGTCGA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKD5.640186', 'TGCTACAGACGT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKD6.640190', 'ATGGCCTGACTA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKD7.640191', 'ACGCACATACAA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKD8.640184', 'TGAGTGGTCTGT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKD9.640182', 'GATAGCACTCGT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKM1.640183', 'TAGCGCGAACTT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKM2.640199', 'CATACACGCACC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKM3.640197', 'ACCTCAGTCAAG', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKM4.640180', 'TCGACCAAACAC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKM5.640177', 'CCACCCAGTAAC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKM6.640187', 'ATATCGCGATGA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKM7.640188', 'CGCCGGTAATCT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKM8.640201', 'CCGATGCCTTGA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
	('SKM9.640192', 'AGCAGGCACGAA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME');

-- Insert preprocessed information for raw data 1
INSERT INTO qiita.preprocessed_data (preprocessed_params_table, preprocessed_params_id, submitted_to_insdc, data_type_id) VALUES ('preprocessed_sequence_illumina_params', 1, TRUE, 2), ('preprocessed_sequence_illumina_params', 2, FALSE, 2);

-- Link the new preprocessed data with the raw data
INSERT INTO qiita.raw_preprocessed_data (raw_data_id, preprocessed_data_id) VALUES (1, 1), (1, 2);

-- Insert (link) preprocessed information to study 1
INSERT INTO qiita.study_preprocessed_data (preprocessed_data_id, study_id) VALUES (1, 1), (2, 1);

-- Insert the preprocessed filepath for raw data 1
INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id) VALUES ('1_seqs.fna', 4, '852952723', 1), ('1_seqs.qual', 5, '852952723', 1);

-- Insert (link) the preprocessed data with the preprocessed filepaths
INSERT INTO qiita.preprocessed_filepath (preprocessed_data_id, filepath_id) VALUES (1, 5), (1, 6);

-- Insert the preprocessed illumina params used for raw data 1
INSERT INTO qiita.preprocessed_sequence_illumina_params (trim_length) VALUES (151), (100);

-- Insert processed information for study 0 and processed data 1
INSERT INTO qiita.processed_data (processed_params_table, processed_params_id, processed_date, data_type_id) VALUES ('processed_params_uclust', 1, 'Mon Oct 1 09:30:27 2012', 2);

-- Insert (link) processed information to study 1
INSERT INTO qiita.study_processed_data (processed_data_id, study_id) VALUES (1, 1);

-- Link the processed data with the preprocessed data
INSERT INTO qiita.preprocessed_processed_data (preprocessed_data_id, processed_data_id) VALUES (1, 1);

-- Insert the reference files for reference 1
INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id) VALUES ('GreenGenes_13_8_97_otus.fasta', 9, '852952723', 1), ('GreenGenes_13_8_97_otu_taxonomy.txt', 10, '852952723', 1), ('GreenGenes_13_8_97_otus.tree', 11, '852952723', 1);

-- Populate the reference table
INSERT INTO qiita.reference (reference_name, reference_version, sequence_filepath, taxonomy_filepath, tree_filepath) VALUES ('GreenGenes', '13_8', 7, 8, 9);

-- Insert the processed params uclust used for preprocessed data 1
INSERT INTO qiita.processed_params_uclust (similarity, enable_rev_strand_match, suppress_new_clusters, reference_id) VALUES (0.97, TRUE, TRUE, 1);

-- Insert the biom table filepath for processed data 1
INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id) VALUES ('1_study_1001_closed_reference_otu_table.biom', 6, '852952723', 1);

-- Insert (link) the processed data with the processed filepath
INSERT INTO qiita.processed_filepath (processed_data_id, filepath_id) VALUES (1, 10);

-- Insert filepath for job results files
INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id) VALUES ('1_job_result.txt', 8, '852952723', 1), ('2_test_folder', 7, '852952723', 1);

-- Insert jobs
INSERT INTO qiita.job (data_type_id, job_status_id, command_id, options) VALUES (2, 1, 1, '{"--otu_table_fp":1}'), (2, 3, 2, '{"--mapping_fp":1,"--otu_table_fp":1}'), (2, 1, 2, '{"--mapping_fp":1,"--otu_table_fp":1}');

-- Insert Analysis
INSERT INTO qiita.analysis (email, name, description, analysis_status_id, pmid) VALUES ('test@foo.bar', 'SomeAnalysis', 'A test analysis', 1, '121112'), ('test@foo.bar', 'SomeSecondAnalysis', 'Another test analysis', 1, '22221112');

-- Attach jobs to analysis
INSERT INTO qiita.analysis_job (analysis_id, job_id) VALUES (1, 1), (1, 2), (2, 3);

-- Insert filepath for analysis biom files
INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id) VALUES ('1_analysis_18S.biom', 6, '852952723', 1), ('1_analysis_mapping.txt', 8, '852952723', 1);

-- Attach filepath to analysis
INSERT INTO qiita.analysis_filepath (analysis_id, filepath_id, data_type_id) VALUES (1, 13, 2), (1, 14, NULL);

-- Attach samples to analysis
INSERT INTO qiita.analysis_sample (analysis_id, processed_data_id, sample_id) VALUES (1,1,'SKB8.640193'), (1,1,'SKD8.640184'), (1,1,'SKB7.640196'), (1,1,'SKM9.640192'), (1,1,'SKM4.640180'), (2,1,'SKB8.640193'), (2,1,'SKD8.640184'), (2,1,'SKB7.640196'), (2,1,'SKM3.640197');

--Share analysis with shared user
INSERT INTO qiita.analysis_users (analysis_id, email) VALUES (1, 'shared@foo.bar');

-- Add job results
INSERT INTO qiita.job_results_filepath (job_id, filepath_id) VALUES (1, 11), (2, 12);
