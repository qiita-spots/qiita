-- Aug 28st, 2019
-- fix #2933
CREATE TABLE qiita.stats_daily (
  stats JSONB NOT NULL,
  stats_timestamp TIMESTAMP NOT NULL
);
