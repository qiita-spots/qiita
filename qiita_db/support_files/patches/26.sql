-- June 11,, 2015
-- Adds portal type to analyses

-- Temporarily have default value for non-portaled analyses
ALTER TABLE qiita.analysis
ADD portal_type_id bigint NOT NULL DEFAULT 3;

-- Add FK to portal_type_id
ALTER TABLE qiita.analysis
ADD CONSTRAINT fk_analysis_portal
FOREIGN KEY (portal_type_id)
REFERENCES qiita.portal_type(portal_type_id);

-- Drop defaut value constraint so it is now required to give portal type
ALTER TABLE qiita.analysis
ALTER portal_type_id DROP DEFAULT;