# ER-диаграмма WMS

## Нотация
Crow's Foot (вороньи лапки). PK — первичный ключ, FK — внешний ключ.

## Связи
### Справочники
- categories (1) --< (N) products  [products.category_id]
- categories (1) --< (N) categories [categories.parent_id]
- units (1) --< (N) products [products.unit_id]
- warehouses (1) --< (N) locations [locations.warehouse_id]

### Товары и идентификация
- products (1) --< (N) barcodes [barcodes.product_id]
- products (1) --< (N) batches [batches.product_id]
- partners (1) --< (N) batches [batches.supplier_id]

### Документы
- documents (1) --< (N) document_items [document_items.document_id]
- documents (N) --> (1) partners [documents.partner_id]
- documents (N) --> (1) warehouses [warehouse_from/to]
- documents (N) --> (1) users [documents.user_id]

### Остатки и движения
- products (1) --< (N) stock [stock.product_id]
- warehouses (1) --< (N) stock [stock.warehouse_id]
- locations (1) --< (N) stock [stock.location_id]
- batches (1) --< (N) stock [stock.batch_id]
- documents (1) --< (N) stock_movements [stock_movements.document_id]

### Служебные
- users (1) --< (N) audit_log [audit_log.user_id]

## ASCII-схема
+--------------+       +----------------+       +--------------+
|  categories  |--1:N--|    products    |--1:N--|   barcodes   |
+------+-------+       +--------+-------+       +--------------+
       | self-ref               | 1:N
       v                        v
+--------------+         +--------------+
|  categories  |         |   batches    |
+--------------+         +------+-------+
                                |
+--------------+       +--------v-------+       +--------------+
|   partners   |--1:N--|   documents    |--1:N--|document_items|
+--------------+       +--------+-------+       +------+-------+
                                | 1:N                  | N:1
                                v                      v
                       +----------------+       +--------------+
                       | stock_movements|       |   products   |
                       +--------+-------+       +--------------+
                                |
+--------------+       +--------v-------+       +--------------+
|  warehouses  |--1:N--|   locations    |--1:N--|    stock     |
+--------------+       +----------------+       +------+-------+
                                                       | N:1
                                                       v
                                                +--------------+
                                                |   batches    |
                                                +--------------+

+--------------+       +----------------+
|    users     |--1:N--|   audit_log    |
+--------------+       +----------------+

## Кардинальности (сводка)
| Родитель | Дочерний | Тип | FK |
|----------|----------|-----|----|
| categories | products | 1:N | products.category_id |
| categories | categories | 1:N | categories.parent_id |
| units | products | 1:N | products.unit_id |
| warehouses | locations | 1:N | locations.warehouse_id |
| products | barcodes | 1:N | barcodes.product_id |
| products | batches | 1:N | batches.product_id |
| partners | batches | 1:N | batches.supplier_id |
| documents | document_items | 1:N | document_items.document_id |
| partners | documents | 1:N | documents.partner_id |
| products | stock | 1:N | stock.product_id |
| warehouses | stock | 1:N | stock.warehouse_id |
| locations | stock | 1:N | stock.location_id |
| batches | stock | 1:N | stock.batch_id |
| documents | stock_movements | 1:N | stock_movements.document_id |
| users | audit_log | 1:N | audit_log.user_id |

## Как построить визуальную ER
1. Открыть dbdiagram.io или draw.io
2. Вставить SQL из db/01-init.sql — сервис сам нарисует ER
3. Экспортировать PNG -> docs/er-diagram.png
