-- Feb 27th, 2019
-- adding fp_size to filepaths to store the filepath size

ALTER TABLE qiita.filepath ADD fp_size BIGINT NOT NULL DEFAULT 0;
