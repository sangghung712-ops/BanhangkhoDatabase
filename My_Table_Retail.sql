/* Create the database */
CREATE DATABASE IF NOT EXISTS Retail;
/* Switch to the Retail database */
USE Retail;
/* Drop existing tables in correct order to avoid foreign key constraints */
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS users;
-- ==========================
-- Table: Users
-- ==========================
CREATE TABLE users (
  user_id INT NOT NULL AUTO_INCREMENT,
  user_name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL CHECK (email LIKE '%_@_%._%'),
  phone VARCHAR(45) NOT NULL CHECK (REGEXP_LIKE(phone, '^0[0-9]{9}$')),
  address VARCHAR(100) DEFAULT NULL,
  user_password VARCHAR(200) NOT NULL,
  user_role VARCHAR(50) NOT NULL DEFAULT 'Customer' CHECK (user_role IN ('Admin', 'Customer')),

  PRIMARY KEY (user_id),
  UNIQUE KEY email (email),
  UNIQUE KEY phone (phone)
   
);



-- ==========================
-- Table: Orders
-- ==========================
CREATE TABLE orders (
  order_id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  order_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  order_status VARCHAR(45) NOT NULL DEFAULT 'Pending' CHECK (order_status IN ('Pending', 'Confirmed', 'Shipping', 'Completed', 'Cancelled')),
  shipping_address VARCHAR(100) NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL CHECK (total_amount > 0),

  PRIMARY KEY (order_id),
  KEY user_id (user_id),
  FOREIGN KEY (user_id) REFERENCES users (user_id)
);




-- ==========================
-- Table: Products
-- ==========================
CREATE TABLE products (
    product_id INT NOT NULL AUTO_INCREMENT,
    product_name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    category VARCHAR(100),
    quantity INT NOT NULL DEFAULT 0 CHECK (quantity >= 0),

    PRIMARY KEY (product_id),
	UNIQUE (product_name)

);


-- ==========================
-- Table: Order_items
-- ==========================
CREATE TABLE order_items (
    order_item_id INT NOT NULL AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL  CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price > 0),

    PRIMARY KEY (order_item_id),

	FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);




-- ==========================
-- Table: Payments
-- ==========================
CREATE TABLE payments (
  payment_id INT NOT NULL AUTO_INCREMENT,
  order_id INT NOT NULL,
  payment_method VARCHAR(50) NOT NULL CHECK (payment_method IN ('Cash', 'Bank_transfer', 'E_wallet')),
  payment_status VARCHAR(50) NOT NULL DEFAULT 'Unpaid' CHECK (payment_status IN ('Unpaid', 'Paid','Refunded')),

  PRIMARY KEY (payment_id),
  UNIQUE KEY order_id (order_id),
  FOREIGN KEY (order_id) REFERENCES orders (order_id)
);

