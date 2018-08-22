-- August 22, 2018
-- add specimen_id_column to study table (needed to plate samples in labman)

ALTER TABLE study ADD specimen_id_column varchar(256);

COMMENT ON COLUMN study.specimen_id_column IS 'The name of the column that describes the specimen identifiers (such as what is written on the tubes).';

