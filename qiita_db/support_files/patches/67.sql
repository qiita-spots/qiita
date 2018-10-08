-- October 6, 2018
-- add addtl_processing_cmd column to record additional information required to merge some BIOMS.

ALTER TABLE qiita.software_command ADD addtl_processing_cmd varchar;

COMMENT ON COLUMN qiita.software_command.addtl_processing_cmd IS 'Store information on additional processes to merge BIOMs, if any.';
