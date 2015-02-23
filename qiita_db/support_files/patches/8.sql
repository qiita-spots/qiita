-- Dec 12, 2014
-- Adding the VAMPS status field in all preprocessed data

ALTER TABLE qiita.preprocessed_data ADD submitted_to_vamps_status varchar DEFAULT 'not submitted' ;
