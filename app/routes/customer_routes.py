from decimal import Decimal

from flask import (Blueprint, render_template, request, redirect,
                   session, url_for, flash)

from ..repositories import product_repo
from ..services.auth import yeu_cau_vai_tro

customer_bp = Blueprint("customer", __name__)


def _cart() -> dict:
    """Giỏ hàng lưu trong session: {product_id (chuỗi): số lượng}."""
    return session.setdefault("cart", {})


def _cart_count() -> int:
    return sum(_cart().values())


@customer_bp.route("/shop")
@yeu_cau_vai_tro("Customer")
def shop():
    keyword = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    products = product_repo.get_active(keyword or None, category or None)
    return render_template(
        "shop.html",
        products=products,
        categories=product_repo.get_categories(),
        keyword=keyword,
        category=category,
        cart_count=_cart_count(),
    )


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
    cart = _cart()
    items, total = [], Decimal(0)
    for pid, qty in list(cart.items()):
        product = product_repo.get_by_id(int(pid))
        if not product or not product.is_active():
            cart.pop(pid)                 # sản phẩm đã ngừng bán thì bỏ khỏi giỏ
            session.modified = True
            continue
        subtotal = product.price * qty
        total += subtotal
        items.append({"product": product, "quantity": qty, "subtotal": subtotal})
    return render_template("cart.html", items=items, total=total,
                           cart_count=_cart_count())


@customer_bp.route("/cart/remove/<int:product_id>", methods=["POST"])
@yeu_cau_vai_tro("Customer")
def cart_remove(product_id):
    _cart().pop(str(product_id), None)
    session.modified = True
    return redirect(url_for("customer.cart"))