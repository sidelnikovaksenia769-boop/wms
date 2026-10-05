-- =====================================================================
-- WMS: демонстрационные данные
-- =====================================================================
INSERT INTO units (code, name) VALUES
    ('шт','штука'),
    ('кг','килограмм'),
    ('л','литр');

INSERT INTO categories (name) VALUES
    ('Электроника'),
    ('Расходники'),
    ('Упаковка');

INSERT INTO warehouses (code, name, address) VALUES
    ('WH-01','Основной склад','г. Москва, ул. Складская, 1'),
    ('WH-02','Резервный склад','г. Москва, ул. Запасная, 5');

INSERT INTO locations (warehouse_id, code, zone, capacity) VALUES
    (1,'A-01-01','A',1000),
    (1,'A-01-02','A',1000),
    (1,'B-02-01','B',500),
    (2,'C-01-01','C',2000);

INSERT INTO users (username, password_hash, full_name, role) VALUES
    ('admin',   '$2b$12$demo', 'Администратор', 'admin'),
    ('manager', '$2b$12$demo', 'Менеджер Иванов', 'manager'),
    ('store1',  '$2b$12$demo', 'Кладовщик Петров', 'storekeeper');

INSERT INTO partners (kind, name, inn) VALUES
    ('supplier','ООО Поставщик-1','7701234567'),
    ('supplier','ООО Поставщик-2','7709876543'),
    ('customer','ООО Клиент-1','7711111111');

INSERT INTO products (sku, name, category_id, unit_id, min_qty, price) VALUES
    ('SKU-001','Кабель USB-C',     1, 1, 20, 350.00),
    ('SKU-002','Бумага А4',        2, 1, 100, 400.00),
    ('SKU-003','Коробка 30x20x10', 3, 1, 50, 45.00);

INSERT INTO barcodes (product_id, code, symbology, is_primary) VALUES
    (1,'4600000000017','EAN13',TRUE),
    (2,'4600000000024','EAN13',TRUE),
    (3,'4600000000031','EAN13',TRUE);

INSERT INTO batches (product_id, batch_number, supplier_id, produced_at) VALUES
    (1,'B-2025-001',1, DATE '2025-01-10'),
    (2,'B-2025-002',2, DATE '2025-01-15');

INSERT INTO stock (product_id, warehouse_id, location_id, batch_id, qty) VALUES
    (1, 1, 1, 1, 150),
    (2, 1, 2, 2,  80),
    (3, 1, 3, NULL, 500);
