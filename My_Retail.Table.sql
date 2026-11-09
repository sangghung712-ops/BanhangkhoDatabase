CREATE DATABASE IF NOT EXISTS Retail;
/* Switch to the Retail database */
USE Retail;


/* Drop existing tables in correct order to avoid foreign key constraints */
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS users;

-- ==========================
-- Table: Users
-- ==========================
CREATE TABLE users (
  user_id INT NOT NULL AUTO_INCREMENT,
  user_name VARCHAR(100) NOT NULL,
  user_password VARCHAR(200) NOT NULL,
  user_role VARCHAR(20) NOT NULL DEFAULT 'Customer' CHECK (user_role IN ('Admin', 'Customer')),

  PRIMARY KEY (user_id),
  UNIQUE KEY user_name (user_name)
);

-- ==========================
-- Table: Customers
-- (1-1 "has" relationship with Users: only accounts with role = 'Customer')
-- ==========================
CREATE TABLE customers (
  customer_id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL CHECK (email LIKE '%_@_%._%'),
  phone VARCHAR(20) NOT NULL CHECK (REGEXP_LIKE(phone, '^0[0-9]{9}$')),
  address VARCHAR(255) DEFAULT NULL,

  PRIMARY KEY (customer_id),
  UNIQUE KEY user_id (user_id),
  UNIQUE KEY email (email),
  UNIQUE KEY phone (phone),
  FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- ==========================
-- Table: Products
-- ==========================
CREATE TABLE products (
    product_id INT NOT NULL AUTO_INCREMENT,
    product_name VARCHAR(100) UNIQUE NOT NULL,
    price DECIMAL(10,2) NOT NULL CHECK (price > 0),
    category VARCHAR(100) NOT NULL,
    quantity INT NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    -- Product status
    product_status VARCHAR(20) NOT NULL DEFAULT 'Active'
        CHECK (product_status IN ('Active', 'Inactive')),

    PRIMARY KEY (product_id)
    
);

-- ==========================
-- Table: Orders
-- (linked to Customers via "place" and "payment" relationships,
--  payment_method / payment_status stored directly here)
-- ==========================
CREATE TABLE orders (
  order_id INT NOT NULL AUTO_INCREMENT,
  customer_id INT NOT NULL,
  order_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  shipping_date DATETIME DEFAULT NULL,
  payment_date DATETIME DEFAULT NULL,
  order_status VARCHAR(45) NOT NULL DEFAULT 'Pending' CHECK (order_status IN ('Pending', 'Confirmed', 'Shipping', 'Completed', 'Cancelled')),
  shipping_address VARCHAR(255) NOT NULL ,
  total_amount DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
  payment_method VARCHAR(50) NOT NULL DEFAULT 'Cash' CHECK (payment_method IN ('Cash', 'Online')),
  payment_status VARCHAR(50) NOT NULL DEFAULT 'Unpaid' CHECK (payment_status IN ('Unpaid', 'Paid', 'Refunded')),

  PRIMARY KEY (order_id),
  KEY customer_id (customer_id),
  FOREIGN KEY (customer_id) REFERENCES customers (customer_id),

  CONSTRAINT chk_shipping_date CHECK (shipping_date IS NULL OR shipping_date >= order_date),
  CONSTRAINT chk_payment_date CHECK (payment_date IS NULL OR payment_date >= order_date)
);

-- ==========================
-- Table: Order_items
-- ==========================
CREATE TABLE order_items (
    order_item_id INT NOT NULL AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
   

    PRIMARY KEY (order_item_id),
    
    UNIQUE KEY uq_order_items_order_product (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

