-- ============================================================
-- Retail Chain Sales Dashboard - Database Schema
-- ============================================================

-- Drop tables in reverse dependency order (for re-runs)
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS stores CASCADE;
DROP TABLE IF EXISTS regions CASCADE;
DROP TABLE IF EXISTS categories CASCADE;

-- ------------------------------------------------------------
-- Regions
-- ------------------------------------------------------------
CREATE TABLE regions (
    region_id   SERIAL PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL,
    country     VARCHAR(100) NOT NULL DEFAULT 'India'
);

-- ------------------------------------------------------------
-- Stores
-- ------------------------------------------------------------
CREATE TABLE stores (
    store_id    SERIAL PRIMARY KEY,
    store_name  VARCHAR(150) NOT NULL,
    city        VARCHAR(100) NOT NULL,
    region_id   INT NOT NULL REFERENCES regions(region_id),
    opened_date DATE NOT NULL,
    store_size  VARCHAR(20) CHECK (store_size IN ('Small', 'Medium', 'Large'))
);

-- ------------------------------------------------------------
-- Product Categories
-- ------------------------------------------------------------
CREATE TABLE categories (
    category_id   SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    department    VARCHAR(100) NOT NULL
);

-- ------------------------------------------------------------
-- Products (SKUs)
-- ------------------------------------------------------------
CREATE TABLE products (
    product_id    SERIAL PRIMARY KEY,
    sku           VARCHAR(50) UNIQUE NOT NULL,
    product_name  VARCHAR(200) NOT NULL,
    category_id   INT NOT NULL REFERENCES categories(category_id),
    unit_price    NUMERIC(10, 2) NOT NULL,
    cost_price    NUMERIC(10, 2) NOT NULL
);

-- ------------------------------------------------------------
-- Customers
-- ------------------------------------------------------------
CREATE TABLE customers (
    customer_id     SERIAL PRIMARY KEY,
    full_name       VARCHAR(200) NOT NULL,
    email           VARCHAR(200) UNIQUE NOT NULL,
    phone           VARCHAR(20),
    city            VARCHAR(100),
    region_id       INT REFERENCES regions(region_id),
    signup_date     DATE NOT NULL,
    customer_segment VARCHAR(20) CHECK (customer_segment IN ('Bronze', 'Silver', 'Gold', 'Platinum'))
);

-- ------------------------------------------------------------
-- Orders
-- ------------------------------------------------------------
CREATE TABLE orders (
    order_id        SERIAL PRIMARY KEY,
    customer_id     INT NOT NULL REFERENCES customers(customer_id),
    store_id        INT NOT NULL REFERENCES stores(store_id),
    order_date      DATE NOT NULL,
    order_status    VARCHAR(20) CHECK (order_status IN ('Completed', 'Returned', 'Cancelled')),
    payment_method  VARCHAR(30)
);

-- ------------------------------------------------------------
-- Order Items (line items)
-- ------------------------------------------------------------
CREATE TABLE order_items (
    item_id       SERIAL PRIMARY KEY,
    order_id      INT NOT NULL REFERENCES orders(order_id),
    product_id    INT NOT NULL REFERENCES products(product_id),
    quantity      INT NOT NULL CHECK (quantity > 0),
    unit_price    NUMERIC(10, 2) NOT NULL,
    discount_pct  NUMERIC(5, 2) DEFAULT 0,
    line_total    NUMERIC(10, 2) GENERATED ALWAYS AS
                    (quantity * unit_price * (1 - discount_pct / 100)) STORED
);

-- ------------------------------------------------------------
-- Useful indexes for dashboard query performance
-- ------------------------------------------------------------
CREATE INDEX idx_orders_date       ON orders(order_date);
CREATE INDEX idx_orders_store      ON orders(store_id);
CREATE INDEX idx_orders_customer   ON orders(customer_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_prod  ON order_items(product_id);
CREATE INDEX idx_customers_region  ON customers(region_id);
