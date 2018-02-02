-- December 27th, 2017
-- Creating archive feature tables

CREATE TABLE qiita.archive_merging_scheme (
	archive_merging_scheme_id bigserial  NOT NULL,
	archive_merging_scheme varchar  NOT NULL,
	CONSTRAINT pk_merging_scheme PRIMARY KEY ( archive_merging_scheme_id )
 ) ;

CREATE TABLE qiita.archive_feature_value (
	archive_merging_scheme_id bigint  NOT NULL,
	archive_feature      varchar  NOT NULL,
	archive_feature_value varchar  NOT NULL,
	CONSTRAINT idx_archive_feature_value PRIMARY KEY ( archive_merging_scheme_id, archive_feature )
 ) ;

CREATE INDEX idx_archive_feature_value_0 ON qiita.archive_feature_value ( archive_merging_scheme_id ) ;

ALTER TABLE qiita.archive_feature_value ADD CONSTRAINT fk_archive_feature_value FOREIGN KEY ( archive_merging_scheme_id ) REFERENCES qiita.archive_merging_scheme( archive_merging_scheme_id );

-- taken from https://goo.gl/YtSvz2
CREATE OR REPLACE FUNCTION archive_upsert(amsi INT, af VARCHAR, afv VARCHAR) RETURNS VOID AS $$
BEGIN
    LOOP
        -- first try to update the key
        UPDATE qiita.archive_feature_value SET archive_feature_value = afv WHERE archive_merging_scheme_id = amsi AND archive_feature = af;
        IF found THEN
            RETURN;
        END IF;
        -- not there, so try to insert the key
        -- if someone else inserts the same key concurrently,
        -- we could get a unique-key failure
        BEGIN
            INSERT INTO qiita.archive_feature_value (archive_merging_scheme_id, archive_feature, archive_feature_value) VALUES (amsi, af, afv);
            RETURN;
        EXCEPTION WHEN unique_violation THEN
            -- Do nothing, and loop to try the UPDATE again.
        END;
    END LOOP;
END;
$$
LANGUAGE plpgsql;

-- January 25th, 2017
-- Adding to artifact_type is_user_uploadable
-- Note that at time of creation we will need to update the following qiita-spots: qtp-biom, qtp-visualization, qtp-diversity, qtp-target-gene & qtp-template-cookiecutter

ALTER TABLE qiita.artifact_type ADD is_user_uploadable BOOL DEFAULT FALSE;
UPDATE qiita.artifact_type SET is_user_uploadable=TRUE WHERE artifact_type IN ('FASTQ', 'BIOM', 'per_sample_FASTQ');
