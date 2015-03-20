-- March 18, 2015
-- Add column to analysis table to mark shopping cart
ALTER TABLE qiita.analysis ADD dflt bool NOT NULL DEFAULT false;