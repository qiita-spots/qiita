-- Nov 18, 2014
-- This patch updates the timeseries structures on the DB

-- We need to drop the unique constraint on timeseries_type
ALTER TABLE qiita.timeseries_type DROP CONSTRAINT idx_timeseries_type;

-- We add a new column, intervention type, and we set the default to None because the column is not nullable
-- and since the database already contains some data, if we don't set a default, it fails on creation
ALTER TABLE qiita.timeseries_type ADD intervention_type varchar DEFAULT 'None' NOT NULL;

-- Now the unique constraint applies to the tuple (timeseries_type, intervention_type)
ALTER TABLE qiita.timeseries_type ADD CONSTRAINT idx_timeseries_type UNIQUE ( timeseries_type, intervention_type ) ;

-- We need to update the current entries on the table
UPDATE qiita.timeseries_type SET timeseries_type='None',intervention_type='None' WHERE timeseries_type_id = 1;
UPDATE qiita.timeseries_type SET timeseries_type='real',intervention_type='single intervention' WHERE timeseries_type_id = 2;
UPDATE qiita.timeseries_type SET timeseries_type='real',intervention_type='multiple intervention' WHERE timeseries_type_id = 3;
UPDATE qiita.timeseries_type SET timeseries_type='real',intervention_type='combo intervention' WHERE timeseries_type_id = 4;

-- Insert the rest of possible timeseries combinations
INSERT INTO qiita.timeseries_type (timeseries_type, intervention_type) VALUES
	('pseudo','single intervention'),
	('pseudo','multiple intervention'),
	('pseudo','combo intervention'),
	('mixed','single intervention'),
	('mixed','multiple intervention'),
	('mixed','combo intervention');
