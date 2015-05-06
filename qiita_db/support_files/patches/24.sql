ALTER TABLE qiita.reference ADD sortmerna_indexed_db_filepath bigint  ;

ALTER TABLE qiita.reference ADD CONSTRAINT fk_reference_filepath FOREIGN KEY ( sortmerna_indexed_db_filepath ) REFERENCES qiita.filepath( filepath_id )    ;

