from flask import (Blueprint, render_template, request, redirect,
                   session, url_for, flash)
from ..services.auth import dang_nhap, yeu_cau_vai_tro, dang_ky

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def trang_chu():
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        mat_khau = request.form.get("password", "")
        user = dang_nhap(username, mat_khau)
        if user:
            session.clear()
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            if user["role"] == "Admin":
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("customer.shop"))

        return render_template("login.html", loi="Sai tên đăng nhập hoặc mật khẩu")

    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", form={})

    f = {k: request.form.get(k, "").strip()
         for k in ("username", "name", "email", "phone", "address")}
    mat_khau = request.form.get("password", "")
    nhap_lai = request.form.get("confirm_password", "")

    if not (f["username"] and mat_khau and f["name"] and f["email"] and f["phone"]):
        loi = "Vui lòng nhập đầy đủ các mục bắt buộc"
    elif mat_khau != nhap_lai:
        loi = "Mật khẩu nhập lại không khớp"
    else:
        loi = dang_ky(f["username"], mat_khau, f["name"],
                      f["email"], f["phone"], f["address"])
        if loi is None:
            flash("Đăng ký thành công, hãy đăng nhập")
            return redirect(url_for("auth.login"))

    return render_template("register.html", loi=loi, form=f)

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
