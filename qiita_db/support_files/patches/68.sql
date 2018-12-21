-- December 21, 2018
-- Strip non-printable-ASCII characters from study_person.name
UPDATE study_person SET name = regexp_replace(name, '[^\x20-\x7E]+', '', 'g');

