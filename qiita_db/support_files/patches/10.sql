--  Dec 17, 2014
--  This patch renames the columns of the processed_params_sortmerna to match
--  the parameter names in the script

ALTER TABLE qiita.processed_params_sortmerna RENAME COLUMN evalue TO sortmerna_e_value;

ALTER TABLE qiita.processed_params_sortmerna RENAME COLUMN max_pos TO sortmerna_max_pos;

ALTER TABLE qiita.processed_params_sortmerna RENAME COLUMN coverage TO sortmerna_coverage;
