-- Nov 27, 2019
-- Adds download_link table for allowing jwt secured downloads of artifacts from shortened links
ALTER TABLE qiita.prep_template ADD deprecated BOOL DEFAULT FALSE;

ALTER TABLE qiita.study ADD notes TEXT NOT NULL DEFAULT '';
