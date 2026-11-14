"""Lưu ảnh sản phẩm trên đĩa, KHÔNG cần thêm cột nào vào database.

Mỗi sản phẩm có tối đa một ảnh, đặt tên theo mã sản phẩm:
    app/static/uploads/products/<product_id>.<png|jpg|gif|webp>

- Kiểm tra bằng NỘI DUNG file (chữ ký đầu file), không tin đuôi file người dùng gửi.
- Không nhận SVG vì SVG có thể chứa mã script.
- Tên file do hệ thống tự đặt nên không lo tên file độc hại (../, ký tự lạ).
"""
import os

MAX_SIZE = 2 * 1024 * 1024  # 2 MB
EXTENSIONS = (".png", ".jpg", ".gif", ".webp")


def _detect_ext(data: bytes):
    """Nhận dạng loại ảnh theo chữ ký đầu file; trả về đuôi file hoặc None."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def read_image(file):
    """Đọc và kiểm tra ảnh tải lên (CHƯA ghi ra đĩa).

    file: đối tượng FileStorage của Flask (request.files.get("image")).
    Trả về (dữ liệu, đuôi file), hoặc None nếu người dùng không chọn ảnh.
    Ném ValueError (thông báo tiếng Việt) nếu ảnh không hợp lệ.
    """
    if file is None or not file.filename:
        return None
    data = file.read(MAX_SIZE + 1)
    if len(data) > MAX_SIZE:
        raise ValueError("Ảnh quá lớn, tối đa 2 MB")
    ext = _detect_ext(data)
    if ext is None:
        raise ValueError("Chỉ chấp nhận ảnh PNG, JPG, GIF hoặc WEBP")
    return data, ext


def delete_images(product_id, upload_dir):
    """Xóa mọi ảnh của sản phẩm (mọi đuôi file)."""
    for ext in EXTENSIONS:
        try:
            os.remove(os.path.join(upload_dir, f"{int(product_id)}{ext}"))
        except OSError:
            pass


def store_image(product_id, data, ext, upload_dir):
    """Ghi ảnh của sản phẩm, thay thế ảnh cũ (kể cả khác đuôi file)."""
    os.makedirs(upload_dir, exist_ok=True)
    delete_images(product_id, upload_dir)
    name = f"{int(product_id)}{ext}"
    with open(os.path.join(upload_dir, name), "wb") as f:
        f.write(data)
    return name


def find_image(product_id, upload_dir):
    """Tên file ảnh của sản phẩm, hoặc None nếu chưa có."""
    for ext in EXTENSIONS:
        name = f"{int(product_id)}{ext}"
        if os.path.isfile(os.path.join(upload_dir, name)):
            return name
    return None