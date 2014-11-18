INSERT INTO qiita.study_status (status, description) VALUES ('sandbox', 'Only available to the owner. No sharing');

UPDATE qiita.study SET study_status_id = 4 WHERE study_status_id = 1;
