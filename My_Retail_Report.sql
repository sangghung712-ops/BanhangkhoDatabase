
-- ---------------------------------------------------------------------
-- 6.1 Lich su don hang cua mot khach
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS xem_don_hang_khach;
 
DELIMITER $$
 
CREATE PROCEDURE xem_don_hang_khach(
    IN p_customer_id INT
)
BEGIN
    SELECT order_id, order_date, order_status, total_amount,
           payment_method, payment_status, shipping_date, payment_date,
           shipping_address
    FROM orders
    WHERE customer_id = p_customer_id
    ORDER BY order_date DESC, order_id DESC;
END$$
 
DELIMITER ;
-- ---------------------------------------------------------------------
-- 6.2 Chi tiet mot don hang. Khach truyen customer_id cua minh (chi xem
--     duoc don cua minh); admin truyen NULL de xem moi don.
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS xem_chi_tiet_don_hang;
 
DELIMITER $$
 
CREATE PROCEDURE xem_chi_tiet_don_hang(
    IN p_order_id INT,
    IN p_customer_id INT
)
BEGIN
    DECLARE v_owner INT;
    DECLARE v_status VARCHAR(45);
 
    SELECT customer_id, order_status
    INTO v_owner, v_status
    FROM orders
    WHERE order_id = p_order_id;
 
    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Don hang khong ton tai';
    END IF;
 
    IF p_customer_id IS NOT NULL AND v_owner <> p_customer_id THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Khong co quyen xem don nay';
    END IF;
 
    -- Thong tin don
    SELECT o.order_id, o.customer_id, c.name AS customer_name, o.order_date,
           o.order_status, o.total_amount, o.payment_method, o.payment_status,
           o.shipping_date, o.payment_date, o.shipping_address
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.order_id = p_order_id;
 
    -- Cac dong san pham (gia_hien_tai = gia ban hien tai, co the khac gia luc dat;
    -- tong tien that su cua don nam o orders.total_amount)
    SELECT oi.product_id, p.product_name, oi.quantity, p.price AS gia_hien_tai
    FROM order_items oi
    JOIN products p ON p.product_id = oi.product_id
    WHERE oi.order_id = p_order_id
    ORDER BY oi.order_item_id;
END$$
 
DELIMITER ;
 
 
-- ---------------------------------------------------------------------
-- 6.3 Admin loc don hang theo trang thai va/hoac khoang ngay dat
--     (tham so NULL = khong loc)
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS admin_loc_don_hang;
 
DELIMITER $$
 
CREATE PROCEDURE admin_loc_don_hang(
    IN p_status VARCHAR(45),
    IN p_from DATE,
    IN p_to DATE
)
BEGIN
    IF p_status IS NOT NULL
       AND p_status NOT IN ('Pending', 'Confirmed', 'Shipping', 'Completed', 'Cancelled') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Trang thai loc khong hop le';
    END IF;
 
    SELECT o.order_id, o.customer_id, c.name AS customer_name, o.order_date,
           o.order_status, o.total_amount, o.payment_method, o.payment_status
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE (p_status IS NULL OR o.order_status = p_status)
      AND (p_from IS NULL OR o.order_date >= p_from)
      AND (p_to IS NULL OR o.order_date < DATE_ADD(p_to, INTERVAL 1 DAY))
    ORDER BY o.order_date DESC, o.order_id DESC;
END$$
 
DELIMITER ;
 
 
-- ---------------------------------------------------------------------
-- 6.4 Bao cao doanh thu theo ky: p_group = 'DAY' | 'MONTH' | 'YEAR'
--     Chi tinh don Completed & Paid, theo payment_date.
--     p_from / p_to NULL = khong gioi han.
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS bao_cao_doanh_thu;
 
DELIMITER $$
 
CREATE PROCEDURE bao_cao_doanh_thu(
    IN p_group VARCHAR(10),
    IN p_from DATE,
    IN p_to DATE
)
BEGIN
    DECLARE v_fmt VARCHAR(10);
 
    SET v_fmt = CASE UPPER(TRIM(p_group))
                    WHEN 'DAY'   THEN '%Y-%m-%d'
                    WHEN 'MONTH' THEN '%Y-%m'
                    WHEN 'YEAR'  THEN '%Y'
                    ELSE NULL
                END;
 
    IF v_fmt IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Nhom bao cao phai la DAY, MONTH hoac YEAR';
    END IF;
 
    SELECT DATE_FORMAT(payment_date, v_fmt) AS period,
           COUNT(*) AS so_don,
           SUM(total_amount) AS doanh_thu
    FROM orders
    WHERE order_status = 'Completed'
      AND payment_status = 'Paid'
      AND payment_date IS NOT NULL
      AND (p_from IS NULL OR payment_date >= p_from)
      AND (p_to IS NULL OR payment_date < DATE_ADD(p_to, INTERVAL 1 DAY))
    GROUP BY period
    ORDER BY period;
END$$
 
DELIMITER ;
 
 
-- ---------------------------------------------------------------------
-- 6.5 San pham ban chay (tinh tren don Completed)
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS san_pham_ban_chay;
 
DELIMITER $$
 
CREATE PROCEDURE san_pham_ban_chay(
    IN p_limit INT,
    IN p_from DATE,
    IN p_to DATE
)
BEGIN
    DECLARE v_limit INT;
 
    SET v_limit = IF(p_limit IS NULL OR p_limit <= 0, 10, p_limit);
 
    SELECT p.product_id,
           p.product_name,
           p.category,
           SUM(oi.quantity) AS so_luong_da_ban
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    JOIN products p ON p.product_id = oi.product_id
    WHERE o.order_status = 'Completed'
      AND (p_from IS NULL OR o.order_date >= p_from)
      AND (p_to IS NULL OR o.order_date < DATE_ADD(p_to, INTERVAL 1 DAY))
    GROUP BY p.product_id, p.product_name, p.category
    ORDER BY so_luong_da_ban DESC, p.product_name
    LIMIT v_limit;
END$$
 
DELIMITER ;
 
 
-- ---------------------------------------------------------------------
-- 6.6 Thong ke don hang theo trang thai
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS thong_ke_don_hang;
 
DELIMITER $$
 
CREATE PROCEDURE thong_ke_don_hang(
    IN p_from DATE,
    IN p_to DATE
)
BEGIN
    SELECT order_status,
           COUNT(*) AS so_don,
           SUM(total_amount) AS tong_gia_tri
    FROM orders
    WHERE (p_from IS NULL OR order_date >= p_from)
      AND (p_to IS NULL OR order_date < DATE_ADD(p_to, INTERVAL 1 DAY))
    GROUP BY order_status
    ORDER BY FIELD(order_status, 'Pending', 'Confirmed', 'Shipping', 'Completed', 'Cancelled');
END$$
 
DELIMITER ;
 
