-- Feb 3, 2017
-- adding study tagging system

CREATE TABLE qiita.study_tags (
  study_tag_id bigserial NOT NULL,
  email varchar NOT NULL,
	study_tag varchar NOT NULL,
  CONSTRAINT pk_study_tag UNIQUE ( study_tag_id ),
  CONSTRAINT pk_study_tag_id PRIMARY KEY ( study_tag_id )
) ;

CREATE INDEX idx_study_tag_id ON qiita.study_tags ( study_tag_id ) ;
ALTER TABLE qiita.study_tags ADD CONSTRAINT fk_study_tags FOREIGN KEY ( email ) REFERENCES qiita.qiita_user( email );

CREATE TABLE qiita.per_study_tags (
  study_tag_id bigint NOT NULL,
  study_id bigint NOT NULL,
  CONSTRAINT pk_per_study_tags PRIMARY KEY ( study_tag_id, study_id )
) ;

ALTER TABLE qiita.per_study_tags ADD CONSTRAINT fk_per_study_tags_study_tag_id FOREIGN KEY ( study_tag_id ) REFERENCES qiita.study_tags( study_tag_id );
ALTER TABLE qiita.per_study_tags ADD CONSTRAINT fk_per_study_tags_study_id FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id );
