-- November 15th, 2017
ALTER TABLE qiita.command_output ADD check_biom_merge bool DEFAULT 'False' NOT NULL;
ALTER TABLE qiita.command_parameter ADD name_order integer  ;
ALTER TABLE qiita.command_parameter ADD check_biom_merge bool DEFAULT 'False' NOT NULL;
