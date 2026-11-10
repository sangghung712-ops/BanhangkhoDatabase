from decimal import Decimal

import mysql.connector
from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, session, url_for)

from ..labels import PAYMENT_METHOD_VI, PAYMENT_VI, STATUS_VI, dich_loi
from ..models import OrderStatus
from ..repositories import customer_repo, order_repo, product_repo
from ..services.auth import yeu_cau_vai_tro

customer_bp = Blueprint("customer", __name__)


# ---------------- Tiện ích ----------------
@customer_bp.app_context_processor
def inject_cart_count():
    """Số lượng trong giỏ, dùng cho thanh điều hướng ở mọi trang khách."""
    if session.get("role") == "Customer":
        return {"cart_count": sum(session.get("cart", {}).values())}
    return {}


def _cart() -> dict:
    """Giỏ hàng lưu trong session: {product_id (chuỗi): số lượng}."""
    return session.setdefault("cart", {})


def _cart_items():
    """Danh sách dòng trong giỏ + tổng tiền; tự bỏ sản phẩm đã ngừng bán."""
    cart = _cart()
    items, total = [], Decimal(0)
    for pid, qty in list(cart.items()):
        product = product_repo.get_by_id(int(pid))
        if not product or not product.is_active():
            cart.pop(pid)
            session.modified = True
            continue
        subtotal = product.price * qty
        total += subtotal
        items.append({"product": product, "quantity": qty, "subtotal": subtotal})
    return items, total


def _customer():
    customer = customer_repo.get_by_user_id(session.get("user_id"))
    if customer is None:
        abort(403)
    return customer


def _order_cua_toi(order_id):
    """Lấy đơn nếu đúng của khách đang đăng nhập, ngược lại trả None."""
    customer = _customer()
    data = order_repo.get_by_id(order_id)
    if data is None or data["order"].customer_id != customer.customer_id:
        return None
    return data


# ---------------- Sản phẩm & giỏ hàng ----------------
@customer_bp.route("/shop")
@yeu_cau_vai_tro("Customer")
def shop():
    keyword = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    products = product_repo.get_active(keyword or None, category or None)
    return render_template("shop.html", products=products,
                           categories=product_repo.get_categories(),
                           keyword=keyword, category=category)


@customer_bp.route("/cart/add/<int:product_id>", methods=["POST"])
@yeu_cau_vai_tro("Customer")
def cart_add(product_id):
    product = product_repo.get_by_id(product_id)
    try:
        qty = max(1, int(request.form.get("quantity", 1)))
    except ValueError:
        qty = 1

    cart = _cart()
    if not product or not product.is_active():
        flash("Sản phẩm không còn kinh doanh")
    else:
        new_qty = cart.get(str(product_id), 0) + qty
        if new_qty > product.quantity:
            flash(f"Chỉ còn {product.quantity} sản phẩm "
                  f"“{product.product_name}” trong kho")
        else:
            cart[str(product_id)] = new_qty
            session.modified = True
            flash(f"Đã thêm “{product.product_name}” vào giỏ hàng")
    return redirect(request.referrer or url_for("customer.shop"))


@customer_bp.route("/cart")
@yeu_cau_vai_tro("Customer")
def cart():
    items, total = _cart_items()
    return render_template("cart.html", items=items, total=total)


@customer_bp.route("/cart/remove/<int:product_id>", methods=["POST"])
@yeu_cau_vai_tro("Customer")
def cart_remove(product_id):
    _cart().pop(str(product_id), None)
    session.modified = True
    return redirect(url_for("customer.cart"))


# ---------------- Đặt hàng ----------------
@customer_bp.route("/checkout", methods=["GET", "POST"])
@yeu_cau_vai_tro("Customer")
def checkout():
    items, total = _cart_items()
    if not items:
        flash("Giỏ hàng đang trống")
        return redirect(url_for("customer.shop"))

    customer = _customer()

    if request.method == "GET":
        form = {"shipping_address": customer.address or "", "payment_method": "Cash"}
        return render_template("checkout.html", items=items, total=total,
                               customer=customer, form=form)

    form = {
        "shipping_address": request.form.get("shipping_address", "").strip(),
        "payment_method": request.form.get("payment_method", "Cash"),
    }
    loi = None
    if not form["shipping_address"]:
        loi = "Vui lòng nhập địa chỉ giao hàng"
    elif form["payment_method"] not in PAYMENT_METHOD_VI:
        loi = "Phương thức thanh toán không hợp lệ"
    else:
        cart_ids = {int(pid): qty for pid, qty in _cart().items()}
        try:
            order_id = order_repo.create_from_cart(
                customer.customer_id, form["shipping_address"],
                form["payment_method"], cart_ids)
        except mysql.connector.Error as e:
            loi = dich_loi(e.msg or str(e))
        except ValueError as e:
            loi = str(e)
        else:
            session["cart"] = {}
            session.modified = True
            flash(f"Đặt hàng thành công! Mã đơn của bạn là #{order_id}")
            return redirect(url_for("customer.order_detail", order_id=order_id))

    return render_template("checkout.html", items=items, total=total,
                           customer=customer, form=form, loi=loi)


# ---------------- Đơn hàng của tôi ----------------
@customer_bp.route("/orders")
@yeu_cau_vai_tro("Customer")
def my_orders():
    orders = order_repo.get_by_customer(_customer().customer_id)
    return render_template("my_orders.html", orders=orders,
                           STATUS_VI=STATUS_VI, PAYMENT_VI=PAYMENT_VI)


@customer_bp.route("/orders/<int:order_id>")
@yeu_cau_vai_tro("Customer")
def order_detail(order_id):
    data = _order_cua_toi(order_id)
    if data is None:
        flash("Không tìm thấy đơn hàng")
        return redirect(url_for("customer.my_orders"))
    return render_template("my_order_detail.html", order=data["order"],
                           STATUS_VI=STATUS_VI, PAYMENT_VI=PAYMENT_VI,
                           PAYMENT_METHOD_VI=PAYMENT_METHOD_VI)


@customer_bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
@yeu_cau_vai_tro("Customer")
def order_cancel(order_id):
    data = _order_cua_toi(order_id)
    if data is None:
        flash("Không tìm thấy đơn hàng")
        return redirect(url_for("customer.my_orders"))
    if data["order"].order_status != OrderStatus.PENDING:
        flash("Chỉ hủy được đơn đang chờ xác nhận")
    else:
        try:
            order_repo.update_status(order_id, "Cancelled")
            flash(f"Đã hủy đơn #{order_id}")
        except mysql.connector.Error as e:
            flash(dich_loi(e.msg or str(e)))
    return redirect(url_for("customer.order_detail", order_id=order_id))
