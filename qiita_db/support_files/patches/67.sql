alter table qiita.software_command add addtl_processing_cmd varchar;
comment on column qiita.software_command.addtl_processing_cmd is 'Store information on additional processes to merge BIOMs, if any.';
