-- ---------------------------------------------------------------------
-- 2. Khach hang (users + customers qua procedure dang ky)( chỉ mới chạy đơn 1)
-- ---------------------------------------------------------------------
USE Retail;
CALL dang_ky_khach_hang('nguyenvana', '123456', 'Nguyen Van A', 'vana@gmail.com', '0901234567', '12 Le Loi, Quan 1, TP.HCM');
CALL dang_ky_khach_hang('tranthib',   '123456', 'Tran Thi B',   'thib@gmail.com', '0912345678', '45 Nguyen Hue, Quan 1, TP.HCM');
CALL dang_ky_khach_hang('levanc',     '123456', 'Le Van C',     'vanc@gmail.com', '0923456789', '78 Tran Hung Dao, Quan 5, TP.HCM');
CALL dang_ky_khach_hang('phamthid',   '123456', 'Pham Thi D',   'thid@gmail.com', '0934567890', '9 Hai Ba Trung, Quan 3, TP.HCM');
CALL dang_ky_khach_hang('hoangvane',  '123456', 'Hoang Van E',  'vane@gmail.com', '0945678901', '23 Vo Van Tan, Quan 3, TP.HCM');
-- ---------------------------------------------------------------------
-- 3. San pham
-- ---------------------------------------------------------------------
INSERT INTO products (product_name, price, category, quantity) VALUES
('Laptop Dell Inspiron 15',          15990000, 'Laptop',     20),   -- id 1
('Laptop ASUS Vivobook 14',          13490000, 'Laptop',     15),   -- id 2
('iPhone 15 128GB',                  19990000, 'Dien thoai', 25),   -- id 3
('Samsung Galaxy A55',                9990000, 'Dien thoai', 30),   -- id 4
('Tai nghe Bluetooth Sony CH520',     1190000, 'Phu kien',   60),   -- id 5
('Chuot khong day Logitech M331',      350000, 'Phu kien',  100),   -- id 6
('Ban phim co Keychron K2',           2190000, 'Phu kien',   40),   -- id 7
('Man hinh LG 24 inch',               3290000, 'Man hinh',   35),   -- id 8
('Sac du phong Anker 10000mAh',        690000, 'Phu kien',   80),   -- id 9
('Loa JBL Flip 6',                    2890000, 'Loa',        25),   -- id 10
('May in Canon LBP2900',              3590000, 'May in',     10),   -- id 11
('Cap sac USB-C Baseus',               150000, 'Phu kien',  200),   -- id 12
('Dien thoai Nokia 105',               450000, 'Dien thoai',  5);   -- id 13 (se ngung kinh doanh)
 select * from products;
 select * from customers;
 select * from users;
USE Retail;
- ---------------------------------------------------------------------
-- 4. Don hang
--    Tao don -> them san pham (trigger tru kho + cong tien) -> doi trang thai
--    Cuoi moi don: chinh lai ngay de bao cao doanh thu co nhieu ky.
-- ---------------------------------------------------------------------
 
-- ---- Don 1: KH1, Cash, Completed (thang 9) ----
CALL tao_don_hang(1, NULL, 'Cash', @o1);
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o1, 1, 1), (@o1, 6, 2);
CALL cap_nhat_trang_thai_don_hang(@o1, 'Confirmed');
CALL cap_nhat_trang_thai_don_hang(@o1, 'Shipping');
CALL cap_nhat_trang_thai_don_hang(@o1, 'Completed');
UPDATE orders SET order_date = '2026-09-05 09:30:00', shipping_date = '2026-09-06 08:00:00',
                  payment_date = '2026-09-08 15:00:00' WHERE order_id = @o1;
-- ---- Don 2: KH2, Online, Paid + Completed (thang 9) ----
CALL tao_don_hang(2, NULL, 'Online', @o2);
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o2, 3, 1), (@o2, 5, 1);
UPDATE orders SET payment_status = 'Paid', payment_date = NOW() WHERE order_id = @o2;
CALL cap_nhat_trang_thai_don_hang(@o2, 'Confirmed');
CALL cap_nhat_trang_thai_don_hang(@o2, 'Shipping');
CALL cap_nhat_trang_thai_don_hang(@o2, 'Completed');
UPDATE orders SET order_date = '2026-09-20 10:15:00', payment_date = '2026-09-20 10:20:00',
                  shipping_date = '2026-09-21 09:00:00' WHERE order_id = @o2;
 
