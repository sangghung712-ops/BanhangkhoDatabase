import os
import hashlib
import hmac
from functools import wraps

from dotenv import load_dotenv
from flask import session, redirect, url_for, abort

from app.db import get_connection

import mysql.connector
from app.models import Customer
load_dotenv(override=True)


def la_admin(username: str, mat_khau: str) -> bool:
    admin_username = os.getenv("admin_username")
    admin_salt = os.getenv("admin_salt")
    admin_hash = os.getenv("admin_hash")
    if not (admin_username and admin_salt and admin_hash):
        return False                      # thiếu cấu hình .env thì không cho vào
    if username != admin_username:
        return False

    salt = bytes.fromhex(admin_salt)
    hash_nhap = hashlib.pbkdf2_hmac("sha256", mat_khau.encode(), salt, 200_000)
    hash_goc = bytes.fromhex(admin_hash)
    return hmac.compare_digest(hash_nhap, hash_goc)


def kiem_tra_user_trong_db(username: str, mat_khau: str):
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT user_id, user_name, user_role FROM users "
            "WHERE user_name = %s AND user_password = %s",
            (username, mat_khau),
        )
        row = cur.fetchone()
    finally:
        conn.close()

    if row and row["user_role"] == "Customer":
        return {"user_id": row["user_id"], "username": row["user_name"], "role": "Customer"}
    return None


def dang_nhap(username: str, mat_khau: str):
    """Đúng: trả về dict {user_id, username, role}. Sai: trả về None."""
    if la_admin(username, mat_khau):
        return {"user_id": None, "username": username, "role": "Admin"}
    return kiem_tra_user_trong_db(username, mat_khau)


def yeu_cau_vai_tro(role: str):
    """Decorator: chưa đăng nhập thì về /login, sai quyền thì báo 403."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "role" not in session:
                return redirect(url_for("auth.login"))
            if session["role"] != role:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator
def dang_ky(username, mat_khau, ten, email, sdt, dia_chi):
    """Trả về None nếu thành công, hoặc chuỗi báo lỗi."""
    # Tên đăng nhập của admin nằm trong .env, không cho khách đăng ký trùng
    if username == os.getenv("admin_username"):
        return "Tên đăng nhập đã được sử dụng"

    try:
        Customer(user_id=0, name=ten, email=email, phone=sdt).validate()
    except ValueError as e:
        return str(e)

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.callproc("dang_ky_khach_hang",
                     [username, mat_khau, ten, email, sdt, dia_chi or None])
        conn.commit()
        return None
    except mysql.connector.Error as e:
        if e.errno == 1062:
            return "Tên đăng nhập, email hoặc số điện thoại đã được sử dụng"
        return e.msg
    finally:
        cur.close()
        conn.close()