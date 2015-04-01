-- March 19, 2015
-- Rename columns to be more descriptive and allow easier joins
ALTER TABLE qiita.processed_data_status RENAME COLUMN description TO processed_data_status_description;
ALTER TABLE qiita.portal_type RENAME COLUMN description TO portal_description;
ALTER TABLE qiita.investigation RENAME COLUMN description TO investigation_description;
ALTER TABLE qiita.investigation RENAME COLUMN name TO investigation_name;