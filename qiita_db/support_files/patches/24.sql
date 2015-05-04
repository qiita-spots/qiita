ALTER TABLE qiita.reference ADD sortmerna_indexed_db_filepath bigint  ;

CREATE INDEX idx_reference_2 ON qiita.reference ( sortmerna_indexed_db_filepath ) ;

ALTER TABLE qiita.reference ADD CONSTRAINT fk_reference_filepath FOREIGN KEY ( sortmerna_indexed_db_filepath ) REFERENCES qiita.filepath( filepath_id )    ;

