-- Mar 7, 2016
-- Add reference_id and command_id of the input file to jobs

-- Changes to tables

ALTER TABLE qiita.job ADD input_file_reference_id bigint;

ALTER TABLE qiita.job ADD input_file_software_command_id bigint;

CREATE INDEX idx_job_0 ON qiita.job ( input_file_reference_id ) ;

CREATE INDEX idx_job_1 ON qiita.job ( input_file_software_command_id ) ;

ALTER TABLE qiita.job ADD CONSTRAINT fk_job_reference FOREIGN KEY ( input_file_reference_id ) REFERENCES qiita.reference( reference_id );

ALTER TABLE qiita.job ADD CONSTRAINT fk_job_software_command FOREIGN KEY ( input_file_software_command_id ) REFERENCES qiita.software_command( command_id );

-- Change values:
-- input_file_reference_id can be = 1 as it's only needed for job processing
-- input_file_software_command_id = 3 as it's close reference picking.

UPDATE qiita.job SET input_file_reference_id = 1;
ALTER TABLE qiita.job ALTER COLUMN input_file_reference_id SET NOT NULL;

UPDATE qiita.job SET input_file_software_command_id = 3;
ALTER TABLE qiita.job ALTER COLUMN input_file_software_command_id SET NOT NULL;
