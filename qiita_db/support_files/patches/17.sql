/*
10 March 2015

This patch removes the 100 character limit on the study_sample_columns's
column_name column. To my knowledge, there is no reason for this limit.
- Adam Robbins-Pianka
*/
alter table qiita.study_sample_columns alter column column_name type varchar;
