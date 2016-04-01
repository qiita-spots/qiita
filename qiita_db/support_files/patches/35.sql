-- Dec 5, 2015
-- Adds names to the artifacts

ALTER TABLE qiita.artifact ADD name varchar(35)  NOT NULL DEFAULT 'noname';
