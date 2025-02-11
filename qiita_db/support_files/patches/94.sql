-- Jan 13, 2025
-- Adding a table for formulas for resource allocations
CREATE TABLE qiita.resource_allocation_equations (
  equation_id            SERIAL PRIMARY KEY,
  equation_name          TEXT NOT NULL,
  expression             TEXT NOT NULL
 );

INSERT INTO qiita.resource_allocation_equations(equation_name, expression) VALUES 
        ('mem_model1', '(k * (np.log(x))) + (x * a) + b'),
        ('mem_model2', '(k * (np.log(x))) + (b * ((np.log(x))**2)) + a'),
        ('mem_model3', '(k * (np.log(x))) + (b * ((np.log(x))**2)) + (a * ((np.np.log(x))**3))'),
        ('mem_model4', '(k * (np.log(x))) + (b * ((np.log(x))**2)) + (a * ((np.log(x))**2.5))'),
        ('time_model1', 'a + b + ((np.log(x)) * k)'),
        ('time_model2', 'a + (b * x) + ((np.log(x)) * k)'),
        ('time_model3', 'a + (b * ((np.log(x))**2)) + ((np.log(x)) * k)'),
        ('time_model4', '(a * ((np.log(x))**3)) + (b * ((np.log(x))**2)) + ((np.log(x)) * k)');

CREATE TABLE qiita.resource_allocation_column_names (
  col_name_id   SERIAL PRIMARY KEY,
  col_name      TEXT NOT NULL
 );

INSERT INTO qiita.resource_allocation_column_names(col_name) VALUES
      ('samples'), ('columns'), ('input_size'),
      ('samples*columns'), ('samples*input_size'),
      ('columns*input_size'), ('samples*columns*input_size');