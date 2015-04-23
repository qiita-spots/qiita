-- April 16, 2015
-- Add primary key to analysis_sample table, first deleting the duplicates
-- http://stackoverflow.com/a/9862688
DO $do$
BEGIN
    CREATE TEMP TABLE temp_table
    ON COMMIT drop AS
        SELECT analysis_id, processed_data_id, sample_id,
        ROW_NUMBER() OVER(PARTITION BY analysis_id, processed_data_id, sample_id ORDER BY (SELECT 0)) AS rn
        FROM qiita.analysis_sample;
    DELETE FROM qiita.analysis_sample;
    INSERT INTO qiita.analysis_sample (analysis_id, processed_data_id, sample_id) SELECT analysis_id, processed_data_id, sample_id FROM temp_table WHERE rn = 1;

    ALTER TABLE qiita.analysis_sample ADD CONSTRAINT pk_analysis_sample PRIMARY KEY ( analysis_id, processed_data_id, sample_id );
END $do$