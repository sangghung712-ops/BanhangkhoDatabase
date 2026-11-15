USE Retail;
-- =====================================================================
-- 1. KHACH HANG (5) - qua procedure dang_ky_khach_hang (users + customers)
--    Mat khau mau: 123456 (neu app da hash mat khau thi thay bang gia tri hash)
-- =====================================================================
CALL dang_ky_khach_hang('nguyenvana', '123456', 'Nguyen Van An',  'an.nguyen@gmail.com', '0901234567', '12 Nguyen Hue, Quan 1, TP.HCM');
CALL dang_ky_khach_hang('tranthib',   '123456', 'Tran Thi Binh',  'binh.tran@gmail.com', '0912345678', '45 Le Loi, Hai Chau, Da Nang');
CALL dang_ky_khach_hang('levanc',     '123456', 'Le Van Cuong',   'cuong.le@gmail.com',  '0923456789', '78 Tran Phu, TP. Tan An, Long An');
CALL dang_ky_khach_hang('phamthid',   '123456', 'Pham Thi Dung',  'dung.pham@gmail.com', '0934567890', '23 Hung Vuong, Ninh Kieu, Can Tho');
CALL dang_ky_khach_hang('hoangvane',  '123456', 'Hoang Van Em',   'em.hoang@gmail.com',  '0945678901', NULL);  -- chua co dia chi
SET @c1 = (SELECT customer_id FROM customers WHERE email = 'an.nguyen@gmail.com');
SET @c2 = (SELECT customer_id FROM customers WHERE email = 'binh.tran@gmail.com');
SET @c3 = (SELECT customer_id FROM customers WHERE email = 'cuong.le@gmail.com');
SET @c4 = (SELECT customer_id FROM customers WHERE email = 'dung.pham@gmail.com');
SET @c5 = (SELECT customer_id FROM customers WHERE email = 'em.hoang@gmail.com');
-- =====================================================================
-- 2. SAN PHAM (20) - chi ban do dien tu
--    Co san pham ton kho thap (3, 5, 8), het hang (0) va 1 san pham ngung ban
-- =====================================================================
INSERT INTO products (product_name, price, category, quantity) VALUES
-- Dien thoai
('Samsung Galaxy A55 128GB',        9990000, 'Dien thoai',     25),   -- p1
('iPhone 15 128GB',                18990000, 'Dien thoai',     15),   -- p2
('Xiaomi Redmi Note 13',            5490000, 'Dien thoai',     30),   -- p3
-- Laptop
('Laptop Dell Inspiron 15',        15990000, 'Laptop',         10),   -- p4
('Laptop Asus Vivobook 14',        13490000, 'Laptop',         12),   -- p5
('MacBook Air M2 13 inch',         24990000, 'Laptop',          3),   -- p6  (sap het)
-- May tinh bang
('iPad Gen 10 64GB',                9490000, 'May tinh bang',  14),   -- p7
('Samsung Galaxy Tab A9',           4290000, 'May tinh bang',  20),   -- p8
-- Am thanh
('Tai nghe AirPods 2',              3290000, 'Am thanh',       40),   -- p9
('Loa JBL Flip 6',                  2890000, 'Am thanh',       25),   -- p10
('Tai nghe Sony WH-1000XM5',        6990000, 'Am thanh',        8),   -- p11 
('Loa Bluetooth Xiaomi',             590000, 'Am thanh',        0),   -- p12 
-- Phu kien
('Sac nhanh Anker 20W',              290000, 'Phu kien',      100),   -- p13
('Cap USB-C 1m',                     120000, 'Phu kien',      150),   -- p14
('Chuot Logitech M331',              250000, 'Phu kien',       60),   -- p15
('Ban phim co Keychron K2',         1890000, 'Phu kien',        5),   -- p16 
('Pin du phong Xiaomi 10000mAh',     450000, 'Phu kien',       45),   -- p17
('The nho SanDisk 128GB',            220000, 'Phu kien',       70),   -- p18 
-- Man hinh & TV
('Man hinh LG 24 inch',             3290000, 'Man hinh & TV',  18),   -- p19
('Smart Tivi Samsung 43 inch',      8990000, 'Man hinh & TV',   9);   -- p20

-- Ma san pham lien tiep tu dau (dung cho phan don hang ben duoi)
SET @pb = LAST_INSERT_ID();
SET @p1  = @pb,      @p2  = @pb + 1,  @p3  = @pb + 2,  @p4  = @pb + 3,  @p5  = @pb + 4,
    @p6  = @pb + 5,  @p7  = @pb + 6,  @p8  = @pb + 7,  @p9  = @pb + 8,  @p10 = @pb + 9,
    @p11 = @pb + 10, @p12 = @pb + 11, @p13 = @pb + 12, @p14 = @pb + 13, @p15 = @pb + 14,
    @p16 = @pb + 15, @p17 = @pb + 16, @p18 = @pb + 17, @p19 = @pb + 18, @p20 = @pb + 19;