-- ---- Don 3: KH3, Cash, Completed (thang 10) ----
CALL tao_don_hang(3, NULL, 'Cash', @o3);
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o3, 4, 2), (@o3, 12, 3);
CALL cap_nhat_trang_thai_don_hang(@o3, 'Confirmed');
CALL cap_nhat_trang_thai_don_hang(@o3, 'Shipping');
CALL cap_nhat_trang_thai_don_hang(@o3, 'Completed');
UPDATE orders SET order_date = '2026-10-03 14:00:00', shipping_date = '2026-10-04 08:30:00',
                  payment_date = '2026-10-06 11:00:00' WHERE order_id = @o3;
 
-- ---- Don 4: KH1, Online, Completed (thang 10) ----
CALL tao_don_hang(1, '99 Pasteur, Quan 3, TP.HCM', 'Online', @o4);
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o4, 8, 2), (@o4, 7, 1);
UPDATE orders SET payment_status = 'Paid', payment_date = NOW() WHERE order_id = @o4;
CALL cap_nhat_trang_thai_don_hang(@o4, 'Confirmed');
CALL cap_nhat_trang_thai_don_hang(@o4, 'Shipping');
CALL cap_nhat_trang_thai_don_hang(@o4, 'Completed');
UPDATE orders SET order_date = '2026-10-15 16:45:00', payment_date = '2026-10-15 16:50:00',
                  shipping_date = '2026-10-16 09:00:00' WHERE order_id = @o4;
 
-- ---- Don 5: KH4, Cash, dang Shipping ----
CALL tao_don_hang(4, NULL, 'Cash', @o5);
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o5, 10, 1), (@o5, 9, 2);
CALL cap_nhat_trang_thai_don_hang(@o5, 'Confirmed');
CALL cap_nhat_trang_thai_don_hang(@o5, 'Shipping');
UPDATE orders SET order_date = '2026-11-05 13:20:00', shipping_date = '2026-11-06 08:00:00'
WHERE order_id = @o5;
 
-- ---- Don 6: KH5, Online da tra tien, Confirmed ----
CALL tao_don_hang(5, NULL, 'Online', @o6);
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o6, 2, 1);
UPDATE orders SET payment_status = 'Paid', payment_date = NOW() WHERE order_id = @o6;
CALL cap_nhat_trang_thai_don_hang(@o6, 'Confirmed');
 
-- ---- Don 7: KH2, Cash, Pending ----
CALL tao_don_hang(2, NULL, 'Cash', @o7);
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o7, 6, 1), (@o7, 12, 2);
 
-- ---- Don 8: KH3, Online da tra tien, bi Cancelled -> Refunded + hoan kho ----
CALL tao_don_hang(3, NULL, 'Online', @o8);
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o8, 11, 1);
UPDATE orders SET payment_status = 'Paid', payment_date = NOW() WHERE order_id = @o8;
CALL cap_nhat_trang_thai_don_hang(@o8, 'Confirmed');
CALL cap_nhat_trang_thai_don_hang(@o8, 'Cancelled');
 
-- ---- Don 9: KH4, Cash, Cancelled tu Pending ----
CALL tao_don_hang(4, NULL, 'Cash', @o9);
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o9, 5, 2);
CALL cap_nhat_trang_thai_don_hang(@o9, 'Cancelled');
-- ---- Don 10: KH5, Cash, Completed (thang 11) ----
CALL tao_don_hang(5, NULL, 'Cash', @o10);
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o10, 9, 1), (@o10, 6, 3);
CALL cap_nhat_trang_thai_don_hang(@o10, 'Confirmed');
CALL cap_nhat_trang_thai_don_hang(@o10, 'Shipping');
CALL cap_nhat_trang_thai_don_hang(@o10, 'Completed');
UPDATE orders SET order_date = '2026-11-02 11:00:00', shipping_date = '2026-11-03 08:00:00',
                  payment_date = '2026-11-04 17:00:00' WHERE order_id = @o10;
 
-- ---------------------------------------------------------------------
-- 5. Ngung kinh doanh san pham (sau khi da tao don, vi trigger chan SP Inactive)
-- ---------------------------------------------------------------------
CALL ngung_kinh_doanh_san_pham(13);

--------------------------------------------------------------------
-- 6. Kiem tra nhanh
-- ---------------------------------------------------------------------
SELECT * FROM v_tong_quan_don_hang ORDER BY order_id;
SELECT * FROM v_ton_kho_san_pham ORDER BY product_id;
SELECT * FROM v_doanh_thu_theo_thang ORDER BY thang;
SELECT * FROM v_san_pham_ban_chay ORDER BY so_luong_da_ban DESC;
SELECT * FROM v_chi_tieu_khach_hang ORDER BY tong_chi_tieu DESC;
SELECT * FROM v_thong_ke_trang_thai_don;
CALL bao_cao_doanh_thu('MONTH', NULL, NULL);
 



SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE order_items;
TRUNCATE TABLE orders;
TRUNCATE TABLE products;
TRUNCATE TABLE customers;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

