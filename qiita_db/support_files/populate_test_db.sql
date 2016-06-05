-- Populate.sql sets the increment to begin at 10000, but all tests expect it to start at 1, so set it back to 1 for the test DB population
SELECT setval('qiita.study_study_id_seq', 1, false);

-- Patch 33.sql sets the increment to begin at 2000, but all tests expect it to start at 1, so set it back to 1 for the test DB population
SELECT setval('qiita.artifact_artifact_id_seq', 1, false);

-- Insert some users in the system. Passwords are 'password' for all users
INSERT INTO qiita.qiita_user (email, user_level_id, password, name,
    affiliation, address, phone) VALUES
    ('test@foo.bar', 4,
    '$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe', 'Dude',
    'Nowhere University', '123 fake st, Apt 0, Faketown, CO 80302',
    '111-222-3344'),
    ('shared@foo.bar', 3,
    '$2a$12$gnUi8Qg.0tvW243v889BhOBhWLIHyIJjjgaG6dxuRJkUM8nXG9Efe', 'Shared',
    'Nowhere University', '123 fake st, Apt 0, Faketown, CO 80302',
    '111-222-3344'),
    ('admin@foo.bar', 1,
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
INSERT INTO qiita.study (email, emp_person_id, first_contact,
    funding, timeseries_type_id, lab_person_id, metadata_complete,
    mixs_compliant, most_recent_contact, number_samples_collected,
    number_samples_promised, principal_investigator_id, reprocess,
    spatial_series, study_title, study_alias, study_description,
    study_abstract, vamps_id, ebi_study_accession, ebi_submission_status) VALUES
    ('test@foo.bar', 2, '2014-05-19 16:10', NULL, 1, 1, TRUE, TRUE,
    '2014-05-19 16:11', 27, 27, 3, FALSE, FALSE,
    'Identification of the Microbiomes for Cannabis Soils', 'Cannabis Soils', 'Analysis of the Cannabis Plant Microbiome',
    'This is a preliminary study to examine the microbiota associated with the Cannabis plant. Soils samples from the bulk soil, soil associated with the roots, and the rhizosphere were extracted and the DNA sequenced. Roots from three independent plants of different strains were examined. These roots were obtained November 11, 2011 from plants that had been harvested in the summer. Future studies will attempt to analyze the soils and rhizospheres from the same location at different time points in the plant lifecycle.',
    NULL, 'EBI123456-BB', 'submitted');

-- Add portal to the study
INSERT INTO qiita.study_portal (study_id, portal_type_id) VALUES (1, 1);

-- Add some environmental packages to the study
INSERT INTO qiita.study_environmental_package (study_id, environmental_package_name) VALUES (1, 'soil'), (1, 'plant-associated');

-- Insert study_users (share study 1 with shared user)
INSERT INTO qiita.study_users (study_id, email) VALUES (1, 'shared@foo.bar');

-- Insert PMIDs for study
INSERT INTO qiita.publication (doi, pubmed_id) VALUES ('10.100/123456', '123456'), ('10.100/7891011', '7891011');
INSERT INTO qiita.study_publication (study_id, publication_doi) VALUES (1, '10.100/123456'), (1, '10.100/7891011');

-- Insert an investigation
INSERT INTO qiita.investigation (investigation_name, investigation_description, contact_person_id) VALUES
    ('TestInvestigation', 'An investigation for testing purposes', 3);

-- Insert investigation_study (link study 1 with investigation 1)
INSERT INTO qiita.investigation_study (investigation_id, study_id) VALUES (1, 1);

-- Insert the study experimental factor for study 1
INSERT INTO qiita.study_experimental_factor (study_id, efo_id) VALUES (1, 1);

-- Add the study_sample for study 1
INSERT INTO qiita.study_sample (study_id, sample_id, ebi_sample_accession, biosample_accession) VALUES
    (1, '1.SKB8.640193', 'ERS000000', 'SAMEA0000000'),
    (1, '1.SKD8.640184', 'ERS000001', 'SAMEA0000001'),
    (1, '1.SKB7.640196', 'ERS000002', 'SAMEA0000002'),
    (1, '1.SKM9.640192', 'ERS000003', 'SAMEA0000003'),
    (1, '1.SKM4.640180', 'ERS000004', 'SAMEA0000004'),
    (1, '1.SKM5.640177', 'ERS000005', 'SAMEA0000005'),
    (1, '1.SKB5.640181', 'ERS000006', 'SAMEA0000006'),
    (1, '1.SKD6.640190', 'ERS000007', 'SAMEA0000007'),
    (1, '1.SKB2.640194', 'ERS000008', 'SAMEA0000008'),
    (1, '1.SKD2.640178', 'ERS000009', 'SAMEA0000009'),
    (1, '1.SKM7.640188', 'ERS000010', 'SAMEA0000010'),
    (1, '1.SKB1.640202', 'ERS000011', 'SAMEA0000011'),
    (1, '1.SKD1.640179', 'ERS000012', 'SAMEA0000012'),
    (1, '1.SKD3.640198', 'ERS000013', 'SAMEA0000013'),
    (1, '1.SKM8.640201', 'ERS000014', 'SAMEA0000014'),
    (1, '1.SKM2.640199', 'ERS000015', 'SAMEA0000015'),
    (1, '1.SKB9.640200', 'ERS000016', 'SAMEA0000016'),
    (1, '1.SKD5.640186', 'ERS000017', 'SAMEA0000017'),
    (1, '1.SKM3.640197', 'ERS000018', 'SAMEA0000018'),
    (1, '1.SKD9.640182', 'ERS000019', 'SAMEA0000019'),
    (1, '1.SKB4.640189', 'ERS000020', 'SAMEA0000020'),
    (1, '1.SKD7.640191', 'ERS000021', 'SAMEA0000021'),
    (1, '1.SKM6.640187', 'ERS000022', 'SAMEA0000022'),
    (1, '1.SKD4.640185', 'ERS000023', 'SAMEA0000023'),
    (1, '1.SKB3.640195', 'ERS000024', 'SAMEA0000024'),
    (1, '1.SKB6.640176', 'ERS000025', 'SAMEA0000025'),
    (1, '1.SKM1.640183', 'ERS000025', 'SAMEA0000026');

-- Crate the sample_1 dynamic table
CREATE TABLE qiita.sample_1 (
    sample_id                       varchar,
    season_environment              varchar,
    assigned_from_geo               varchar,
    texture                         varchar,
    taxon_id                        varchar,
    depth                           varchar,
    host_taxid                      varchar,
    common_name                     varchar,
    water_content_soil              varchar,
    elevation                       varchar,
    temp                            varchar,
    tot_nitro                       varchar,
    samp_salinity                   varchar,
    altitude                        varchar,
    env_biome                       varchar,
    country                         varchar,
    ph                              varchar,
    anonymized_name                 varchar,
    tot_org_carb                    varchar,
    description_duplicate           varchar,
    env_feature                     varchar,
    physical_specimen_location      varchar,
    physical_specimen_remaining     varchar,
    dna_extracted                   varchar,
    sample_type                     varchar,
    collection_timestamp            varchar,
    host_subject_id                 varchar,
    description                     varchar,
    latitude                        varchar,
    longitude                       varchar,
    scientific_name                 varchar,
    CONSTRAINT pk_sample_1 PRIMARY KEY ( sample_id )
);

-- Populates the sample_1 dynamic table
INSERT INTO qiita.sample_1 (sample_id, season_environment, assigned_from_geo, texture, taxon_id, depth, host_taxid, common_name, water_content_soil, elevation, temp, tot_nitro, samp_salinity, altitude, env_biome, country, ph, anonymized_name, tot_org_carb, description_duplicate, env_feature, physical_specimen_location, physical_specimen_remaining, dna_extracted, sample_type, collection_timestamp, host_subject_id, description, latitude, longitude, scientific_name) VALUES
    ('1.SKM7.640188', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '1118232', '0.15', '3483', 'root metagenome', '0.101', '114', '15', '1.3', '7.44', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.82', 'SKM7', '3.31', 'Bucu Roots', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:B6', 'Cannabis Soil Microbiome', 60.1102854322, 74.7123248382, '1118232'),
    ('1.SKD9.640182', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '1118232', '0.15', '3483', 'root metagenome', '0.178', '114', '15', '1.51', '7.1', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.82', 'SKD9', '4.32', 'Diesel Root', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:D3', 'Cannabis Soil Microbiome', 23.1218032799, 42.838497795, '1118232'),
    ('1.SKM8.640201', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '1118232', '0.15', '3483', 'root metagenome', '0.101', '114', '15', '1.3', '7.44', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.82', 'SKM8', '3.31', 'Bucu Roots', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:D8', 'Cannabis Soil Microbiome', 3.21190859967, 26.8138925876, '1118232'),
    ('1.SKB8.640193', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '1118232', '0.15', '3483', 'root metagenome', '0.164', '114', '15', '1.41', '7.15', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.94', 'SKB8', '5', 'Burmese root', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:M7', 'Cannabis Soil Microbiome', 74.0894932572, 65.3283470202, '1118232'),
    ('1.SKD2.640178', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '410658', '0.15', '3483', 'soil metagenome', '0.178', '114', '15', '1.51', '7.1', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.8', 'SKD2', '4.32', 'Diesel bulk', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:B5', 'Cannabis Soil Microbiome', 53.5050692395, 31.6056761814, '1118232'),
    ('1.SKM3.640197', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '410658', '0.15', '3483', 'soil metagenome', '0.101', '114', '15', '1.3', '7.44', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.82', 'SKM3', '3.31', 'Bucu bulk', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:B7', 'Cannabis Soil Microbiome', 'not applicable', 31.2003474585, '1118232'),
    ('1.SKM4.640180', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '939928', '0.15', '3483', 'rhizosphere metagenome', '0.101', '114', '15', '1.3', '7.44', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.82', 'SKM4', '3.31', 'Bucu Rhizo', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:D2', 'Cannabis Soil Microbiome', 'not applicable', 'not applicable', '1118232'),
    ('1.SKB9.640200', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '1118232', '0.15', '3483', 'root metagenome', '0.164', '114', '15', '1.41', '7.15', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.8', 'SKB9', '5', 'Burmese root', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:B3', 'Cannabis Soil Microbiome', 12.6245524972, 96.0693176066, '1118232'),
    ('1.SKB4.640189', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '939928', '0.15', '3483', 'rhizosphere metagenome', '0.164', '114', '15', '1.41', '7.15', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.94', 'SKB4', '5', 'Burmese Rhizo', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:D7', 'Cannabis Soil Microbiome', 43.9614715197, 82.8516734159, '1118232'),
    ('1.SKB5.640181', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '939928', '0.15', '3483', 'rhizosphere metagenome', '0.164', '114', '15', '1.41', '7.15', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.94', 'SKB5', '5', 'Burmese Rhizo', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:M4', 'Cannabis Soil Microbiome', 10.6655599093, 70.784770579, '1118232'),
    ('1.SKB6.640176', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '939928', '0.15', '3483', 'rhizosphere metagenome', '0.164', '114', '15', '1.41', '7.15', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.94', 'SKB6', '5', 'Burmese Rhizo', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:D5', 'Cannabis Soil Microbiome', 78.3634273709, 74.423907894, '1118232'),
    ('1.SKM2.640199', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '410658', '0.15', '3483', 'soil metagenome', '0.101', '114', '15', '1.3', '7.44', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.82', 'SKM2', '3.31', 'Bucu bulk', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:D4', 'Cannabis Soil Microbiome', 82.8302905615, 86.3615778099, '1118232'),
    ('1.SKM5.640177', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '939928', '0.15', '3483', 'rhizosphere metagenome', '0.101', '114', '15', '1.3', '7.44', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.82', 'SKM5', '3.31', 'Bucu Rhizo', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:M3', 'Cannabis Soil Microbiome', 44.9725384282, 66.1920014699, '1118232'),
    ('1.SKB1.640202', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '410658', '0.15', '3483', 'soil metagenome', '0.164', '114', '15', '1.41', '7.15', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.94', 'SKB1', '5', 'Burmese bulk', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:M2', 'Cannabis Soil Microbiome', 4.59216095574, 63.5115213108, '1118232'),
    ('1.SKD8.640184', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '1118232', '0.15', '3483', 'root metagenome', '0.178', '114', '15', '1.51', '7.1', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.8', 'SKD8', '4.32', 'Diesel Root', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:D9', 'Cannabis Soil Microbiome', 57.571893782, 32.5563076447, '1118232'),
    ('1.SKD4.640185', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '939928', '0.15', '3483', 'rhizosphere metagenome', '0.178', '114', '15', '1.51', '7.1', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.8', 'SKD4', '4.32', 'Diesel Rhizo', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:M9', 'Cannabis Soil Microbiome', 40.8623799474, 6.66444220187, '1118232'),
    ('1.SKB3.640195', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '410658', '0.15', '3483', 'soil metagenome', '0.164', '114', '15', '1.41', '7.15', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.94', 'SKB3', '5', 'Burmese bulk', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:M6', 'Cannabis Soil Microbiome', 95.2060749748, 27.3592668624, '1118232'),
    ('1.SKM1.640183', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '410658', '0.15', '3483', 'soil metagenome', '0.101', '114', '15', '1.3', '7.44', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.82', 'SKM1', '3.31', 'Bucu bulk', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:D1', 'Cannabis Soil Microbiome', 38.2627021402, 3.48274264219, '1118232'),
    ('1.SKB7.640196', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '1118232', '0.15', '3483', 'root metagenome', '0.164', '114', '15', '1.41', '7.15', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.94', 'SKB7', '5', 'Burmese root', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:M8', 'Cannabis Soil Microbiome', 13.089194595, 92.5274472082, '1118232'),
    ('1.SKD3.640198', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '410658', '0.15', '3483', 'soil metagenome', '0.178', '114', '15', '1.51', '7.1', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.8', 'SKD3', '4.32', 'Diesel bulk', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:B1', 'Cannabis Soil Microbiome', 84.0030227585, 66.8954849864, '1118232'),
    ('1.SKD7.640191', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '1118232', '0.15', '3483', 'root metagenome', '0.178', '114', '15', '1.51', '7.1', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.8', 'SKD7', '4.32', 'Diesel Root', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:D6', 'Cannabis Soil Microbiome', 68.51099627, 2.35063674718, '1118232'),
    ('1.SKD6.640190', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '939928', '0.15', '3483', 'rhizosphere metagenome', '0.178', '114', '15', '1.51', '7.1', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.8', 'SKD6', '4.32', 'Diesel Rhizo', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:B9', 'Cannabis Soil Microbiome', 29.1499460692, 82.1270418227, '1118232'),
    ('1.SKB2.640194', 'winter', 'n', '64.6 sand, 17.6 silt, 17.8 clay', '410658', '0.15', '3483', 'soil metagenome', '0.164', '114', '15', '1.41', '7.15', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.94', 'SKB2', '5', 'Burmese bulk', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:B4', 'Cannabis Soil Microbiome', 35.2374368957, 68.5041623253, '1118232'),
    ('1.SKM9.640192', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '1118232', '0.15', '3483', 'root metagenome', '0.101', '114', '15', '1.3', '7.44', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.82', 'SKM9', '3.31', 'Bucu Roots', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:B8', 'Cannabis Soil Microbiome', 12.7065957714, 84.9722975792, '1118232'),
    ('1.SKM6.640187', 'winter', 'n', '63.1 sand, 17.7 silt, 19.2 clay', '939928', '0.15', '3483', 'rhizosphere metagenome', '0.101', '114', '15', '1.3', '7.44', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.82', 'SKM6', '3.31', 'Bucu Rhizo', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:B2', 'Cannabis Soil Microbiome', 0.291867635913, 68.5945325743, '1118232'),
    ('1.SKD5.640186', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '939928', '0.15', '3483', 'rhizosphere metagenome', '0.178', '114', '15', '1.51', '7.1', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.8', 'SKD5', '4.32', 'Diesel Rhizo', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:M1', 'Cannabis Soil Microbiome', 85.4121476399, 15.6526750776, '1118232'),
    ('1.SKD1.640179', 'winter', 'n', '66 sand, 16.3 silt, 17.7 clay', '410658', '0.15', '3483', 'soil metagenome', '0.178', '114', '15', '1.51', '7.1', '0', 'ENVO:Temperate grasslands, savannas, and shrubland biome', 'GAZ:United States of America', '6.8', 'SKD1', '4.32', 'Diesel bulk', 'ENVO:plant-associated habitat', 'ANL', TRUE, TRUE, 'ENVO:soil', '11/11/11 13:00:00', '1001:M5', 'Cannabis Soil Microbiome', 68.0991287718, 34.8360987059, '1118232');

-- Create a new prep template for the added raw data
INSERT INTO qiita.prep_template (data_type_id, preprocessing_status, investigation_type) VALUES (2, 'success', 'Metagenomics');
INSERT INTO qiita.prep_template (data_type_id, preprocessing_status, investigation_type) VALUES (2, 'success', 'Metagenomics');

-- Add the common prep info for study 1
INSERT INTO qiita.prep_template_sample (prep_template_id, sample_id, ebi_experiment_accession) VALUES
    (1, '1.SKB8.640193', 'ERX0000000'),
    (1, '1.SKD8.640184', 'ERX0000001'),
    (1, '1.SKB7.640196', 'ERX0000002'),
    (1, '1.SKM9.640192', 'ERX0000003'),
    (1, '1.SKM4.640180', 'ERX0000004'),
    (1, '1.SKM5.640177', 'ERX0000005'),
    (1, '1.SKB5.640181', 'ERX0000006'),
    (1, '1.SKD6.640190', 'ERX0000007'),
    (1, '1.SKB2.640194', 'ERX0000008'),
    (1, '1.SKD2.640178', 'ERX0000009'),
    (1, '1.SKM7.640188', 'ERX0000010'),
    (1, '1.SKB1.640202', 'ERX0000011'),
    (1, '1.SKD1.640179', 'ERX0000012'),
    (1, '1.SKD3.640198', 'ERX0000013'),
    (1, '1.SKM8.640201', 'ERX0000014'),
    (1, '1.SKM2.640199', 'ERX0000015'),
    (1, '1.SKB9.640200', 'ERX0000016'),
    (1, '1.SKD5.640186', 'ERX0000017'),
    (1, '1.SKM3.640197', 'ERX0000018'),
    (1, '1.SKD9.640182', 'ERX0000019'),
    (1, '1.SKB4.640189', 'ERX0000020'),
    (1, '1.SKD7.640191', 'ERX0000021'),
    (1, '1.SKM6.640187', 'ERX0000022'),
    (1, '1.SKD4.640185', 'ERX0000023'),
    (1, '1.SKB3.640195', 'ERX0000024'),
    (1, '1.SKB6.640176', 'ERX0000025'),
    (1, '1.SKM1.640183', 'ERX0000026');

-- Add the common prep info for study 2
INSERT INTO qiita.prep_template_sample (prep_template_id, sample_id, ebi_experiment_accession) VALUES
    (2, '1.SKB8.640193', 'ERX0000000'),
    (2, '1.SKD8.640184', 'ERX0000001'),
    (2, '1.SKB7.640196', 'ERX0000002'),
    (2, '1.SKM9.640192', 'ERX0000003'),
    (2, '1.SKM4.640180', 'ERX0000004'),
    (2, '1.SKM5.640177', 'ERX0000005'),
    (2, '1.SKB5.640181', 'ERX0000006'),
    (2, '1.SKD6.640190', 'ERX0000007'),
    (2, '1.SKB2.640194', 'ERX0000008'),
    (2, '1.SKD2.640178', 'ERX0000009'),
    (2, '1.SKM7.640188', 'ERX0000010'),
    (2, '1.SKB1.640202', 'ERX0000011'),
    (2, '1.SKD1.640179', 'ERX0000012'),
    (2, '1.SKD3.640198', 'ERX0000013'),
    (2, '1.SKM8.640201', 'ERX0000014'),
    (2, '1.SKM2.640199', 'ERX0000015'),
    (2, '1.SKB9.640200', 'ERX0000016'),
    (2, '1.SKD5.640186', 'ERX0000017'),
    (2, '1.SKM3.640197', 'ERX0000018'),
    (2, '1.SKD9.640182', 'ERX0000019'),
    (2, '1.SKB4.640189', 'ERX0000020'),
    (2, '1.SKD7.640191', 'ERX0000021'),
    (2, '1.SKM6.640187', 'ERX0000022'),
    (2, '1.SKD4.640185', 'ERX0000023'),
    (2, '1.SKB3.640195', 'ERX0000024'),
    (2, '1.SKB6.640176', 'ERX0000025'),
    (2, '1.SKM1.640183', 'ERX0000026');

-- Crate the prep_1 dynamic table
CREATE TABLE qiita.prep_1 (
    sample_id                       varchar,
    barcode                         varchar,
    LIBRARY_CONSTRUCTION_PROTOCOL   varchar,
    primer                          varchar,
    TARGET_SUBFRAGMENT              varchar,
    target_gene                     varchar,
    RUN_CENTER                      varchar,
    RUN_PREFIX                      varchar,
    RUN_DATE                        varchar,
    EXPERIMENT_CENTER               varchar,
    EXPERIMENT_DESIGN_DESCRIPTION   varchar,
    EXPERIMENT_TITLE                varchar,
    PLATFORM                        varchar,
    INSTRUMENT_MODEL                varchar,
    SAMP_SIZE                       varchar,
    SEQUENCING_METH                 varchar,
    illumina_technology             varchar,
    SAMPLE_CENTER                   varchar,
    pcr_primers                     varchar,
    STUDY_CENTER                    varchar,
    center_name                     varchar,
    center_project_name             varchar,
    emp_status                      varchar,
    CONSTRAINT pk_prep_1 PRIMARY KEY ( sample_id )
);

-- Crate the prep_2 dynamic table
CREATE TABLE qiita.prep_2 (
    sample_id                       varchar,
    barcode                         varchar,
    LIBRARY_CONSTRUCTION_PROTOCOL   varchar,
    primer                          varchar,
    TARGET_SUBFRAGMENT              varchar,
    target_gene                     varchar,
    RUN_CENTER                      varchar,
    RUN_PREFIX                      varchar,
    RUN_DATE                        varchar,
    EXPERIMENT_CENTER               varchar,
    EXPERIMENT_DESIGN_DESCRIPTION   varchar,
    EXPERIMENT_TITLE                varchar,
    PLATFORM                        varchar,
    INSTRUMENT_MODEL                varchar,
    SAMP_SIZE                       varchar,
    SEQUENCING_METH                 varchar,
    illumina_technology             varchar,
    SAMPLE_CENTER                   varchar,
    pcr_primers                     varchar,
    STUDY_CENTER                    varchar,
    center_name                     varchar,
    center_project_name             varchar,
    emp_status                      varchar,
    CONSTRAINT pk_prep_2 PRIMARY KEY ( sample_id )
);

-- Populates the prep_1 dynamic table
INSERT INTO qiita.prep_1 (sample_id, barcode, LIBRARY_CONSTRUCTION_PROTOCOL, primer, TARGET_SUBFRAGMENT, target_gene, RUN_CENTER, RUN_PREFIX, RUN_DATE, EXPERIMENT_CENTER, EXPERIMENT_DESIGN_DESCRIPTION, EXPERIMENT_TITLE, PLATFORM, INSTRUMENT_MODEL, SAMP_SIZE, SEQUENCING_METH, illumina_technology, SAMPLE_CENTER, pcr_primers, STUDY_CENTER, center_name, center_project_name, emp_status) VALUES
    ('1.SKB1.640202', 'GTCCGCAAGTTA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKB2.640194', 'CGTAGAGCTCTC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKB3.640195', 'CCTCTGAGAGCT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKB4.640189', 'CCTCGATGCAGT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKB5.640181', 'GCGGACTATTCA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKB6.640176', 'CGTGCACAATTG', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKB7.640196', 'CGGCCTAAGTTC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKB8.640193', 'AGCGCTCACATC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKB9.640200', 'TGGTTATGGCAC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD1.640179', 'CGAGGTTCTGAT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD2.640178', 'AACTCCTGTGGA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD3.640198', 'TAATGGTCGTAG', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD4.640185', 'TTGCACCGTCGA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD5.640186', 'TGCTACAGACGT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD6.640190', 'ATGGCCTGACTA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD7.640191', 'ACGCACATACAA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD8.640184', 'TGAGTGGTCTGT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD9.640182', 'GATAGCACTCGT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM1.640183', 'TAGCGCGAACTT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM2.640199', 'CATACACGCACC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM3.640197', 'ACCTCAGTCAAG', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM4.640180', 'TCGACCAAACAC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM5.640177', 'CCACCCAGTAAC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM6.640187', 'ATATCGCGATGA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM7.640188', 'CGCCGGTAATCT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM8.640201', 'CCGATGCCTTGA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM9.640192', 'AGCAGGCACGAA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP');


-- Populates the prep_2 dynamic table
INSERT INTO qiita.prep_2 (sample_id, barcode, LIBRARY_CONSTRUCTION_PROTOCOL, primer, TARGET_SUBFRAGMENT, target_gene, RUN_CENTER, RUN_PREFIX, RUN_DATE, EXPERIMENT_CENTER, EXPERIMENT_DESIGN_DESCRIPTION, EXPERIMENT_TITLE, PLATFORM, INSTRUMENT_MODEL, SAMP_SIZE, SEQUENCING_METH, illumina_technology, SAMPLE_CENTER, pcr_primers, STUDY_CENTER, center_name, center_project_name, emp_status) VALUES
    ('1.SKB1.640202', 'GTCCGCAAGTTA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKB2.640194', 'CGTAGAGCTCTC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKB3.640195', 'CCTCTGAGAGCT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKB4.640189', 'CCTCGATGCAGT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKB5.640181', 'GCGGACTATTCA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKB6.640176', 'CGTGCACAATTG', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKB7.640196', 'CGGCCTAAGTTC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKB8.640193', 'AGCGCTCACATC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKB9.640200', 'TGGTTATGGCAC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD1.640179', 'CGAGGTTCTGAT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD2.640178', 'AACTCCTGTGGA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD3.640198', 'TAATGGTCGTAG', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD4.640185', 'TTGCACCGTCGA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD5.640186', 'TGCTACAGACGT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD6.640190', 'ATGGCCTGACTA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD7.640191', 'ACGCACATACAA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD8.640184', 'TGAGTGGTCTGT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKD9.640182', 'GATAGCACTCGT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM1.640183', 'TAGCGCGAACTT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM2.640199', 'CATACACGCACC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM3.640197', 'ACCTCAGTCAAG', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM4.640180', 'TCGACCAAACAC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM5.640177', 'CCACCCAGTAAC', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM6.640187', 'ATATCGCGATGA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM7.640188', 'CGCCGGTAATCT', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM8.640201', 'CCGATGCCTTGA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP'),
    ('1.SKM9.640192', 'AGCAGGCACGAA', 'This analysis was done as in Caporaso et al 2011 Genome research. The PCR primers (F515/R806) were developed against the V4 region of the 16S rRNA (both bacteria and archaea), which we determined would yield optimal community clustering with reads of this length using a procedure similar to that of ref. 15. [For reference, this primer pair amplifies the region 533_786 in the Escherichia coli strain 83972 sequence (greengenes accession no. prokMSA_id:470367).] The reverse PCR primer is barcoded with a 12-base error-correcting Golay code to facilitate multiplexing of up to 1,500 samples per lane, and both PCR primers contain sequencer adapter regions.', 'GTGCCAGCMGCCGCGGTAA', 'V4', '16S rRNA', 'ANL', 's_G1_L001_sequences', '8/1/12', 'ANL', 'micro biome of soil and rhizosphere of cannabis plants from CA', 'Cannabis Soil Microbiome', 'Illumina', 'Illumina MiSeq', '.25,g', 'Sequencing by synthesis', 'MiSeq', 'ANL', 'FWD:GTGCCAGCMGCCGCGGTAA; REV:GGACTACHVGGGTWTCTAAT', 'CCME', 'ANL', NULL, 'EMP');

-- Link the prep template to the study
INSERT INTO qiita.study_prep_template (study_id, prep_template_id) VALUES (1, 1);
INSERT INTO qiita.study_prep_template (study_id, prep_template_id) VALUES (1, 2);

-- Insert some artifacts
--   1 (Raw fastq) ---> 2 (demultiplexed) ---> 4 (otu table)
--                  \-> 3 (demultiplexed)
INSERT INTO qiita.artifact (name, generated_timestamp, command_id, command_parameters,
                            visibility_id, artifact_type_id, data_type_id)
    VALUES ('Raw data 1', 'Mon Oct 1 09:30:27 2012', NULL, NULL, 3, 3, 2),
           ('Demultiplexed 1', 'Mon Oct 1 10:30:27 2012', 1, '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5,"input_data":1,"phred_offset":""}'::json,
            3, 6, 2),
           ('Demultiplexed 2', 'Mon Oct 1 11:30:27 2012', 1, '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":true,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5,"input_data":1,"phred_offset":""}'::json,
            3, 6, 2),
           ('BIOM', 'Tue Oct 2 17:30:00 2012', 3, '{"reference":1,"sortmerna_e_value":1,"sortmerna_max_pos":10000,"similarity":0.97,"sortmerna_coverage":0.97,"threads":1,"input_data":2}'::json,
            3, 7, 2),
           ('BIOM', 'Tue Oct 2 17:30:00 2012', 3, '{"reference":1,"sortmerna_e_value":1,"sortmerna_max_pos":10000,"similarity":0.97,"sortmerna_coverage":0.97,"threads":1,"input_data":2}'::json,
            3, 7, 2),
           ('BIOM', 'Tue Oct 2 17:30:00 2012', 3, '{"reference":2,"sortmerna_e_value":1,"sortmerna_max_pos":10000,"similarity":0.97,"sortmerna_coverage":0.97,"threads":1,"input_data":2}'::json,
            3, 7, 1),
           ('BIOM', 'Tue Oct 2 17:30:00 2012', NULL, NULL,
            3, 7, 1);

-- Link the child artifacts with their parents artifacts
INSERT INTO qiita.parent_artifact (parent_id, artifact_id)
    VALUES (1, 2), (1, 3),
           (2, 4), (2, 5), (2, 6);

-- Insert the jobs that processed the previous artifacts
INSERT INTO qiita.processing_job (processing_job_id, email, command_id, command_parameters, processing_job_status_id)
    VALUES ('6d368e16-2242-4cf8-87b4-a5dc40bb890b', 'test@foo.bar', 1, '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5,"input_data":1,"phred_offset":""}'::json, 3),
           ('4c7115e8-4c8e-424c-bf25-96c292ca1931', 'test@foo.bar', 1, '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":true,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5,"input_data":1,"phred_offset":""}'::json, 3),
           ('3c9991ab-6c14-4368-a48c-841e8837a79c', 'test@foo.bar', 3, '{"reference":1,"sortmerna_e_value":1,"sortmerna_max_pos":10000,"similarity":0.97,"sortmerna_coverage":0.97,"threads":1,"input_data":2}'::json, 3);

-- Relate the above jobs with the artifacts
INSERT INTO qiita.artifact_processing_job (artifact_id, processing_job_id)
    VALUES (1, '6d368e16-2242-4cf8-87b4-a5dc40bb890b'),
           (1, '4c7115e8-4c8e-424c-bf25-96c292ca1931'),
           (2, '3c9991ab-6c14-4368-a48c-841e8837a79c');

-- Insert filepaths for the artifacts and reference
INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id, data_directory_id)
    VALUES ('1_s_G1_L001_sequences.fastq.gz', 1, '852952723', 1, 5),
           ('1_s_G1_L001_sequences_barcodes.fastq.gz', 3, '852952723', 1, 5),
           ('1_seqs.fna', 4, '852952723', 1, 3),
           ('1_seqs.qual', 5, '852952723', 1, 3),
           ('1_seqs.demux', 6, 852952723, 1, 3),
           ('GreenGenes_13_8_97_otus.fasta', 10, '852952723', 1, 6),
           ('GreenGenes_13_8_97_otu_taxonomy.txt', 11, '852952723', 1, 6),
           ('GreenGenes_13_8_97_otus.tree', 12, '852952723', 1, 6),
           ('1_study_1001_closed_reference_otu_table.biom', 7, '852952723', 1, 4),
           ('Silva_97_otus.fasta', 10, '852952723', 1, 6),
           ('Silva_97_otu_taxonomy.txt', 11, '852952723', 1, 6),
           ('1_study_1001_closed_reference_otu_table_Silva.biom', 7, '852952723', 1, 4);

-- Link the artifacts with the filepaths
INSERT INTO qiita.artifact_filepath (artifact_id, filepath_id)
    VALUES (1, 1), (1, 2),
           (2, 3), (2, 4), (2, 5),
           (4, 9), (5, 9), (6, 12);

-- Link the artifact with the prep template
UPDATE qiita.prep_template SET artifact_id = 1 WHERE prep_template_id = 1;
UPDATE qiita.prep_template SET artifact_id = 7 WHERE prep_template_id = 2;

-- Link the study with the artifacts
INSERT INTO qiita.study_artifact (study_id, artifact_id)
    VALUES (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7);

-- Insert EBI information for artifact 2
INSERT INTO qiita.ebi_run_accession (sample_id, artifact_id, ebi_run_accession)
    VALUES ('1.SKB1.640202', 2, 'ERR0000001'),
           ('1.SKB2.640194', 2, 'ERR0000002'),
           ('1.SKB3.640195', 2, 'ERR0000003'),
           ('1.SKB4.640189', 2, 'ERR0000004'),
           ('1.SKB5.640181', 2, 'ERR0000005'),
           ('1.SKB6.640176', 2, 'ERR0000006'),
           ('1.SKB7.640196', 2, 'ERR0000007'),
           ('1.SKB8.640193', 2, 'ERR0000008'),
           ('1.SKB9.640200', 2, 'ERR0000009'),
           ('1.SKD1.640179', 2, 'ERR0000010'),
           ('1.SKD2.640178', 2, 'ERR0000011'),
           ('1.SKD3.640198', 2, 'ERR0000012'),
           ('1.SKD4.640185', 2, 'ERR0000013'),
           ('1.SKD5.640186', 2, 'ERR0000014'),
           ('1.SKD6.640190', 2, 'ERR0000015'),
           ('1.SKD7.640191', 2, 'ERR0000016'),
           ('1.SKD8.640184', 2, 'ERR0000017'),
           ('1.SKD9.640182', 2, 'ERR0000018'),
           ('1.SKM1.640183', 2, 'ERR0000019'),
           ('1.SKM2.640199', 2, 'ERR0000020'),
           ('1.SKM3.640197', 2, 'ERR0000021'),
           ('1.SKM4.640180', 2, 'ERR0000022'),
           ('1.SKM5.640177', 2, 'ERR0000023'),
           ('1.SKM6.640187', 2, 'ERR0000024'),
           ('1.SKM7.640188', 2, 'ERR0000025'),
           ('1.SKM8.640201', 2, 'ERR0000026'),
           ('1.SKM9.640192', 2, 'ERR0000027');

-- Populate the reference table
INSERT INTO qiita.reference (reference_name, reference_version, sequence_filepath, taxonomy_filepath, tree_filepath) VALUES
('Greengenes', '13_8', 6, 7, 8),
('Silva', 'test', 10, 11, NULL);

-- Insert filepath for job results files
INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id, data_directory_id) VALUES
('1_job_result.txt', 9, '852952723', 1, 2),
('2_test_folder', 8, '852952723', 1, 2);

-- Insert jobs
INSERT INTO qiita.job (data_type_id, job_status_id, command_id, options, input_file_reference_id, input_file_software_command_id) VALUES
(2, 1, 1, '{"--otu_table_fp":1}', 1, 3),
(2, 3, 2, '{"--mapping_fp":1,"--otu_table_fp":1}', 2, 3),
(2, 1, 2, '{"--mapping_fp":1,"--otu_table_fp":1}', 1, 3);

-- Add job results
INSERT INTO qiita.job_results_filepath (job_id, filepath_id) VALUES (1, 13), (2, 14);

-- Insert Analysis
INSERT INTO qiita.analysis (email, name, description, analysis_status_id, pmid) VALUES ('test@foo.bar', 'SomeAnalysis', 'A test analysis', 1, '121112'), ('admin@foo.bar', 'SomeSecondAnalysis', 'Another test analysis', 1, '22221112');
INSERT INTO qiita.analysis_portal (analysis_id, portal_type_id) VALUES (1, 1), (2, 1);
-- Insert Analysis Workflow
INSERT INTO qiita.analysis_workflow (analysis_id, step) VALUES (1, 3), (2, 3);

-- Attach jobs to analysis
INSERT INTO qiita.analysis_job (analysis_id, job_id) VALUES (1, 1), (1, 2), (2, 3);

-- Insert filepath for analysis biom files
INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id, data_directory_id) VALUES
('1_analysis_18S.biom', 7, '852952723', 1, 1), ('1_analysis_mapping.txt', 9, '852952723', 1, 1);

