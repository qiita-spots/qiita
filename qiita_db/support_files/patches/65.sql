-- Jul 5, 2018
-- add ignore_parent_command to software_comamnd

ALTER TABLE qiita.software_command ADD ignore_parent_command BOOL DEFAULT FALSE NOT NULL;
