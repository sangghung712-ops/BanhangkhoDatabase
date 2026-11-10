from app.db import get_connection
from app.models import Product


def _query(sql, params=()):
    con = get_connection()
    try:
        cur = con.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        con.close()


def _call(proc, args):
    """Gọi stored procedure rồi commit. Lỗi SIGNAL của MySQL sẽ được ném ra."""
    con = get_connection()
    cur = con.cursor()
    try:
        cur.callproc(proc, args)
        con.commit()
    finally:
        cur.close()
        con.close()


# ---------- Đọc ----------
def get_active(keyword=None, category=None):
    sql = "SELECT * FROM products WHERE product_status = 'Active'"
    params = []
    if keyword:
        sql += " AND product_name LIKE %s"
        params.append(f"%{keyword}%")
    if category:
        sql += " AND category = %s"
        params.append(category)
    sql += " ORDER BY product_name"
    return [Product.from_row(r) for r in _query(sql, tuple(params))]


def get_all(keyword=None):
    """Tất cả sản phẩm (cả đã ngừng kinh doanh) cho trang admin."""
    sql = "SELECT * FROM products"
    params = []
    if keyword:
        sql += " WHERE product_name LIKE %s OR category LIKE %s"
        params += [f"%{keyword}%", f"%{keyword}%"]
    sql += " ORDER BY product_id DESC"
    return [Product.from_row(r) for r in _query(sql, tuple(params))]


def get_categories(only_active=True):
    sql = "SELECT DISTINCT category FROM products"
    if only_active:
        sql += " WHERE product_status = 'Active'"
    sql += " ORDER BY category"
    return [r["category"] for r in _query(sql)]


def get_by_id(product_id):
    rows = _query("SELECT * FROM products WHERE product_id = %s", (product_id,))
    return Product.from_row(rows[0]) if rows else None


def get_low_stock(threshold=5, limit=5):
    rows = _query("SELECT * FROM products WHERE product_status = 'Active' "
                  "AND quantity <= %s ORDER BY quantity LIMIT %s",
                  (threshold, limit))
    return [Product.from_row(r) for r in rows]


# ---------- Ghi (qua stored procedure) ----------
def create(name, price, category, quantity):
    _call("them_san_pham", [name, price, category, quantity])


def update(product_id, name, price, category):
    _call("cap_nhat_san_pham", [product_id, name, price, category])


def set_stock(product_id, quantity):
    _call("cap_nhat_ton_kho", [product_id, quantity])


def add_stock(product_id, qty):
    """Nhập thêm hàng: dùng Product.add_stock rồi ghi tồn kho mới."""
    product = get_by_id(product_id)
    if product is None:
        raise ValueError("Sản phẩm không tồn tại")
    product.add_stock(qty)
    set_stock(product_id, product.quantity)


def set_active(product_id, active: bool):
    _call("kinh_doanh_lai_san_pham" if active else "ngung_kinh_doanh_san_pham",
          [product_id])
