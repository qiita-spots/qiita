ALTER TABLE qiita.timeseries_type DROP CONSTRAINT idx_timeseries_type;

ALTER TABLE qiita.timeseries_type ADD intervention_type varchar DEFAULT 'None' NOT NULL;

ALTER TABLE qiita.timeseries_type ADD CONSTRAINT idx_timeseries_type UNIQUE ( timeseries_type, intervention_type ) ;

