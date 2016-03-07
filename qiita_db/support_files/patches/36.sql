-- Jan 25, 2016
-- Move the can_be_submitted_to_XX columns to the artifact type

ALTER TABLE qiita.artifact DROP COLUMN can_be_submitted_to_ebi;
ALTER TABLE qiita.artifact DROP COLUMN can_be_submitted_to_vamps;
ALTER TABLE qiita.artifact_type ADD can_be_submitted_to_ebi bool DEFAULT 'FALSE' NOT NULL;
ALTER TABLE qiita.artifact_type ADD can_be_submitted_to_vamps bool DEFAULT 'FALSE' NOT NULL;

UPDATE qiita.artifact_type SET can_be_submitted_to_ebi = TRUE, can_be_submitted_to_vamps = TRUE
    WHERE artifact_type = 'Demultiplexed';
