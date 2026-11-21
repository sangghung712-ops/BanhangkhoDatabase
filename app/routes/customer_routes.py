import os
from decimal import Decimal

import mysql.connector
from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, session, url_for, current_app)

from ..labels import PAYMENT_METHOD_VI, PAYMENT_VI, STATUS_VI, dich_loi
from ..models import OrderStatus, PaymentMethod, PaymentStatus
from ..repositories import customer_repo, order_repo, product_repo
from ..services import image_upload, vietqr
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
    """Lấy đơn (kèm items) nếu đúng của khách đang đăng nhập, ngược lại None."""
    return order_repo.get_for_customer(order_id, _customer().customer_id)


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
@customer_bp.route("/shop/product/<int:product_id>")
@yeu_cau_vai_tro("Customer")
def product_detail(product_id):
    product = product_repo.get_by_id(product_id)
    if product is None or not product.is_active():
        flash("Sản phẩm không tồn tại hoặc đã ngừng kinh doanh")
        return redirect(url_for("customer.shop"))
    related = product_repo.get_related(product.product_id, product.category)
    return render_template("product_detail.html", product=product,
                           related=related)

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
            if form["payment_method"] == "Online":
                return redirect(url_for("customer.order_pay", order_id=order_id))
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
    order = _order_cua_toi(order_id)
    if order is None:
        flash("Không tìm thấy đơn hàng")
        return redirect(url_for("customer.my_orders"))
    return render_template("my_order_detail.html", order=order,
                           STATUS_VI=STATUS_VI, PAYMENT_VI=PAYMENT_VI,
                           PAYMENT_METHOD_VI=PAYMENT_METHOD_VI)


@customer_bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
@yeu_cau_vai_tro("Customer")
def order_cancel(order_id):
    order = _order_cua_toi(order_id)
    if order is None:
        flash("Không tìm thấy đơn hàng")
        return redirect(url_for("customer.my_orders"))
    if order.order_status != OrderStatus.PENDING:
        flash("Chỉ hủy được đơn đang chờ xác nhận")
    else:
        try:
            order_repo.update_status(order_id, "Cancelled")
            flash(f"Đã hủy đơn #{order_id}")
        except mysql.connector.Error as e:
            flash(dich_loi(e.msg or str(e)))
    return redirect(url_for("customer.order_detail", order_id=order_id))

@customer_bp.route("/orders/<int:order_id>/received", methods=["POST"])
@customer_bp.route("/orders/<int:order_id>/received", methods=["POST"])
@yeu_cau_vai_tro("Customer")
def order_received(order_id):
    data = _order_cua_toi(order_id)
    if data is None:
        flash("Không tìm thấy đơn hàng")
        return redirect(url_for("customer.my_orders"))

    # data có thể là dict {"order": Order, ...} hoặc chính là Order
    order = data["order"] if isinstance(data, dict) else data

    if order.order_status != OrderStatus.SHIPPING:
        flash("Chỉ xác nhận đã nhận hàng khi đơn đang được giao")
    else:
        try:
            order_repo.update_status(order_id, "Completed")
            flash(f"Cảm ơn bạn! Đơn #{order_id} đã hoàn thành")
        except mysql.connector.Error as e:
            flash(dich_loi(e.msg or str(e)))
    return redirect(url_for("customer.order_detail", order_id=order_id))

@customer_bp.app_context_processor
def inject_product_image():
    def product_image(product_id):
        folder = os.path.join(current_app.static_folder, "uploads", "products")
        name = image_upload.find_image(product_id, folder)
        if not name:
            return None
        version = int(os.path.getmtime(os.path.join(folder, name)))
        return url_for("static", filename=f"uploads/products/{name}", v=version)
    return {"product_image": product_image}

@customer_bp.route("/orders/<int:order_id>/pay")
@yeu_cau_vai_tro("Customer")
def order_pay(order_id):
    order = _don_cua_toi(order_id)
    if order is None:
        flash("Không tìm thấy đơn hàng")
        return redirect(url_for("customer.my_orders"))
    if not _can_pay(order):
        flash("Đơn này không cần hoặc không thể thanh toán chuyển khoản")
        return redirect(url_for("customer.order_detail", order_id=order_id))

    bank = vietqr.bank_config()
    if bank is None:
        flash("Cửa hàng chưa cấu hình tài khoản nhận tiền, vui lòng liên hệ cửa hàng")
        return redirect(url_for("customer.order_detail", order_id=order_id))

    noi_dung = f"DH{order.order_id}"
    try:
        payload = vietqr.build_payload(bank["bin"], bank["account"],
                                       order.total_amount, noi_dung)
        qr_svg = vietqr.qr_svg(payload)
    except Exception:          # thiếu thư viện segno hoặc cấu hình sai
        qr_svg = None
    return render_template("payment_qr.html", order=order, bank=bank,
                           noi_dung=noi_dung, qr_svg=qr_svg)
def _don_cua_toi(order_id):
    """Trả về Order nếu đúng của khách đang đăng nhập, ngược lại None."""
    customer = _customer()
    data = order_repo.get_by_id(order_id)
    order = data["order"] if isinstance(data, dict) else data
    if order is None or order.customer_id != customer.customer_id:
        return None
    return order


def _can_pay(order):
    return (order.payment_method == PaymentMethod.ONLINE
            and order.payment_status == PaymentStatus.UNPAID
            and order.order_status in (OrderStatus.PENDING,
                                       OrderStatus.CONFIRMED,
                                       OrderStatus.SHIPPING))


@customer_bp.route("/orders/<int:order_id>/pay/result", methods=["POST"])
@yeu_cau_vai_tro("Customer")
def order_pay_result(order_id):
    order = _don_cua_toi(order_id)
    if order is None:
        flash("Không tìm thấy đơn hàng")
        return redirect(url_for("customer.my_orders"))

    result = request.form.get("result")
    if result == "success":
        if order_repo.mark_paid(order_id):
            flash(f"Thanh toán thành công đơn #{order_id}!")
        else:
            flash("Không thể thanh toán đơn này (đã thanh toán hoặc đã hủy)")
    elif result == "fail":
        flash("Thanh toán thất bại. Bạn có thể thử lại bất cứ lúc nào.")
    else:
        flash("Bạn đã hủy thanh toán. Đơn vẫn được giữ, bạn có thể thanh toán sau.")
    return redirect(url_for("customer.order_detail", order_id=order_id))