-- Attach filepath to analysis
INSERT INTO qiita.analysis_filepath (analysis_id, filepath_id, data_type_id) VALUES (1, 15, 2), (1, 16, NULL);

-- Attach samples to analysis
INSERT INTO qiita.analysis_sample (analysis_id, artifact_id, sample_id) VALUES
(1, 4, '1.SKB8.640193'), (1, 4, '1.SKD8.640184'), (1, 4, '1.SKB7.640196'), (1, 4, '1.SKM9.640192'), (1, 4, '1.SKM4.640180'),
(2, 4, '1.SKB8.640193'), (2, 4, '1.SKD8.640184'), (2, 4, '1.SKB7.640196'), (2, 4, '1.SKM3.640197'),
(1, 5, '1.SKB8.640193'), (1, 5, '1.SKD8.640184'), (1, 5, '1.SKB7.640196'), (1, 5, '1.SKM9.640192'), (1, 5, '1.SKM4.640180'),
(2, 5, '1.SKB8.640193'), (2, 5, '1.SKD8.640184'), (2, 5, '1.SKB7.640196'), (2, 5, '1.SKM3.640197'),
(1, 6, '1.SKB8.640193'), (1, 6, '1.SKD8.640184'), (1, 6, '1.SKB7.640196'), (1, 6, '1.SKM9.640192'), (1, 6, '1.SKM4.640180'),
(2, 6, '1.SKB8.640193'), (2, 6, '1.SKD8.640184'), (2, 6, '1.SKB7.640196'), (2, 6, '1.SKM3.640197');

