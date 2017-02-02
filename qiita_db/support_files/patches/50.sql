-- Feb 1, 2017
-- adding study tag system


CREATE TABLE qiita.study_tags (
  study_tag_id bigserial NOT NULL,
	study_tag varchar NOT NULL,
  CONSTRAINT pk_study_tag UNIQUE ( study_tag_id ),
  CONSTRAINT pk_study_tag_id PRIMARY KEY ( study_tag_id )
) ;

CREATE INDEX idx_study_tag_id ON qiita.study_tags ( study_tag_id ) ;

-- inserting tags for GOLD
INSERT INTO qiita.study_tags (study_tag) VALUES ('GOLD');
