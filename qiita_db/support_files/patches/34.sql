-- Dec 5, 2015
-- Adds table needed for oauth2 authentication

CREATE TABLE qiita.oauth_identifiers (
	client_id            varchar(50)  NOT NULL,
	client_secret        varchar(255),
	CONSTRAINT pk_oauth2 PRIMARY KEY ( client_id )
 );

 CREATE TABLE qiita.oauth_software (
	software_id          bigint  NOT NULL,
	client_id            varchar  NOT NULL,
	CONSTRAINT idx_oauth_software PRIMARY KEY ( software_id, client_id )
 ) ;
CREATE INDEX idx_oauth_software_software ON qiita.oauth_software ( software_id ) ;
CREATE INDEX idx_oauth_software_client ON qiita.oauth_software ( client_id ) ;
ALTER TABLE qiita.oauth_software ADD CONSTRAINT fk_oauth_software_software FOREIGN KEY ( software_id ) REFERENCES qiita.software( software_id )    ;
ALTER TABLE qiita.oauth_software ADD CONSTRAINT fk_oauth_software FOREIGN KEY ( client_id ) REFERENCES qiita.oauth_identifiers( client_id )    ;