--Share analysis with shared user
INSERT INTO qiita.analysis_users (analysis_id, email) VALUES (1, 'shared@foo.bar');

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

-- Create the new sample_template_filepath
INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id, data_directory_id) VALUES ('1_19700101-000000.txt', 14, '852952723', 1, 9);
INSERT INTO qiita.sample_template_filepath VALUES (1, 17);

--add collection to the database
INSERT INTO qiita.collection (email, name, description) VALUES ('test@foo.bar', 'TEST_COLLECTION', 'collection for testing purposes');

--associate analyses and jobs with collection
INSERT INTO qiita.collection_analysis (collection_id, analysis_id) VALUES (1, 1);
INSERT INTO qiita.collection_job (collection_id, job_id) VALUES (1, 1);

--share collection with shared user
INSERT INTO qiita.collection_users (email, collection_id) VALUES ('shared@foo.bar', 1);

--add default analysis for users
INSERT INTO qiita.analysis (email, name, description, dflt, analysis_status_id) VALUES ('test@foo.bar', 'test@foo.bar-dflt-1', 'dflt', true, 1), ('admin@foo.bar', 'admin@foo.bar-dflt-1', 'dflt', true, 1), ('shared@foo.bar', 'shared@foo.bar-dflt-1', 'dflt', true, 1), ('demo@microbio.me', 'demo@microbio.me-dflt-1', 'dflt', true, 1), ('test@foo.bar', 'test@foo.bar-dflt-2', 'dflt', true, 1), ('admin@foo.bar', 'admin@foo.bar-dflt-2', 'dflt', true, 2), ('shared@foo.bar', 'shared@foo.bar-dflt-2', 'dflt', true, 2), ('demo@microbio.me', 'demo@microbio.me-dflt-2', 'dflt', true, 2);
INSERT INTO qiita.analysis_portal (analysis_id, portal_type_id) VALUES (3, 1), (4, 1), (5, 1), (6, 1), (7, 2), (8, 2), (9, 2), (10, 2);

