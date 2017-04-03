-- Apr 3, 2017
-- Linking qiita users to the oauth table
ALTER TABLE qiita_user ADD client_id varchar  ;

CREATE INDEX idx_qiita_user ON qiita_user ( client_id ) ;

ALTER TABLE qiita_user ADD CONSTRAINT fk_qiita_user_client_id FOREIGN KEY ( client_id ) REFERENCES oauth_identifiers( client_id )    ;

