-- Jan 13, 2025
-- Adding a table for formulas for resource allocations

CREATE TABLE qiita.resource_allocation_column_names (
  col_name_id   SERIAL PRIMARY KEY,
  col_name      TEXT NOT NULL
 );

INSERT INTO qiita.resource_allocation_column_names(col_name) VALUES
      ('samples'), ('columns');