-- Attach samples to analysis
INSERT INTO qiita.analysis_sample (analysis_id, artifact_id, sample_id)
    VALUES (3, 4, '1.SKD8.640184'), (3, 4, '1.SKB7.640196'), (3, 4, '1.SKM9.640192'), (3, 4, '1.SKM4.640180');

-- Create the new prep_template_filepath
INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id, data_directory_id) VALUES ('1_prep_1_19700101-000000.txt', 15, '3703494589', 1, 9);
INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id, data_directory_id) VALUES ('1_prep_1_qiime_19700101-000000.txt', 16, '3703494589', 1, 9);
INSERT INTO qiita.prep_template_filepath VALUES (1, 18), (1, 19);
INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id, data_directory_id) VALUES ('1_prep_1_19700101-000000.txt', 15, '3703494589', 1, 9);
INSERT INTO qiita.filepath (filepath, filepath_type_id, checksum, checksum_algorithm_id, data_directory_id) VALUES ('1_prep_1_qiime_19700101-000000.txt', 16, '3703494589', 1, 9);
INSERT INTO qiita.prep_template_filepath VALUES (1, 20), (1, 21);


-- Create some test messages
INSERT INTO qiita.message (message) VALUES ('message 1'), ('Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque sed auctor ex, non placerat sapien. Vestibulum vestibulum massa ut sapien condimentum, cursus consequat diam sodales. Nulla aliquam arcu ut massa auctor, et vehicula mauris tempor. In lacinia viverra ante quis pellentesque. Nunc vel mi accumsan, porttitor eros ut, pharetra elit. Nulla ac nisi quis dui egestas malesuada vitae ut mauris. Morbi blandit non nisl a finibus. In erat velit, congue at ipsum sit amet, venenatis bibendum sem. Curabitur vel odio sed est rutrum rutrum. Quisque efficitur ut purus in ultrices. Pellentesque eu auctor justo.'), ('message <a href="#">3</a>');
INSERT INTO qiita.message_user (message_id, email) VALUES (1, 'test@foo.bar'),(1, 'shared@foo.bar'),(2, 'test@foo.bar'),(3, 'test@foo.bar');

