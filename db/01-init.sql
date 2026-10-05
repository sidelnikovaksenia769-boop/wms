-- =====================================================================
-- WMS: Система управления складом
-- Этап 1. Инициализация схемы БД (PostgreSQL 15+)
-- =====================================================================
DROP DATABASE IF EXISTS wms_db;
CREATE DATABASE wms_db ENCODING 'UTF8';
\c wms_db

-- 1. Справочники
CREATE TABLE categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(150) NOT NULL UNIQUE,
    parent_id   INT REFERENCES categories(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE units (
    id    SERIAL PRIMARY KEY,
    code  VARCHAR(10) NOT NULL UNIQUE,
    name  VARCHAR(50) NOT NULL
);

CREATE TABLE products (
    id           SERIAL PRIMARY KEY,
    sku          VARCHAR(50) NOT NULL UNIQUE,
    name         VARCHAR(255) NOT NULL,
    category_id  INT REFERENCES categories(id) ON DELETE SET NULL,
    unit_id      INT REFERENCES units(id) ON DELETE RESTRICT,
    min_qty      NUMERIC(14,3) NOT NULL DEFAULT 0 CHECK (min_qty >= 0),
    price        NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (price >= 0),
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_name     ON products(name);

CREATE TABLE warehouses (
    id        SERIAL PRIMARY KEY,
    code      VARCHAR(20) NOT NULL UNIQUE,
    name      VARCHAR(150) NOT NULL,
    address   TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE locations (
    id           SERIAL PRIMARY KEY,
    warehouse_id INT NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    code         VARCHAR(30) NOT NULL,
    zone         VARCHAR(30),
    capacity     NUMERIC(14,3),
    UNIQUE (warehouse_id, code)
);
CREATE INDEX idx_locations_wh ON locations(warehouse_id);

-- 2. Контрагенты
CREATE TABLE partners (
    id         SERIAL PRIMARY KEY,
    kind       VARCHAR(10) NOT NULL CHECK (kind IN ('supplier','customer')),
    name       VARCHAR(255) NOT NULL,
    inn        VARCHAR(20),
    phone      VARCHAR(30),
    email      VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_partners_kind ON partners(kind);

-- 3. Пользователи
CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(150),
    role          VARCHAR(20) NOT NULL DEFAULT 'storekeeper'
                  CHECK (role IN ('admin','manager','storekeeper','analyst')),
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 4. Штрих-коды и партии
CREATE TABLE barcodes (
    id         SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    code       VARCHAR(64) NOT NULL UNIQUE,
    symbology  VARCHAR(20) NOT NULL DEFAULT 'EAN13'
               CHECK (symbology IN ('EAN13','CODE128')),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_barcodes_product ON barcodes(product_id);

CREATE TABLE batches (
    id           SERIAL PRIMARY KEY,
    product_id   INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    batch_number VARCHAR(50) NOT NULL,
    supplier_id  INT REFERENCES partners(id) ON DELETE SET NULL,
    produced_at  DATE,
    expires_at   DATE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (product_id, batch_number)
);

-- 5. Документы
CREATE TABLE documents (
    id             BIGSERIAL PRIMARY KEY,
    doc_type       VARCHAR(20) NOT NULL
                   CHECK (doc_type IN ('receipt','transfer','writeoff','inventory','shipment')),
    doc_number     VARCHAR(50) NOT NULL UNIQUE,
    status         VARCHAR(20) NOT NULL DEFAULT 'draft'
                   CHECK (status IN ('draft','posted','cancelled')),
    warehouse_from INT REFERENCES warehouses(id),
    warehouse_to   INT REFERENCES warehouses(id),
    partner_id     INT REFERENCES partners(id),
    user_id        INT REFERENCES users(id) ON DELETE SET NULL,
    comment        TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    posted_at      TIMESTAMPTZ
);
CREATE INDEX idx_documents_type_date ON documents(doc_type, created_at);
CREATE INDEX idx_documents_status    ON documents(status);

CREATE TABLE document_items (
    id            BIGSERIAL PRIMARY KEY,
    document_id   BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    product_id    INT NOT NULL REFERENCES products(id),
    batch_id      INT REFERENCES batches(id),
    location_from INT REFERENCES locations(id),
    location_to   INT REFERENCES locations(id),
    qty           NUMERIC(14,3) NOT NULL CHECK (qty > 0),
    price         NUMERIC(14,2) NOT NULL DEFAULT 0,
    qty_fact      NUMERIC(14,3)
);
CREATE INDEX idx_docitems_doc     ON document_items(document_id);
CREATE INDEX idx_docitems_product ON document_items(product_id);

-- 6. Остатки и движения
CREATE TABLE stock (
    id           BIGSERIAL PRIMARY KEY,
    product_id   INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    warehouse_id INT NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    location_id  INT REFERENCES locations(id) ON DELETE SET NULL,
    batch_id     INT REFERENCES batches(id) ON DELETE SET NULL,
    qty          NUMERIC(14,3) NOT NULL DEFAULT 0 CHECK (qty >= 0),
    reserved     NUMERIC(14,3) NOT NULL DEFAULT 0 CHECK (reserved >= 0),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (product_id, warehouse_id, location_id, batch_id)
);
CREATE INDEX idx_stock_product   ON stock(product_id);
CREATE INDEX idx_stock_warehouse ON stock(warehouse_id);

CREATE TABLE stock_movements (
    id            BIGSERIAL PRIMARY KEY,
    product_id    INT NOT NULL REFERENCES products(id),
    batch_id      INT REFERENCES batches(id),
    warehouse_id  INT NOT NULL REFERENCES warehouses(id),
    location_id   INT REFERENCES locations(id),
    document_id   BIGINT REFERENCES documents(id) ON DELETE SET NULL,
    movement_type VARCHAR(20) NOT NULL
                  CHECK (movement_type IN ('in','out','move','adjust')),
    qty           NUMERIC(14,3) NOT NULL,
    user_id       INT REFERENCES users(id) ON DELETE SET NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_mov_product_date ON stock_movements(product_id, created_at DESC);
CREATE INDEX idx_mov_doc          ON stock_movements(document_id);

-- 7. Аудит
CREATE TABLE audit_log (
    id         BIGSERIAL PRIMARY KEY,
    user_id    INT REFERENCES users(id) ON DELETE SET NULL,
    action     VARCHAR(50) NOT NULL,
    entity     VARCHAR(50) NOT NULL,
    entity_id  BIGINT,
    payload    JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_entity ON audit_log(entity, entity_id);

-- 8. Представления
CREATE OR REPLACE VIEW v_low_stock AS
SELECT p.id AS product_id, p.sku, p.name, p.min_qty,
       COALESCE(SUM(s.qty), 0) AS total_qty,
       (p.min_qty - COALESCE(SUM(s.qty), 0)) AS deficit
FROM products p
LEFT JOIN stock s ON s.product_id = p.id
WHERE p.is_active
GROUP BY p.id, p.sku, p.name, p.min_qty
HAVING COALESCE(SUM(s.qty), 0) <= p.min_qty;

CREATE OR REPLACE VIEW v_turnover AS
SELECT p.id AS product_id, p.sku, p.name,
       COALESCE(SUM(CASE WHEN m.qty < 0 THEN -m.qty END), 0) / 30.0 AS avg_out_per_day,
       COALESCE(SUM(s.qty), 0) AS current_stock
FROM products p
LEFT JOIN stock_movements m ON m.product_id = p.id
     AND m.created_at >= now() - INTERVAL '30 days'
LEFT JOIN stock s ON s.product_id = p.id
GROUP BY p.id, p.sku, p.name;

-- 9. Триггеры
CREATE OR REPLACE FUNCTION trg_set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER products_updated
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

CREATE TRIGGER stock_updated
    BEFORE UPDATE ON stock
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();
