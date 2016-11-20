-- Oct 29, 2016
-- Dropping command and reference NULL constraints from jobs so bioms
-- without them can be analyzed

ALTER TABLE qiita.job ALTER COLUMN input_file_reference_id DROP NOT NULL;
ALTER TABLE qiita.job ALTER COLUMN input_file_software_command_id DROP NOT NULL;
