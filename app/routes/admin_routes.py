from datetime import datetime
from decimal import Decimal, InvalidOperation

import mysql.connector
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash)

from ..models import OrderStatus
from ..repositories import order_repo, product_repo
from ..services.auth import yeu_cau_vai_tro

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

STATUS_VI = {
    "Pending": "Chờ xác nhận", "Confirmed": "Đã xác nhận",
    "Shipping": "Đang giao", "Completed": "Hoàn thành", "Cancelled": "Đã hủy",
}
ACTION_VI = {
    "Confirmed": "Xác nhận", "Shipping": "Giao hàng",
    "Completed": "Hoàn thành", "Cancelled": "Hủy đơn",
}
PAYMENT_VI = {"Unpaid": "Chưa thanh toán", "Paid": "Đã thanh toán",
              "Refunded": "Đã hoàn tiền"}


def _loi_db(e):
    """Thông báo lỗi từ MySQL (SIGNAL trong procedure hoặc ràng buộc)."""
    return e.msg or str(e)


def _doc_gia(chuoi):
    try:
        return Decimal(chuoi.replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        return None


# ---------------- Tổng quan ----------------
@admin_bp.route("/")
@yeu_cau_vai_tro("Admin")
def dashboard():
    return render_template(
        "admin_dashboard.html",
        stats=order_repo.stats(),
        low_stock=product_repo.get_low_stock(),
        recent=order_repo.get_all()[:5],
        STATUS_VI=STATUS_VI,
    )


# ---------------- Sản phẩm ----------------
@admin_bp.route("/products")
@yeu_cau_vai_tro("Admin")
def products():
    keyword = request.args.get("q", "").strip()
    return render_template("admin_products.html",
                           products=product_repo.get_all(keyword or None),
                           keyword=keyword)


@admin_bp.route("/products/new", methods=["GET", "POST"])
@yeu_cau_vai_tro("Admin")
def product_new():
    categories = product_repo.get_categories(only_active=False)
    if request.method == "GET":
        return render_template("admin_product_form.html", product=None,
                               categories=categories, form={})

    form = {k: request.form.get(k, "").strip()
            for k in ("name", "price", "category", "quantity")}
    price = _doc_gia(form["price"])
    try:
        quantity = int(form["quantity"] or 0)
    except ValueError:
        quantity = None

    if not (form["name"] and form["category"]):
        loi = "Vui lòng nhập tên và danh mục"
    elif price is None or price <= 0:
        loi = "Giá phải là số lớn hơn 0"
    elif quantity is None or quantity < 0:
        loi = "Số lượng phải là số nguyên không âm"
    else:
        try:
            product_repo.create(form["name"], price, form["category"], quantity)
            flash(f"Đã thêm sản phẩm “{form['name']}”")
            return redirect(url_for("admin.products"))
        except mysql.connector.Error as e:
            loi = _loi_db(e)
    return render_template("admin_product_form.html", product=None,
                           categories=categories, form=form, loi=loi)


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@yeu_cau_vai_tro("Admin")
def product_edit(product_id):
    product = product_repo.get_by_id(product_id)
    if product is None:
        flash("Sản phẩm không tồn tại")
        return redirect(url_for("admin.products"))
    categories = product_repo.get_categories(only_active=False)

    if request.method == "GET":
        form = {"name": product.product_name, "price": f"{product.price:.0f}",
                "category": product.category}
        return render_template("admin_product_form.html", product=product,
                               categories=categories, form=form)

    form = {k: request.form.get(k, "").strip()
            for k in ("name", "price", "category")}
    price = _doc_gia(form["price"])
    if not (form["name"] and form["category"]):
        loi = "Vui lòng nhập tên và danh mục"
    elif price is None or price <= 0:
        loi = "Giá phải là số lớn hơn 0"
    else:
        try:
            product_repo.update(product_id, form["name"], price, form["category"])
            flash("Đã cập nhật sản phẩm")
            return redirect(url_for("admin.products"))
        except mysql.connector.Error as e:
            loi = _loi_db(e)
    return render_template("admin_product_form.html", product=product,
                           categories=categories, form=form, loi=loi)


@admin_bp.route("/products/<int:product_id>/stock", methods=["POST"])
@yeu_cau_vai_tro("Admin")
def product_stock(product_id):
    mode = request.form.get("mode")          # "add" = nhập thêm, "set" = đặt lại
    try:
        qty = int(request.form.get("quantity", ""))
    except ValueError:
        flash("Số lượng phải là số nguyên")
        return redirect(url_for("admin.products"))
    try:
        if mode == "add":
            product_repo.add_stock(product_id, qty)
            flash(f"Đã nhập thêm {qty} sản phẩm")
        else:
            product_repo.set_stock(product_id, qty)
            flash(f"Đã đặt tồn kho = {qty}")
    except ValueError as e:
        flash(str(e))
    except mysql.connector.Error as e:
        flash(_loi_db(e))
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/<int:product_id>/toggle", methods=["POST"])
@yeu_cau_vai_tro("Admin")
def product_toggle(product_id):
    product = product_repo.get_by_id(product_id)
    if product is None:
        flash("Sản phẩm không tồn tại")
    else:
        try:
            product_repo.set_active(product_id, not product.is_active())
            flash("Đã ngừng kinh doanh" if product.is_active()
                  else "Đã kinh doanh lại")
        except mysql.connector.Error as e:
            flash(_loi_db(e))
    return redirect(url_for("admin.products"))


# ---------------- Đơn hàng ----------------
@admin_bp.route("/orders")
@yeu_cau_vai_tro("Admin")
def orders():
    status = request.args.get("status", "").strip()
    if status not in STATUS_VI:
        status = ""
    rows = order_repo.get_all(status or None)
    for r in rows:
        r["actions"] = [s.value for s in OrderStatus if r["order"].can_change_to(s)]
    return render_template("admin_orders.html", rows=rows, status=status,
                           STATUS_VI=STATUS_VI, ACTION_VI=ACTION_VI,
                           PAYMENT_VI=PAYMENT_VI)


@admin_bp.route("/orders/<int:order_id>")
@yeu_cau_vai_tro("Admin")
def order_detail(order_id):
    data = order_repo.get_by_id(order_id)
    if data is None:
        flash("Đơn hàng không tồn tại")
        return redirect(url_for("admin.orders"))
    data["actions"] = [s.value for s in OrderStatus
                       if data["order"].can_change_to(s)]
    return render_template("admin_order_detail.html", data=data,
                           STATUS_VI=STATUS_VI, ACTION_VI=ACTION_VI,
                           PAYMENT_VI=PAYMENT_VI)


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@yeu_cau_vai_tro("Admin")
def order_status(order_id):
    new_status = request.form.get("new_status", "")
    try:
        order_repo.update_status(order_id, new_status)
        flash(f"Đơn #{order_id}: {STATUS_VI.get(new_status, new_status)}")
    except mysql.connector.Error as e:
        flash(_loi_db(e))
    return redirect(request.referrer or url_for("admin.orders"))

# ---------------- Báo cáo doanh thu ----------------
GROUP_VI = {"DAY": "Theo ngày", "MONTH": "Theo tháng", "YEAR": "Theo năm"}
 
 
def _doc_ngay(chuoi):
    """'YYYY-MM-DD' -> date; rỗng/sai định dạng -> None (không lọc)."""
    try:
        return datetime.strptime(chuoi.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None
 
 
@admin_bp.route("/reports")
@yeu_cau_vai_tro("Admin")
def reports():
    group = request.args.get("group", "MONTH").upper()
    if group not in GROUP_VI:
        group = "MONTH"
    date_from = _doc_ngay(request.args.get("from", ""))
    date_to = _doc_ngay(request.args.get("to", ""))
 
    revenue, sellers, status_stats = [], [], []
    try:
        revenue = order_repo.revenue_report(group, date_from, date_to)
        sellers = order_repo.best_sellers(10, date_from, date_to)
        status_stats = order_repo.order_status_stats(date_from, date_to)
    except mysql.connector.Error as e:
        flash(_loi_db(e))
 
    return render_template(
        "admin_reports.html",
        group=group, GROUP_VI=GROUP_VI,
        date_from=date_from.isoformat() if date_from else "",
        date_to=date_to.isoformat() if date_to else "",
        revenue=revenue, sellers=sellers, status_stats=status_stats,
        total_revenue=sum((r["doanh_thu"] for r in revenue), Decimal(0)),
        total_orders=sum(r["so_don"] for r in revenue),
        STATUS_VI=STATUS_VI,
    )
 

