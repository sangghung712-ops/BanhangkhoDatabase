USE Retail;
-- ---------------------------- CHUAN BI -------------------------------
SET @c1 = (SELECT customer_id FROM customers WHERE email = 'an.nguyen@gmail.com');
SET @c2 = (SELECT customer_id FROM customers WHERE email = 'binh.tran@gmail.com');

SET @o_ship    = (SELECT MIN(order_id) FROM orders WHERE order_status = 'Shipping');
SET @o_cancel  = (SELECT MIN(order_id) FROM orders WHERE order_status = 'Cancelled');
SET @p_samsung = (SELECT product_id FROM products WHERE product_name = 'Samsung Galaxy A55 128GB');
SET @p_loa     = (SELECT product_id FROM products WHERE product_name = 'Loa Bluetooth Xiaomi');      -- ton kho 0
SET @p_sandisk = (SELECT product_id FROM products WHERE product_name = 'The nho SanDisk 128GB');     -- Inactive
SELECT  @o_ship, @o_cancel, @p_samsung, @p_loa, @p_sandisk; -- khong duoc co NULL
-- ======================= A. RANG BUOC BANG (CHECK / UNIQUE / FK) =====
-- TC01: Gia am -> loi CHECK (price > 0)
INSERT INTO products (product_name, price, category, quantity)
VALUES ('San pham test 1', -5, 'Test', 1);
-- TC02: Ton kho am -> loi CHECK (quantity >= 0)
INSERT INTO products (product_name, price, category, quantity)
VALUES ('San pham test 2', 1000, 'Test', -3);
 
-- TC03: Trung ten san pham -> loi Duplicate entry (UNIQUE product_name)
INSERT INTO products (product_name, price, category, quantity)
VALUES ('iPhone 15 128GB', 1000, 'Test', 1);
-- TC05: Don hang cua khach khong ton tai -> loi FOREIGN KEY
INSERT INTO orders (customer_id, shipping_address, payment_method)
VALUES (9999, 'Ha Noi', 'Cash');
-- TC06: Phuong thuc thanh toan khong hop le -> loi CHECK (payment_method)
INSERT INTO orders (customer_id, shipping_address, payment_method)
VALUES (@c1, 'Ha Noi', 'Bitcoin');
-- ======================= B. DANG KY KHACH (TRANSACTION + ROLLBACK) ===
-- TC08: Trung username -> loi Duplicate entry (UNIQUE user_name), ROLLBACK
CALL dang_ky_khach_hang('nguyenvana', '123456', 'Nguoi Khac', 'khac@gmail.com', '0967890123', 'Ha Noi');
 
-- TC09: Trung email -> loi Duplicate entry (UNIQUE email), ROLLBACK
CALL dang_ky_khach_hang('testuser2', '123456', 'Test User', 'an.nguyen@gmail.com', '0967890124', 'Ha Noi');
 
-- TC10: Trung so dien thoai -> loi Duplicate entry (UNIQUE phone), ROLLBACK
CALL dang_ky_khach_hang('testuser3', '123456', 'Test User', 'test3@gmail.com', '0901234567', 'Ha Noi');
-- ======================= C. TRIGGER ==================================
-- TC11: Dat vuot ton kho -> 'Khong du hang trong kho'
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o_pending, @p_samsung, 9999);
 -- TC12 Them san pham vao don khong con Pending -> 'Chi them san pham vao don dang Pending'
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o_ship, @p_samsung, 1);
-- TC16: Xoa dong san pham cua don da Shipping -> 'Khong the xoa san pham khi don khong con Pending'
DELETE FROM order_items WHERE order_id = @o_ship;-- TC16: Xoa dong san pham cua don da Shipping -> 'Khong the xoa san pham khi don khong con Pending'
-- ======================= D. STORED PROCEDURE =========================

-- TC19: Don da huy khong the doi tiep -> 'Khong the chuyen sang trang thai nay'
CALL cap_nhat_trang_thai_don_hang(@o_cancel, 'Confirmed');
 