CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.customers (
    customer_id INTEGER PRIMARY KEY,
    signup_date DATE NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.products (
    product_id INTEGER PRIMARY KEY,
    category TEXT NOT NULL,
    unit_cost NUMERIC(12,2) NOT NULL CHECK (unit_cost >= 0)
);

CREATE TABLE IF NOT EXISTS raw.sessions (
    session_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES raw.customers(customer_id),
    session_ts TIMESTAMPTZ NOT NULL,
    channel TEXT NOT NULL,
    landing_page TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES raw.customers(customer_id),
    session_id INTEGER NOT NULL REFERENCES raw.sessions(session_id),
    order_ts TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('paid', 'cancelled', 'refunded'))
);

CREATE TABLE IF NOT EXISTS raw.order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES raw.orders(order_id),
    product_id INTEGER NOT NULL REFERENCES raw.products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0)
);
