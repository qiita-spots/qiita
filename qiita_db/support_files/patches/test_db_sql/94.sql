INSERT INTO qiita.allocation_equations(equation_name, expression)
        VALUES 
        ('mem_model1', '(k * (log(x))) + (x * a) + b'),
('mem_model2', '(k * (log(x))) + (b * ((log(x))**2)) + a'),
('mem_model3', '(k * (log(x))) + (b * ((log(x))**2)) + (a * ((log(x))**3))'),
('mem_model4', '(k * (log(x))) + (b * ((log(x))**2)) + (a * ((log(x))**2.5))'),
('time_model1', 'a + b + ((log(x)) * k)'),
('time_model2', 'a + (b * x) + ((log(x)) * k)'),
('time_model3', 'a + (b * ((log(x))**2)) + ((log(x)) * k)'),
('time_model4', '(a * ((log(x))**3)) + (b * ((log(x))**2)) + ((log(x)) * k)');
