-- May 25, 2021
-- Adding max samples in a single preparation
-- we need to do it via a DO because IF NOT EXISTS in ALTER TABLE only exists
-- in PostgreSQL 9.6 or higher and we use 9.5
DO $do$
BEGIN
  IF NOT EXISTS (
       SELECT max_preparation_samples FROM settings
     ) THEN
     ALTER TABLE settings ADD COLUMN max_preparation_samples INT DEFAULT 800;
  END IF;
END $do$;
