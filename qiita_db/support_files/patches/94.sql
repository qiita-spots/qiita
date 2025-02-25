-- Jan 13, 2025
-- Adding a table for formulas for resource allocations
CREATE TABLE qiita.allocation_equations (
  equation_id     SERIAL PRIMARY KEY,
  equation_name   TEXT NOT NULL,
  expression      TEXT NOT NULL
 );