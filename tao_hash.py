import hashlib, os, getpass

mat_khau = getpass.getpass("Nhập mật khẩu admin: ")
salt = os.urandom(16)
hash_ = hashlib.pbkdf2_hmac("sha256", mat_khau.encode(), salt, 200_000)

print("admin_salt=" + salt.hex())
print("admin_hash=" + hash_.hex())