-- Don 1: Pending, Cash (khach moi dat, cho xac nhan)
INSERT INTO orders (customer_id, shipping_address, payment_method)
VALUES (@c1, '12 Nguyen Hue, Quan 1, TP.HCM', 'Cash');
SET @o1 = LAST_INSERT_ID();
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o1, @p1, 1), (@o1, @p13, 2);
-- Don 2: Confirmed, Cash
INSERT INTO orders (customer_id, shipping_address, payment_method)
VALUES (@c2, '45 Le Loi, Hai Chau, Da Nang', 'Cash');
SET @o2 = LAST_INSERT_ID();
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o2, @p3, 1), (@o2, @p14, 2);
CALL cap_nhat_trang_thai_don_hang(@o2, 'Confirmed');
-- Don 3: Shipping, Cash (dang giao)
INSERT INTO orders (customer_id, shipping_address, payment_method)
VALUES (@c3, '78 Tran Phu, TP. Tan An, Long An', 'Cash');
SET @o3 = LAST_INSERT_ID();
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o3, @p5, 1), (@o3, @p15, 1);
CALL cap_nhat_trang_thai_don_hang(@o3, 'Confirmed');
CALL cap_nhat_trang_thai_don_hang(@o3, 'Shipping');
 -- Don 4: Completed, Cash (thang 9)
INSERT INTO orders (customer_id, shipping_address, payment_method)
VALUES (@c1, '12 Nguyen Hue, Quan 1, TP.HCM', 'Cash');
SET @o4 = LAST_INSERT_ID();
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o4, @p9, 1), (@o4, @p13, 1);
CALL cap_nhat_trang_thai_don_hang(@o4, 'Confirmed');
CALL cap_nhat_trang_thai_don_hang(@o4, 'Shipping');
CALL cap_nhat_trang_thai_don_hang(@o4, 'Completed');
UPDATE orders SET order_date = '2026-09-10 09:00:00', shipping_date = '2026-09-11 08:30:00',
                  payment_date = '2026-09-13 15:00:00' WHERE order_id = @o4;
-- Don 5: Completed, Online da thanh toan (thang 10)
INSERT INTO orders (customer_id, shipping_address, payment_method)
VALUES (@c4, '23 Hung Vuong, Ninh Kieu, Can Tho', 'Online');
SET @o5 = LAST_INSERT_ID();
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o5, @p2, 1), (@o5, @p17, 1);
UPDATE orders SET payment_status = 'Paid', payment_date = NOW() WHERE order_id = @o5;  -- admin xac nhan da nhan tien
CALL cap_nhat_trang_thai_don_hang(@o5, 'Completed');
UPDATE orders SET order_date = '2026-10-05 10:00:00', payment_date = '2026-10-05 10:20:00',
                  shipping_date = '2026-10-06 14:00:00' WHERE order_id = @o5;
-- Don 6: Pending, Online chua thanh toan (de thu man hinh QR)
INSERT INTO orders (customer_id, shipping_address, payment_method)
VALUES (@c2, '45 Le Loi, Hai Chau, Da Nang', 'Online');
SET @o6 = LAST_INSERT_ID();
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o6, @p8, 1), (@o6, @p10, 1);
-- Don 7: Cancelled, Cash (khach huy khi con Pending -> kho duoc hoan lai)
INSERT INTO orders (customer_id, shipping_address, payment_method)
VALUES (@c4, '23 Hung Vuong, Ninh Kieu, Can Tho', 'Cash');
SET @o7 = LAST_INSERT_ID();
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o7, @p4, 1);
CALL cap_nhat_trang_thai_don_hang(@o7, 'Cancelled');
-- Don 8: Cancelled, Online da tra tien -> tu chuyen sang Refunded
INSERT INTO orders (customer_id, shipping_address, payment_method)
VALUES (@c3, '78 Tran Phu, TP. Tan An, Long An', 'Online');
SET @o8 = LAST_INSERT_ID();
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o8, @p19, 1);
UPDATE orders SET payment_status = 'Paid', payment_date = NOW() WHERE order_id = @o8;
CALL cap_nhat_trang_thai_don_hang(@o8, 'Confirmed');
-- Don 9: Completed, Cash (thang 10) - khach chua co dia chi trong ho so, nhap luc dat
INSERT INTO orders (customer_id, shipping_address, payment_method)
VALUES (@c5, '99 Pasteur, Quan 3, TP.HCM', 'Cash');
SET @o9 = LAST_INSERT_ID();
INSERT INTO order_items (order_id, product_id, quantity) VALUES (@o9, @p7, 1), (@o9, @p16, 1);
CALL cap_nhat_trang_thai_don_hang(@o9, 'Confirmed');
CALL cap_nhat_trang_thai_don_hang(@o9, 'Shipping');
CALL cap_nhat_trang_thai_don_hang(@o9, 'Completed');
UPDATE orders SET order_date = '2026-10-20 13:00:00', shipping_date = '2026-10-21 09:00:00',
                  payment_date = '2026-10-23 16:30:00' WHERE order_id = @o9;
-- 4. San pham ngung kinh doanh--
CALL ngung_kinh_doanh_san_pham(@p18);