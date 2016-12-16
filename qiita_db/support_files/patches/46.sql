-- Dec 3, 2016
-- Modify qiita.study_publication so studies can have string
-- dois and pubmed ids


-- dropping PRIMARY KEY ( study_id, publication_doi )
ALTER TABLE qiita.study_publication DROP CONSTRAINT idx_study_publication_0;

-- dropping FOREIGN KEY ( study_id ) REFERENCES qiita.study( study_id )
ALTER TABLE qiita.study_publication DROP CONSTRAINT fk_study_publication_study;

-- dropping FOREIGN KEY ( publication_doi ) REFERENCES qiita.publication( doi )
ALTER TABLE qiita.study_publication DROP CONSTRAINT fk_study_publication;

-- renaming publication_doi to publication
ALTER TABLE qiita.study_publication RENAME publication_doi TO publication;

-- adding a new column so we know if the publication is doi or pubmedid
ALTER TABLE qiita.study_publication ADD COLUMN is_doi boolean;