-- Create a loggin entry
INSERT INTO qiita.logging (time, severity_id, msg, information)
    VALUES ('Sun Nov 22 21:29:30 2015', 2, 'Error message', '{}');

-- Create some processing jobs
INSERT INTO qiita.processing_job
        (processing_job_id, email, command_id, command_parameters,
         processing_job_status_id, logging_id, heartbeat, step)
    VALUES ('063e553b-327c-4818-ab4a-adfe58e49860', 'test@foo.bar', 1, '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5,"input_data":1,"phred_offset":""}'::json, 1, NULL, NULL, NULL),
           ('bcc7ebcd-39c1-43e4-af2d-822e3589f14d', 'test@foo.bar', 2, '{"min_seq_len":100,"max_seq_len":1000,"trim_seq_length":false,"min_qual_score":25,"max_ambig":6,"max_homopolymer":6,"max_primer_mismatch":0,"barcode_type":"golay_12","max_barcode_errors":1.5,"disable_bc_correction":false,"qual_score_window":0,"disable_primers":false,"reverse_primers":"disable","reverse_primer_mismatches":0,"truncate_ambi_bases":false,"input_data":1}'::json, 2, NULL, 'Sun Nov 22 21:00:00 2015', 'demultiplexing'),
           ('b72369f9-a886-4193-8d3d-f7b504168e75', 'shared@foo.bar', 1, '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":true,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5,"input_data":1,"phred_offset":""}'::json, 3, NULL, 'Sun Nov 22 21:15:00 2015', NULL),
           ('d19f76ee-274e-4c1b-b3a2-a12d73507c55', 'shared@foo.bar', 3, '{"reference":1,"sortmerna_e_value":1,"sortmerna_max_pos":10000,"similarity":0.97,"sortmerna_coverage":0.97,"threads":1,"input_data":2}'::json, 4, 1, 'Sun Nov 22 21:30:00 2015', 'generating demux file'),
           ('ac653cb5-76a6-4a45-929e-eb9b2dee6b63', 'test@foo.bar', 1, '{"max_bad_run_length":3,"min_per_read_length_fraction":0.75,"sequence_max_n":0,"rev_comp_barcode":false,"rev_comp_mapping_barcodes":false,"rev_comp":false,"phred_quality_threshold":3,"barcode_type":"golay_12","max_barcode_errors":1.5,"input_data":1}'::json, 5, NULL, NULL, NULL);

