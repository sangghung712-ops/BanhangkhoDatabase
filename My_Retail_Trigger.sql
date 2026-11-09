
USE Retail;

DROP TRIGGER IF EXISTS trg_order_items_bi_check_stock;
DROP TRIGGER IF EXISTS trg_order_items_ai_deduct_stock;

DELIMITER $$
	
-- Trigger 1: Kiểm tra trước khi thêm sản phẩm
CREATE TRIGGER trg_order_items_bi_check_stock
BEFORE INSERT ON order_items
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(45);
    DECLARE v_stock INT;
    DECLARE v_product_status VARCHAR(20);
    DECLARE v_order_count INT DEFAULT 0;
    DECLARE v_product_count INT DEFAULT 0;

    -- Kiểm tra đơn hàng
    SELECT COUNT(*)
    INTO v_order_count
    FROM orders
    WHERE order_id = NEW.order_id;

    IF v_order_count = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Don hang khong ton tai';
    END IF;

    -- Kiểm tra trạng thái đơn hàng
    SELECT order_status
    INTO v_status
    FROM orders
    WHERE order_id = NEW.order_id;

    IF v_status <> 'Pending' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Chi them san pham vao don dang Pending';
    END IF;

    -- Kiểm tra sản phẩm
    SELECT COUNT(*)
    INTO v_product_count
    FROM products
    WHERE product_id = NEW.product_id;

    IF v_product_count = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'San pham khong ton tai';
    END IF;

    -- Lấy tồn kho và trạng thái sản phẩm
    SELECT quantity, product_status
    INTO v_stock, v_product_status
    FROM products
    WHERE product_id = NEW.product_id
    FOR UPDATE;

    -- Kiểm tra sản phẩm còn kinh doanh không
    IF v_product_status <> 'Active' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'San pham da ngung kinh doanh';
    END IF;

    -- Kiểm tra tồn kho
    IF NEW.quantity > v_stock THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Khong du hang trong kho';
    END IF;
END$$


-- Trigger 2: Trừ tồn kho và cập nhật tổng tiền
CREATE TRIGGER trg_order_items_ai_deduct_stock
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    DECLARE v_price DECIMAL(10,2);

    -- Lấy giá hiện tại của sản phẩm
    SELECT price
    INTO v_price
    FROM products
    WHERE product_id = NEW.product_id;

    -- Trừ số lượng tồn kho
    UPDATE products
    SET quantity = quantity - NEW.quantity
    WHERE product_id = NEW.product_id;

    -- Cộng tiền vào tổng đơn hàng
    UPDATE orders
    SET total_amount = total_amount + (NEW.quantity * v_price)
    WHERE order_id = NEW.order_id;
END$$

DELIMITER ;