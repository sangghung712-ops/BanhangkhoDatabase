USE Retail;
 
-- ---------------------------------------------------------------------
-- 7.1 Thong tin khach hang (KHONG lo mat khau)
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_thong_tin_khach_hang;
CREATE VIEW v_thong_tin_khach_hang AS
SELECT c.customer_id,
       u.user_id,
       u.user_name,
       u.user_role,
       c.name,
       c.email,
       c.phone,
       c.address
FROM customers c
JOIN users u ON u.user_id = c.user_id;
 
-- ---------------------------------------------------------------------
-- 7.2 Tinh trang ton kho san pham
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_ton_kho_san_pham;
CREATE VIEW v_ton_kho_san_pham AS
SELECT product_id,
       product_name,
       category,
       price,
       quantity,
       product_status,
       CASE
           WHEN quantity = 0  THEN 'Het hang'
           WHEN quantity <= 10 THEN 'Sap het hang'
           ELSE 'Con hang'
       END AS tinh_trang_kho
FROM products;
 
-- ---------------------------------------------------------------------
-- 7.3 San pham dang kinh doanh va con hang (danh muc cho khach)
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_san_pham_dang_ban;
CREATE VIEW v_san_pham_dang_ban AS
SELECT product_id, product_name, category, price, quantity
FROM products
WHERE product_status = 'Active'
  AND quantity > 0;
 
-- ---------------------------------------------------------------------
-- 7.4 Canh bao san pham sap het / het hang (chi san pham Active)
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_canh_bao_ton_kho;
CREATE VIEW v_canh_bao_ton_kho AS
SELECT product_id, product_name, category, quantity
FROM products
WHERE product_status = 'Active'
  AND quantity <= 10
ORDER BY quantity, product_name;
-- ---------------------------------------------------------------------
-- 7.5 Tong quan don hang (kem ten khach, so dong, tong so luong)
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_tong_quan_don_hang;
CREATE VIEW v_tong_quan_don_hang AS
SELECT o.order_id,
       o.customer_id,
       c.name AS customer_name,
       c.phone,
       o.order_date,
       o.order_status,
       o.payment_method,
       o.payment_status,
       o.total_amount,
       o.shipping_date,
       o.payment_date,
       o.shipping_address,
       COUNT(oi.order_item_id)         AS so_dong_san_pham,
       COALESCE(SUM(oi.quantity), 0)   AS tong_so_luong
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
LEFT JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY o.order_id, o.customer_id, c.name, c.phone, o.order_date,
         o.order_status, o.payment_method, o.payment_status, o.total_amount,
         o.shipping_date, o.payment_date, o.shipping_address;
 
-- ---------------------------------------------------------------------
-- 7.6 Chi tiet dong san pham trong don
--     (gia_hien_tai co the khac gia luc dat; tong tien that o orders.total_amount)
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_chi_tiet_don_hang;
CREATE VIEW v_chi_tiet_don_hang AS
SELECT oi.order_id,
       o.order_status,
       o.customer_id,
       c.name AS customer_name,
       oi.product_id,
       p.product_name,
       p.category,
       oi.quantity,
       p.price AS gia_hien_tai,
       oi.quantity * p.price AS thanh_tien_hien_tai
FROM order_items oi
JOIN orders o    ON o.order_id = oi.order_id
JOIN customers c ON c.customer_id = o.customer_id
JOIN products p  ON p.product_id = oi.product_id;
-- ---------------------------------------------------------------------
-- 7.7 Doanh thu theo thang (Completed & Paid, theo payment_date)
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_doanh_thu_theo_thang;
CREATE VIEW v_doanh_thu_theo_thang AS
SELECT DATE_FORMAT(payment_date, '%Y-%m') AS thang,
       COUNT(*)                           AS so_don,
       SUM(total_amount)                  AS doanh_thu
FROM orders
WHERE order_status = 'Completed'
  AND payment_status = 'Paid'
  AND payment_date IS NOT NULL
GROUP BY DATE_FORMAT(payment_date, '%Y-%m');
 
-- ---------------------------------------------------------------------
-- 7.8 San pham ban chay (don Completed)
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_san_pham_ban_chay;
CREATE VIEW v_san_pham_ban_chay AS
SELECT p.product_id,
       p.product_name,
       p.category,
       SUM(oi.quantity) AS so_luong_da_ban
FROM order_items oi
JOIN orders o   ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.order_status = 'Completed'
GROUP BY p.product_id, p.product_name, p.category;
-- ---------------------------------------------------------------------
-- 7.9 Tong chi tieu cua tung khach (don Completed)
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_chi_tieu_khach_hang;
CREATE VIEW v_chi_tieu_khach_hang AS
SELECT c.customer_id,
       c.name,
       c.email,
       COUNT(o.order_id)                 AS so_don_hoan_thanh,
       COALESCE(SUM(o.total_amount), 0)  AS tong_chi_tieu
FROM customers c
LEFT JOIN orders o
       ON o.customer_id = c.customer_id
      AND o.order_status = 'Completed'
GROUP BY c.customer_id, c.name, c.email;
 
-- ---------------------------------------------------------------------
-- 7.10 Thong ke don hang theo trang thai
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_thong_ke_trang_thai_don;
CREATE VIEW v_thong_ke_trang_thai_don AS
SELECT order_status,
       COUNT(*)          AS so_don,
       SUM(total_amount) AS tong_gia_tri
FROM orders
GROUP BY order_status;
 
