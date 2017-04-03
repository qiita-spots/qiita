-- Apr 3, 2017
-- Linking qiita users to the oauth table
ALTER TABLE qiita.qiita_user ADD client_id varchar  ;

ALTER TABLE qiita.qiita_user ADD CONSTRAINT uc_qiita_user_client_id UNIQUE ( client_id ) ;

ALTER TABLE qiita.qiita_user ADD CONSTRAINT fk_qiita_user_client_id FOREIGN KEY ( client_id ) REFERENCES qiita.oauth_identifiers( client_id )    ;
