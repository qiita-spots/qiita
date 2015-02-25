--Feb 25, 2015
--Adds tables for analysis collection object
CREATE TABLE qiita.collection_status ( 
	collection_status_id bigserial  NOT NULL,
	status               varchar(100)  NOT NULL,
	CONSTRAINT pk_collection_status PRIMARY KEY ( collection_status_id )
 ) ;

CREATE TABLE qiita.collection ( 
	collection_id        bigserial  NOT NULL,
	email                varchar  NOT NULL,
	name                 varchar(100)  NOT NULL,
	description          varchar  ,
	collection_status_id bigint DEFAULT 1 NOT NULL,
	CONSTRAINT pk_collection PRIMARY KEY ( collection_id )
 ) ;

CREATE INDEX idx_collection ON qiita.collection ( email ) ;

CREATE INDEX idx_collection_0 ON qiita.collection ( collection_status_id ) ;

COMMENT ON TABLE qiita.collection IS 'Tracks a group of analyses and important jobs for an overarching goal.';

CREATE TABLE qiita.collection_analysis ( 
	collection_id        bigint  NOT NULL,
	analysis_id          bigint  NOT NULL,
	CONSTRAINT idx_collection_analysis PRIMARY KEY ( collection_id, analysis_id )
 ) ;

CREATE INDEX idx_collection_analysis_0 ON qiita.collection_analysis ( collection_id ) ;

CREATE INDEX idx_collection_analysis_1 ON qiita.collection_analysis ( analysis_id ) ;

COMMENT ON TABLE qiita.collection_analysis IS 'Matches collection to analyses as one to many.';

CREATE TABLE qiita.collection_job ( 
	collection_id        bigint  NOT NULL,
	job_id               bigint  NOT NULL,
	CONSTRAINT idx_collection_job_1 PRIMARY KEY ( collection_id, job_id )
 ) ;

CREATE INDEX idx_collection_job ON qiita.collection_job ( collection_id ) ;

CREATE INDEX idx_collection_job_0 ON qiita.collection_job ( job_id ) ;

COMMENT ON TABLE qiita.collection_job IS 'Matches collection important jobs as one to many.';

CREATE TABLE qiita.collection_users ( 
	collection_id        bigint  NOT NULL,
	email                varchar  NOT NULL,
	CONSTRAINT idx_collection_user PRIMARY KEY ( collection_id, email )
 ) ;

CREATE INDEX idx_collection_user_0 ON qiita.collection_users ( collection_id ) ;

CREATE INDEX idx_collection_user_1 ON qiita.collection_users ( email ) ;

COMMENT ON TABLE qiita.collection_users IS 'Allows sharing of a collection';

ALTER TABLE qiita.collection ADD CONSTRAINT fk_collection FOREIGN KEY ( email ) REFERENCES qiita.qiita_user( email )    ;

ALTER TABLE qiita.collection ADD CONSTRAINT fk_collection_0 FOREIGN KEY ( collection_status_id ) REFERENCES qiita.collection_status( collection_status_id )    ;

ALTER TABLE qiita.collection_analysis ADD CONSTRAINT fk_collection_analysis FOREIGN KEY ( collection_id ) REFERENCES qiita.collection( collection_id )    ;

ALTER TABLE qiita.collection_analysis ADD CONSTRAINT fk_collection_analysis_0 FOREIGN KEY ( analysis_id ) REFERENCES qiita.analysis( analysis_id )    ;

ALTER TABLE qiita.collection_job ADD CONSTRAINT fk_collection_job FOREIGN KEY ( collection_id ) REFERENCES qiita.collection( collection_id )    ;

ALTER TABLE qiita.collection_job ADD CONSTRAINT fk_collection_job_0 FOREIGN KEY ( job_id ) REFERENCES qiita.job( job_id )    ;

ALTER TABLE qiita.collection_users ADD CONSTRAINT fk_collection_user FOREIGN KEY ( collection_id ) REFERENCES qiita.collection( collection_id )    ;

ALTER TABLE qiita.collection_users ADD CONSTRAINT fk_collection_user_email FOREIGN KEY ( email ) REFERENCES qiita.qiita_user( email )    ;

--Insert collection statuses
INSERT INTO qiita.collection_status (status) VALUES ('private'), ('public');
