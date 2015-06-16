-- June 11,, 2015
-- Adds portal type to analyses

-- Temporarily have default value for non-portaled analyses
ALTER TABLE qiita.analysis
ADD portal_type_id bigint NOT NULL DEFAULT 1;

-- Add FK to portal_type_id
ALTER TABLE qiita.analysis
ADD CONSTRAINT fk_analysis_portal
FOREIGN KEY (portal_type_id)
REFERENCES qiita.portal_type(portal_type_id);

-- Drop defaut value constraint so it is now required to give portal type
ALTER TABLE qiita.analysis
ALTER portal_type_id DROP DEFAULT;

-- Remove existing portals and replace with more relevant ones
UPDATE qiita.study SET portal_type_id = 1 WHERE portal_type_id = 3;

DELETE FROM qiita.portal_type WHERE portal = 'QIIME_EMP';

UPDATE qiita.portal_type
SET portal = 'QIITA', portal_description = 'QIITA portal. Access to all data stored in database.'
WHERE portal_type_id = 1;

-- Remove study portal info to it's own table, as one study can be in multiple portals
CREATE TABLE qiita.study_portal (
	study_id             bigint  NOT NULL,
	portal_type_id       bigint  NOT NULL,
	CONSTRAINT pk_study_portal PRIMARY KEY ( study_id, portal_type_id )
 );

CREATE INDEX idx_study_portal ON qiita.study_portal ( study_id );

CREATE INDEX idx_study_portal_0 ON qiita.study_portal ( portal_type_id );

COMMENT ON TABLE qiita.study_portal IS 'Controls what studies are visible on what portals';

ALTER TABLE qiita.study_portal ADD CONSTRAINT fk_study_portal FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id );

ALTER TABLE qiita.study_portal ADD CONSTRAINT fk_study_portal_0 FOREIGN KEY ( portal_type_id ) REFERENCES qiita.portal_type( portal_type_id );

INSERT INTO qiita.study_portal (study_id, portal_type_id) SELECT s.study_id, s.portal_type_id FROM qiita.study s;

ALTER TABLE qiita.study DROP COLUMN portal_type_id;