INSERT INTO qiita.allocation_equations(equation_name, expression)
        VALUES  ('mem_model1', 'k * np.log(x) + x * a + b'),
('mem_model2', 'k * np.log(x) + b * np.log(x)**2 + a'),
('mem_model3', 'k * np.log(x) + b * np.log(x)**2 + a * np.log(x)**3'),
('mem_model4', 'k * np.log(x) + b * np.log(x)**2 + a * np.log(x)**2.5'),
('time_model1', 'a + b + np.log(x) * k'),
('time_model2', 'a + b * x + np.log(x) * k'),
('time_model3', 'a + b * np.log(x)**2 + np.log(x) * k'),
('time_model4', 'a * np.log(x)**3 + b * np.log(x)**2 + np.log(x) * k');
