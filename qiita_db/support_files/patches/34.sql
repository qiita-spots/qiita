-- Dec 5, 2015
-- Adds table needed for oauth2 authentication

CREATE TABLE qiita.oauth_identifiers ( 
	client_id            varchar(50)  NOT NULL,
	client_secret        varchar,
	CONSTRAINT pk_oauth2 PRIMARY KEY ( client_id )
 );

INSERT INTO qiita.oauth_identifiers (client_id) VALUES ('DWelYzEYJYcZ4wlqUp0bHGXojrvZVz0CNBJvOqUKcrPQ5p4UqE');
INSERT INTO qiita.oauth_identifiers (client_id, client_secret) VALUES ('19ndkO3oMKsoChjVVWluF7QkxHRfYhTKSFbAVt8IhK7gZgDaO4', 'J7FfQ7CQdOxuKhQAf1eoGgBAE81Ns8Gu3EKaWFm3IO2JKhAmmCWZuabe0O5Mp28s1');