INSERT INTO qiita.artifact_processing_job (artifact_id, processing_job_id)
    VALUES (1, '063e553b-327c-4818-ab4a-adfe58e49860'),
           (1, 'bcc7ebcd-39c1-43e4-af2d-822e3589f14d'),
           (1, 'b72369f9-a886-4193-8d3d-f7b504168e75'),
           (2, 'd19f76ee-274e-4c1b-b3a2-a12d73507c55');

-- Add client ids and secrets

INSERT INTO qiita.oauth_identifiers (client_id) VALUES ('DWelYzEYJYcZ4wlqUp0bHGXojrvZVz0CNBJvOqUKcrPQ5p4UqE');
INSERT INTO qiita.oauth_identifiers (client_id, client_secret) VALUES ('19ndkO3oMKsoChjVVWluF7QkxHRfYhTKSFbAVt8IhK7gZgDaO4', 'J7FfQ7CQdOxuKhQAf1eoGgBAE81Ns8Gu3EKaWFm3IO2JKhAmmCWZuabe0O5Mp28s1');
INSERT INTO qiita.oauth_identifiers (client_id, client_secret) VALUES ('yKDgajoKn5xlOA8tpo48Rq8mWJkH9z4LBCx2SvqWYLIryaan2u', '9xhU5rvzq8dHCEI5sSN95jesUULrZi6pT6Wuc71fDbFbsrnWarcSq56TJLN4kP4hH');
INSERT INTO qiita.oauth_identifiers (client_id, client_secret) VALUES ('dHgaXDwq665ksFPqfIoD3Jt8KRXdSioTRa4lGa5mGDnz6JTIBf', 'xqx61SD4M2EWbaS0WYv3H1nIemkvEAMIn16XMLjy5rTCqi7opCcWbfLINEwtV48bQ');
INSERT INTO qiita.oauth_identifiers (client_id, client_secret) VALUES ('4MOBzUBHBtUmwhaC258H7PS0rBBLyGQrVxGPgc9g305bvVhf6h', 'rFb7jwAb3UmSUN57Bjlsi4DTl2owLwRpwCc0SggRNEVb2Ebae2p5Umnq20rNMhmqN');

