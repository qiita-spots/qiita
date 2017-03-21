-- Mar 16, 2017
-- Changing tagging system structure, now study_tag will be the index

-- dropping all not required constrints, indexes and columns
ALTER TABLE qiita.study_tags DROP CONSTRAINT fk_study_tags;
DROP INDEX qiita.idx_study_tag_id;
ALTER TABLE qiita.study_tags DROP CONSTRAINT pk_study_tag;
ALTER TABLE qiita.study_tags DROP CONSTRAINT pk_study_tag_id;
ALTER TABLE qiita.study_tags DROP COLUMN study_tag_id;
ALTER TABLE qiita.per_study_tags ADD COLUMN study_tag varchar NOT NULL;
ALTER TABLE qiita.per_study_tags DROP CONSTRAINT pk_per_study_tags;
ALTER TABLE qiita.per_study_tags DROP COLUMN study_tag_id;

-- adding new restrictions
ALTER TABLE qiita.study_tags ADD CONSTRAINT pk_study_tags PRIMARY KEY ( study_tag );
ALTER TABLE qiita.study_tags ADD CONSTRAINT fk_email FOREIGN KEY ( email ) REFERENCES qiita.qiita_user( email );
ALTER TABLE qiita.per_study_tags ADD CONSTRAINT fk_study_tags FOREIGN KEY ( study_tag ) REFERENCES qiita.study_tags( study_tag );
ALTER TABLE qiita.per_study_tags ADD CONSTRAINT fk_study_id FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id );
ALTER TABLE qiita.per_study_tags ADD CONSTRAINT pk_per_study_tags PRIMARY KEY ( study_tag, study_id);

-- New structure:
-- CREATE TABLE qiita.study_tags (
--   email varchar NOT NULL,
--   study_tag varchar NOT NULL,
-- ) ;
--
-- CREATE TABLE qiita.per_study_tags (
--   study_tag varchar NOT NULL,
--   study_id bigint NOT NULL,
-- ) ;
