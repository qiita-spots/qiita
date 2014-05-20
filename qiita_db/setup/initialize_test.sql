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
	('PIDude', 'PI_dude@foo.bar', '123 PI street', NULL);

-- Insert a study: EMP 1001
INSERT INTO qiita.study (email, study_status_id, emp_person_id, first_contact,
	funding, timeseries_type_id, lab_person_id, metadata_complete,
	mixs_compliant, most_recent_contact, number_samples_collected,
	number_samples_promised, portal_type_id, principal_investigator_id, reprocess,
	spatial_series, study_title, study_alias, study_description,
	study_abstract, vamps_id) VALUES
	('test@foo.bar', 1, 1, '2014-05-19 16:10', NULL, 0, 0, TRUE, TRUE,
	'2014-05-19 16:11', 27, 27, 1, 2, FALSE, FALSE,
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

-- Insert the raw data filepaths for study 0
INSERT INTO qiita.filepath (filepath, filepath_type_id) VALUES ('$QIITA_TEST_FOLDER/s_G1_L001_sequences.fastq.gz', 0), ('$QIITA_TEST_FOLDER/s_G1_L001_sequences_barcodes.fastq.gz', 1);

-- Insert the raw data information for study 0
INSERT INTO qiita.raw_data (filetype_id, submitted_to_insdc) VALUES (1, 0);

-- Insert (link) the raw data with the raw filepaths
INSERT INTO qiita.raw_filepath (raw_data_id, filepath_id) VALUES (0, 0), (0, 1);

-- Insert (link) the study with the raw data
INSERT INTO qiita.study_raw_data (study_id, raw_data_id) VALUES (0, 0);

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
	(0, 'sample_id', 'varchar'),
	(0, 'SEASON_ENVIRONMENT', 'varchar'),
	(0, 'ASSIGNED_FROM_GEO', 'varchar'),
	(0, 'TEXTURE', 'varchar'),
	(0, 'TAXON_ID', 'varchar'),
	(0, 'DEPTH', 'float8'),
	(0, 'HOST_TAXID', 'varchar'),
	(0, 'COMMON_NAME', 'varchar'),
	(0, 'WATER_CONTENT_SOIL', 'float8'),
	(0, 'ELEVATION', 'float8'),
	(0, 'TEMP', 'float8'),
	(0, 'TOT_NITRO', 'float8'),
	(0, 'SAMP_SALINITY', 'float8'),
	(0, 'ALTITUDE', 'float8'),
	(0, 'ENV_BIOME', 'varchar'),
	(0, 'COUNTRY', 'varchar'),
	(0, 'PH', 'float8'),
	(0, 'ANONYMIZED_NAME', 'varchar'),
	(0, 'TOT_ORG_CARB', 'float8'),
	(0, 'LONGITUDE', 'float8'),
	(0, 'Description_duplicate', 'varchar'),
	(0, 'ENV_FEATURE', 'varchar'),
	(0, 'LATITUDE', 'float8');

-- Crate the sample_0 dynamic table
CREATE TABLE qiita.sample_0 (
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
	CONSTRAINT pk_sample_0 PRIMARY KEY ( sample_id ),
	CONSTRAINT fk_sample_0_sample_id FOREIGN KEY (sample_id) REFERENCES qiita.required_sample_info( sample_id )
);

-- Populates the sample_0 dynamic table
INSERT INTO qiita.sample_0 (sample_id, SEASON_ENVIRONMENT, ASSIGNED_FROM_GEO, TEXTURE, TAXON_ID, DEPTH, HOST_TAXID, COMMON_NAME, WATER_CONTENT_SOIL, ELEVATION, TEMP, TOT_NITRO, SAMP_SALINITY, ALTITUDE, ENV_BIOME, COUNTRY, PH, ANONYMIZED_NAME, TOT_ORG_CARB, LONGITUDE, Description_duplicate, ENV_FEATURE, LATITUDE) VALUES
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

-- Add raw data prep columns
INSERT INTO qiita.raw_data_prep_columns (raw_data_id, column_name, column_type) VALUES
	(0, 'sample_id', 'varchar'),
	(0, 'BarcodeSequence', 'varchar'),
	(0, 'LIBRARY_CONSTRUCTION_PROTOCOL', 'varchar'),
	(0, 'LinkerPrimerSequence', 'varchar'),
	(0, 'TARGET_SUBFRAGMENT', 'varchar'),
	(0, 'target_gene', 'varchar'),
	(0, 'RUN_CENTER', 'varchar'),
	(0, 'RUN_PREFIX', 'varchar'),
	(0, 'RUN_DATE', 'varchar'),
	(0, 'EXPERIMENT_CENTER', 'varchar'),
	(0, 'EXPERIMENT_DESIGN_DESCRIPTION', 'varchar'),
	(0, 'EXPERIMENT_TITLE', 'varchar'),
	(0, 'PLATFORM', 'varchar'),
	(0, 'SAMP_SIZE', 'varchar'),
	(0, 'SEQUENCING_METH', 'varchar'),
	(0, 'illumina_technology', 'varchar'),
	(0, 'SAMPLE_CENTER', 'varchar'),
	(0, 'pcr_primers', 'varchar'),
	(0, 'STUDY_CENTER', 'varchar');

-- Crate the prep_0 dynamic table
CREATE TABLE qiita.prep_0 (
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
	CONSTRAINT pk_prep_0 PRIMARY KEY ( sample_id ),
	CONSTRAINT fk_prep_0_sample_id FOREIGN KEY (sample_id) REFERENCES qiita.required_sample_info( sample_id )
);

-- Populates the prep_0 dynamic table
INSERT INTO qiita.prep_0 (sample_id, BarcodeSequence, LIBRARY_CONSTRUCTION_PROTOCOL, LinkerPrimerSequence, TARGET_SUBFRAGMENT, target_gene, RUN_CENTER, RUN_PREFIX, RUN_DATE, EXPERIMENT_CENTER, EXPERIMENT_DESIGN_DESCRIPTION, EXPERIMENT_TITLE, PLATFORM, SAMP_SIZE, SEQUENCING_METH, illumina_technology, SAMPLE_CENTER, pcr_primers, STUDY_CENTER) VALUES
('SKB1.640202', 'GTCCGCAAGTTA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKB2.640194', 'CGTAGAGCTCTC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKB3.640195', 'CCTCTGAGAGCT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKB4.640189', 'CCTCGATGCAGT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKB5.640181', 'GCGGACTATTCA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKB6.640176', 'CGTGCACAATTG', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKB7.640196', 'CGGCCTAAGTTC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKB8.640193', 'AGCGCTCACATC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKB9.640200', 'TGGTTATGGCAC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKD1.640179', 'CGAGGTTCTGAT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKD2.640178', 'AACTCCTGTGGA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKD3.640198', 'TAATGGTCGTAG', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKD4.640185', 'TTGCACCGTCGA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKD5.640186', 'TGCTACAGACGT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKD6.640190', 'ATGGCCTGACTA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKD7.640191', 'ACGCACATACAA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKD8.640184', 'TGAGTGGTCTGT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKD9.640182', 'GATAGCACTCGT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKM1.640183', 'TAGCGCGAACTT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKM2.640199', 'CATACACGCACC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKM3.640197', 'ACCTCAGTCAAG', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKM4.640180', 'TCGACCAAACAC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKM5.640177', 'CCACCCAGTAAC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKM6.640187', 'ATATCGCGATGA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKM7.640188', 'CGCCGGTAATCT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKM8.640201', 'CCGATGCCTTGA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME'),
('SKM9.640192', 'AGCAGGCACGAA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to Ê1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME');

-- Insert preprocessed information for raw data 0
INSERT INTO qiita.preprocessed_data (raw_data_id, preprocessed_params_table, preprocessed_params_id) VALUES (0, 'preprocessed_sequence_illumina_params', 0);

-- Insert the preprocessed filepath for raw data 0
INSERT INTO qiita.filepath (filepath, filepath_type_id) VALUES ('$QIITA_TEST_FOLDER/seqs.fna', 3), ('$QIITA_TEST_FOLDER/seqs.qual', 4);

-- Insert (link) the preprocessed data with the preprocessed filepaths
INSERT INTO qiita.preprocessed_filepath (preprocessed_data_id, filepath_id) VALUES (0, 2), (0, 3);

-- Insert the preprocessed illumina params used for raw data 0
INSERT INTO qiita.preprocessed_sequence_illumina_params (trim_length) VALUES (151);

-- Insert processed information for study 0 and processed data 0
INSERT INTO qiita.processed_data (preprocessed_data_id, processed_params_table, processed_params_id, processed_date) VALUES (0, 'processed_params_uclust', 0, '2012-10-01');

-- Populate the reference table
INSERT INTO qiita.reference (reference_name, reference_version, sequence_filepath, taxonomy_filepath, tree_filepath) VALUES ('GreenGenes', '4feb2011', '$QIITA_TEST_FOLDER/gg_97_otus_4feb2011.fasta', '$QIITA_TEST_FOLDER/greengenes_tax.txt', '$QIITA_TEST_FOLDER/gg_97_otus_4feb2011.tre')

-- Insert the processed params uclust used for preprocessed data 0
INSERT INTO qiita.processed_params_uclust (similarity, enable_rev_strand_match, suppress_new_clusters, reference_id) VALUES (0.97, 1, 1, 0);

-- Insert the biom table filepath for processed data 0
INSERT INTO qiita.filepath (filepath, filepath_type_id) VALUES ('$QIITA_TEST_FOLDER/study_1001_closed_reference_otu_table.biom', 5);

-- Insert (link) the processed data with the processed filepath
INSERT INTO qiita.processed_filepath (processed_data_id, filepath_id) VALUES (0, 4);
