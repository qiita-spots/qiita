-- Sep 21, 2016
-- Adding active column to the software and software command table to be able
-- to disallow plugins and/or individual software commands

ALTER TABLE qiita.software ADD active bool DEFAULT 'True' NOT NULL;

ALTER TABLE qiita.software_command ADD active bool DEFAULT 'True' NOT NULL;
