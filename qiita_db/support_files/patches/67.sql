-- October 6, 2018
-- add post_processing_cmd column to record additional information required to merge some BIOMS.

ALTER TABLE qiita.software_command ADD post_processing_cmd varchar;

COMMENT ON COLUMN qiita.software_command.post_processing_cmd IS 'Store information on additional post-processing steps for merged BIOMs, if any.';