UPDATE qiita.oauth_software SET client_id = 'yKDgajoKn5xlOA8tpo48Rq8mWJkH9z4LBCx2SvqWYLIryaan2u' WHERE software_id = 1;
UPDATE qiita.oauth_software SET client_id = 'dHgaXDwq665ksFPqfIoD3Jt8KRXdSioTRa4lGa5mGDnz6JTIBf' WHERE software_id = 2;
UPDATE qiita.oauth_software SET client_id = '4MOBzUBHBtUmwhaC258H7PS0rBBLyGQrVxGPgc9g305bvVhf6h' WHERE software_id = 3;

-- Add a processing workflow
INSERT INTO qiita.processing_job_workflow (email, name)
    VALUES ('shared@foo.bar', 'Testing processing workflow'),
           ('test@foo.bar', 'Single node workflow');

INSERT INTO qiita.processing_job_workflow_root (processing_job_workflow_id, processing_job_id)
    VALUES ('1', 'b72369f9-a886-4193-8d3d-f7b504168e75'),
           ('2', 'ac653cb5-76a6-4a45-929e-eb9b2dee6b63');

INSERT INTO qiita.parent_processing_job (parent_id, child_id)
    VALUES ('b72369f9-a886-4193-8d3d-f7b504168e75', 'd19f76ee-274e-4c1b-b3a2-a12d73507c55');
