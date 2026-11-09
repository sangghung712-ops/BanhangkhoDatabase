-- ---------------------------------------------------------------------
-- 3.1 Dang ky khach hang (users + customers trong 1 transaction)
-- ---------------------------------------------------------------------
USE Retail;
DROP PROCEDURE IF EXISTS dang_ky_khach_hang;
 
DELIMITER $$
 
CREATE PROCEDURE dang_ky_khach_hang(
    IN p_user_name VARCHAR(100),
    IN p_user_password VARCHAR(200),
    IN p_name VARCHAR(100),
    IN p_email VARCHAR(100),
    IN p_phone VARCHAR(20),
    IN p_address VARCHAR(255)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    START TRANSACTION;
 
    INSERT INTO users (user_name, user_password)
    VALUES (p_user_name, p_user_password);
 
    INSERT INTO customers (user_id, name, email, phone, address)
    VALUES (LAST_INSERT_ID(), p_name, p_email, p_phone, p_address);
 
    COMMIT;
END$$
 
DELIMITER ;
 
 

 
-- ---------------------------------------------------------------------
-- 4.1 Them san pham
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS them_san_pham;
 
DELIMITER $$
 
CREATE PROCEDURE them_san_pham(
    IN p_name VARCHAR(100),
    IN p_price DECIMAL(10,2),
    IN p_category VARCHAR(100),
    IN p_quantity INT
)
BEGIN
    DECLARE v_product_count INT DEFAULT 0;
 
    SELECT COUNT(*)
    INTO v_product_count
    FROM products
    WHERE product_name = p_name;
 
    IF v_product_count > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'San pham da ton tai';
 
    ELSEIF p_price IS NULL OR p_price <= 0
        OR p_quantity IS NULL OR p_quantity < 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Gia va so luong khong hop le';
 
    ELSE
        INSERT INTO products (product_name, price, category, quantity)
        VALUES (p_name, p_price, p_category, p_quantity);
    END IF;
END$$
 
DELIMITER ;
-- ---------------------------------------------------------------------
-- 4.2 Sua thong tin san pham (tham so NULL/rong = giu nguyen).
--     Doi gia chi anh huong don tao sau do (total_amount da luu co dinh).
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS cap_nhat_san_pham;
 
DELIMITER $$
 
CREATE PROCEDURE cap_nhat_san_pham(
    IN p_product_id INT,
    IN p_name VARCHAR(100),
    IN p_price DECIMAL(10,2),
    IN p_category VARCHAR(100)
)
BEGIN
    DECLARE v_count INT DEFAULT 0;
    DECLARE v_dup INT DEFAULT 0;
 
    SELECT COUNT(*) INTO v_count
    FROM products
    WHERE product_id = p_product_id;
 
    IF v_count = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'San pham khong ton tai';
    END IF;
    IF p_price IS NOT NULL AND p_price <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Gia phai lon hon 0';
    END IF;
 
    IF NULLIF(TRIM(p_name), '') IS NOT NULL THEN
        SELECT COUNT(*) INTO v_dup
        FROM products
        WHERE product_name = TRIM(p_name)
          AND product_id <> p_product_id;
 
        IF v_dup > 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Ten san pham da ton tai';
        END IF;
    END IF;
 
    UPDATE products
    SET product_name = COALESCE(NULLIF(TRIM(p_name), ''), product_name),
        price        = COALESCE(p_price, price),
        category     = COALESCE(NULLIF(TRIM(p_category), ''), category)
    WHERE product_id = p_product_id;
END$$
 
DELIMITER ;
 
-- ---------------------------------------------------------------------
-- 4.3 Admin cap nhat ton kho thu cong (dat so luong moi)
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS cap_nhat_ton_kho;
 
DELIMITER $$
 
CREATE PROCEDURE cap_nhat_ton_kho(
    IN p_product_id INT,
    IN p_quantity INT
)
BEGIN
    DECLARE v_count INT DEFAULT 0;
 
    IF p_quantity IS NULL OR p_quantity < 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'So luong ton kho khong hop le';
    END IF;
 
    SELECT COUNT(*) INTO v_count
    FROM products
    WHERE product_id = p_product_id;
 
    IF v_count = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'San pham khong ton tai';
    END IF;
 
    UPDATE products
    SET quantity = p_quantity
    WHERE product_id = p_product_id;
END$$
 
DELIMITER ;
-- ---------------------------------------------------------------------
-- 4.4 Ngung kinh doanh san pham
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS ngung_kinh_doanh_san_pham;
 
DELIMITER $$
 
CREATE PROCEDURE ngung_kinh_doanh_san_pham(
    IN p_product_id INT
)
BEGIN
    DECLARE v_product_count INT DEFAULT 0;
 
    SELECT COUNT(*)
    INTO v_product_count
    FROM products
    WHERE product_id = p_product_id;
 
    IF v_product_count = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'San pham khong ton tai';
    ELSE
        UPDATE products
        SET product_status = 'Inactive'
        WHERE product_id = p_product_id;
    END IF;
END$$
 
DELIMITER ;
-- ---------------------------------------------------------------------
-- 4.5 Kinh doanh lai san pham
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS kinh_doanh_lai_san_pham;
 
DELIMITER $$
 
CREATE PROCEDURE kinh_doanh_lai_san_pham(
    IN p_product_id INT
)
BEGIN
    DECLARE v_product_count INT DEFAULT 0;
 
    SELECT COUNT(*)
    INTO v_product_count
    FROM products
    WHERE product_id = p_product_id;
 
    IF v_product_count = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'San pham khong ton tai';
    ELSE
        UPDATE products
        SET product_status = 'Active'
        WHERE product_id = p_product_id;
    END IF;
END$$
 
DELIMITER ;
-- ---------------------------------------------------------------------
-- 5.1 Tao don hang RONG (giu lai de tuong thich; GUI nen dung
--     tao_don_hang_tu_gio de tao don kem san pham trong 1 transaction)
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS tao_don_hang;
 
DELIMITER $$
 
CREATE PROCEDURE tao_don_hang(
    IN p_customer_id INT,
    IN p_shipping_address VARCHAR(255),
    IN p_payment_method VARCHAR(50),
    OUT p_order_id INT
)
BEGIN
    DECLARE v_customer_count INT DEFAULT 0;
    DECLARE v_profile_address VARCHAR(255);
    DECLARE v_final_address VARCHAR(255);
    DECLARE v_payment_method VARCHAR(50);
 
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    START TRANSACTION;
 
    SELECT COUNT(*)
    INTO v_customer_count
    FROM customers
    WHERE customer_id = p_customer_id;
 
    IF v_customer_count = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Khach hang khong ton tai';
    END IF;
 
    SELECT address
    INTO v_profile_address
    FROM customers
    WHERE customer_id = p_customer_id
    FOR UPDATE;
 
    IF p_shipping_address IS NOT NULL AND TRIM(p_shipping_address) = '' THEN
        SET p_shipping_address = NULL;
    END IF;
    IF v_profile_address IS NOT NULL AND TRIM(v_profile_address) = '' THEN
        SET v_profile_address = NULL;
    END IF;
 
    SET v_final_address = COALESCE(p_shipping_address, v_profile_address);
 
    IF v_final_address IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Chua co dia chi giao hang';
    END IF;
 
    IF p_payment_method IS NULL OR TRIM(p_payment_method) = '' THEN
        SET v_payment_method = 'Cash';
    ELSE
        SET v_payment_method = TRIM(p_payment_method);
    END IF;
 
    IF v_payment_method NOT IN ('Cash', 'Online') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Phuong thuc thanh toan khong hop le';
    END IF;
 
    IF v_profile_address IS NULL THEN
        UPDATE customers
        SET address = v_final_address
        WHERE customer_id = p_customer_id;
    END IF;
    INSERT INTO orders (customer_id, shipping_address, total_amount, payment_method)
    VALUES (p_customer_id, v_final_address, 0, v_payment_method);
 
    SET p_order_id = LAST_INSERT_ID();
 
    COMMIT;
END$$
 
DELIMITER ;
-- 5.6 Cap nhat trang thai don hang (ADMIN) - da bo sung:
--     * Shipping  : ghi shipping_date
--     * Completed : Cash -> Paid + payment_date; Online phai da Paid
--     * Cancelled : hoan kho, Paid -> Refunded
-- ---------------------------------------------------------------------
DROP PROCEDURE IF EXISTS cap_nhat_trang_thai_don_hang;
 
DELIMITER $$
 
CREATE PROCEDURE cap_nhat_trang_thai_don_hang(
    IN p_order_id INT,
    IN p_new_status VARCHAR(45)
)
BEGIN
    DECLARE v_old_status VARCHAR(45);
    DECLARE v_payment_method VARCHAR(50);
    DECLARE v_payment_status VARCHAR(50);
 
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
 
    IF p_new_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Trang thai moi khong hop le';
    END IF;
 
    START TRANSACTION;
 
    -- Lay thong tin don va khoa dong don hang
    SELECT order_status, payment_method, payment_status
    INTO v_old_status, v_payment_method, v_payment_status
    FROM orders
    WHERE order_id = p_order_id
    FOR UPDATE;
 
    IF v_old_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Don hang khong ton tai';
    END IF;
 
    -- Chi cho chuyen tien theo thu tu, hoac huy khi Pending/Confirmed
    IF NOT (
        (v_old_status = 'Pending'
            AND p_new_status IN ('Confirmed', 'Cancelled'))
        OR
        (v_old_status = 'Confirmed'
            AND p_new_status IN ('Shipping', 'Cancelled'))
        OR
        (v_old_status = 'Shipping'
            AND p_new_status = 'Completed')
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Khong the chuyen sang trang thai nay';
    END IF;
 
    IF p_new_status = 'Completed'
       AND v_payment_method = 'Online'
       AND v_payment_status <> 'Paid' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Don Online chua thanh toan, khong the hoan thanh';
    END IF;
    -- Cap nhat theo tung trang thai moi
    IF p_new_status = 'Shipping' THEN
 
        UPDATE orders
        SET order_status = 'Shipping',
            shipping_date = NOW()
        WHERE order_id = p_order_id;
 
    ELSEIF p_new_status = 'Completed' THEN
 
        -- Cash: nhan hang xong moi thu tien. Online: da Paid, giu payment_date cu
        UPDATE orders
        SET order_status = 'Completed',
            payment_status = 'Paid',
            payment_date = COALESCE(payment_date, NOW())
        WHERE order_id = p_order_id;
 
    ELSEIF p_new_status = 'Cancelled' THEN
        -- Hoan lai ton kho theo tung dong order_items
        UPDATE products p
        JOIN (
            SELECT product_id, SUM(quantity) AS total_quantity
            FROM order_items
            WHERE order_id = p_order_id
            GROUP BY product_id
        ) oi ON p.product_id = oi.product_id
        SET p.quantity = p.quantity + oi.total_quantity;
 
        -- Da thanh toan thi chuyen sang da hoan tien
        UPDATE orders
        SET order_status = 'Cancelled',
            payment_status = IF(payment_status = 'Paid', 'Refunded', payment_status)
        WHERE order_id = p_order_id;
 
    ELSE
 
        UPDATE orders
        SET order_status = p_new_status
        WHERE order_id = p_order_id;
 
    END IF;
 
    COMMIT;
END$$
DELIMITER ;
 
