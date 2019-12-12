-- Nov 27, 2019
-- Adds download_link table for allowing jwt secured downloads of artifacts from shortened links
CREATE TABLE qiita.download_link (
  jti VARCHAR(32) PRIMARY KEY NOT NULL,
  jwt TEXT NOT NULL,
  exp TIMESTAMP NOT NULL
);

CREATE INDEX idx_download_link_exp ON qiita.download_link ( exp ) ;
