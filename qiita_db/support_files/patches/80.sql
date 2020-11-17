-- Nov 10, 2020
-- Add a flag to the studies to see if the study was submitted by Qiita or downloaded by EBI

ALTER TABLE qiita.study ADD autoloaded BOOL NOT NULL DEFAULT false;
