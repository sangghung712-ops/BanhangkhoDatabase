from app.db import get_connection
from app.models import Order, OrderItem


def _query(sql, params=()):
    con = get_connection()
    try:
        cur = con.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        con.close()


_SELECT = ("SELECT o.*, c.name AS customer_name, c.phone AS customer_phone, "
           "c.email AS customer_email "
           "FROM orders o JOIN customers c ON c.customer_id = o.customer_id")


def _wrap(r):
    return {
        "order": Order.from_row(r),
        "customer_name": r["customer_name"],
        "customer_phone": r["customer_phone"],
        "customer_email": r["customer_email"],
    }


# ---------- Admin ----------
def get_all(status=None):
    sql = _SELECT
    params = []
    if status:
        sql += " WHERE o.order_status = %s"
        params.append(status)
    sql += " ORDER BY o.order_date DESC, o.order_id DESC"
    return [_wrap(r) for r in _query(sql, tuple(params))]


def get_by_id(order_id):
    rows = _query(_SELECT + " WHERE o.order_id = %s", (order_id,))
    if not rows:
        return None
    data = _wrap(rows[0])
    data["order"].items = get_items(order_id)
    return data


def get_items(order_id):
    rows = _query(
        "SELECT oi.*, p.product_name, p.price FROM order_items oi "
        "JOIN products p ON p.product_id = oi.product_id "
        "WHERE oi.order_id = %s ORDER BY oi.order_item_id", (order_id,))
    return [OrderItem.from_row(r) for r in rows]


def update_status(order_id, new_status):
    con = get_connection()
    cur = con.cursor()
    try:
        cur.callproc("cap_nhat_trang_thai_don_hang", [order_id, new_status])
        con.commit()
    finally:
        cur.close()
        con.close()


def stats():
    return _query(
        "SELECT "
        "(SELECT COUNT(*) FROM products WHERE product_status='Active') AS products, "
        "(SELECT COUNT(*) FROM customers) AS customers, "
        "(SELECT COUNT(*) FROM orders) AS orders, "
        "(SELECT COUNT(*) FROM orders WHERE order_status='Pending') AS pending, "
        "(SELECT COALESCE(SUM(total_amount),0) FROM orders "
        " WHERE payment_status='Paid') AS revenue")[0]


# ---------- Khách hàng ----------
def get_by_customer(customer_id):
    rows = _query("SELECT * FROM orders WHERE customer_id = %s "
                  "ORDER BY order_date DESC, order_id DESC", (customer_id,))
    return [Order.from_row(r) for r in rows]


def create_from_cart(customer_id, address, payment_method, cart):
    """Tạo đơn từ giỏ hàng. cart: {product_id (int): số lượng}. Trả về mã đơn.

    Mọi bước nằm trong MỘT transaction: tạo đơn rồi thêm từng dòng order_items.
    Trigger (trg_order_items_*) kiểm tra tồn kho, trừ kho và cộng total_amount.
    Lỗi ở bất kỳ bước nào (hết hàng, ngừng kinh doanh...) -> rollback tất cả.

    Ném ValueError nếu dữ liệu đầu vào sai, mysql.connector.Error nếu DB từ chối.
    """
    address = (address or "").strip()
    payment_method = (payment_method or "Cash").strip() or "Cash"

    if not cart:
        raise ValueError("Giỏ hàng đang trống")
    if any(qty <= 0 for qty in cart.values()):
        raise ValueError("Số lượng sản phẩm không hợp lệ")
    if payment_method not in ("Cash", "Online"):
        raise ValueError("Phương thức thanh toán không hợp lệ")

    con = get_connection()
    cur = con.cursor()
    try:
        con.start_transaction()

        # Khóa dòng khách hàng, lấy địa chỉ trong hồ sơ
        cur.execute("SELECT address FROM customers "
                    "WHERE customer_id = %s FOR UPDATE", (customer_id,))
        row = cur.fetchone()
        if row is None:
            raise ValueError("Không tìm thấy thông tin khách hàng")
        profile_address = (row[0] or "").strip()

        if not address:
            address = profile_address
        if not address:
            raise ValueError("Vui lòng nhập địa chỉ giao hàng")

        # Hồ sơ chưa có địa chỉ thì lưu địa chỉ này lại cho lần sau
        if not profile_address:
            cur.execute("UPDATE customers SET address = %s "
                        "WHERE customer_id = %s", (address, customer_id))

        # Tạo đơn
        cur.execute(
            "INSERT INTO orders (customer_id, shipping_address, total_amount, "
            "payment_method) VALUES (%s, %s, 0, %s)",
            (customer_id, address, payment_method))
        order_id = cur.lastrowid

        # Thêm sản phẩm; sắp xếp theo product_id để các giao dịch khóa dòng
        # theo cùng một thứ tự, tránh deadlock
        for product_id in sorted(cart):
            cur.execute(
                "INSERT INTO order_items (order_id, product_id, quantity) "
                "VALUES (%s, %s, %s)", (order_id, product_id, cart[product_id]))

        con.commit()
        return order_id
    except Exception:
        con.rollback()
        raise
    finally:
        cur.close()
        con.close()
