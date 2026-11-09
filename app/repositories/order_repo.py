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