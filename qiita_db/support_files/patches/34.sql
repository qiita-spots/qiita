-- Dec 5, 2015
-- Adds table needed for oauth2 authentication

CREATE TABLE qiita.oauth_identifiers ( 
	client_id            varchar(50)  NOT NULL,
	client_secret        varchar  NOT NULL,
	CONSTRAINT pk_oauth2 PRIMARY KEY ( client_id )
 );
