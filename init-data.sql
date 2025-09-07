-- Создание таблицы с тестовыми данными для анализа
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    date DATE,
    product VARCHAR(100),
    category VARCHAR(50),
    quantity INTEGER,
    price DECIMAL(10,2),
    revenue DECIMAL(10,2)
);

-- Вставка тестовых данных
INSERT INTO sales (date, product, category, quantity, price, revenue) VALUES
('2024-01-01', 'Laptop', 'Electronics', 5, 1200.00, 6000.00),
('2024-01-02', 'Mouse', 'Electronics', 20, 25.00, 500.00),
('2024-01-03', 'Keyboard', 'Electronics', 15, 75.00, 1125.00),
('2024-01-04', 'Monitor', 'Electronics', 8, 300.00, 2400.00),
('2024-01-05', 'Desk', 'Furniture', 3, 400.00, 1200.00),
('2024-01-06', 'Chair', 'Furniture', 12, 150.00, 1800.00),
('2024-01-07', 'Book', 'Education', 50, 20.00, 1000.00),
('2024-01-08', 'Pen', 'Office', 100, 2.00, 200.00),
('2024-01-09', 'Notebook', 'Office', 30, 5.00, 150.00),
('2024-01-10', 'Phone', 'Electronics', 7, 800.00, 5600.00);

-- Создание представления для агрегированных данных
CREATE VIEW sales_by_category AS
SELECT 
    category,
    COUNT(*) as total_orders,
    SUM(quantity) as total_quantity,
    SUM(revenue) as total_revenue,
    AVG(price) as avg_price
FROM sales
GROUP BY category;