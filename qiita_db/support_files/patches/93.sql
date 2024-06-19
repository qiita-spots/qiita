-- Jun 19, 2024
-- Adding a new column to the user table that logs when this account was created
-- Usefull e.g. to prune non-verified=inactive user or to plot user growth

ALTER TABLE qiita.qiita_user
  ADD creation_timestamp timestamp without time zone DEFAULT NOW();

COMMENT ON COLUMN qiita.qiita_user.creation_timestamp IS 'The date the user account was created';
