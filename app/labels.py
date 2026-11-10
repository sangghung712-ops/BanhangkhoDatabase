"""Nhãn tiếng Việt dùng chung cho giao diện."""

STATUS_VI = {
    "Pending": "Chờ xác nhận", "Confirmed": "Đã xác nhận",
    "Shipping": "Đang giao", "Completed": "Hoàn thành", "Cancelled": "Đã hủy",
}
PAYMENT_VI = {
    "Unpaid": "Chưa thanh toán", "Paid": "Đã thanh toán", "Refunded": "Đã hoàn tiền",
}
PAYMENT_METHOD_VI = {"Cash": "Tiền mặt (khi nhận hàng)", "Online": "Thanh toán trực tuyến"}

# Thông báo lỗi từ procedure/trigger (không dấu) -> tiếng Việt
LOI_VI = {
    "Gio hang trong": "Giỏ hàng đang trống",
    "Gio hang khong hop le": "Giỏ hàng không hợp lệ",
    "Khong du hang trong kho": "Có sản phẩm không đủ hàng trong kho, vui lòng giảm số lượng",
    "San pham da ngung kinh doanh": "Có sản phẩm đã ngừng kinh doanh, vui lòng xóa khỏi giỏ",
    "San pham khong ton tai": "Có sản phẩm không còn tồn tại",
    "Chua co dia chi giao hang": "Vui lòng nhập địa chỉ giao hàng",
    "Phuong thuc thanh toan khong hop le": "Phương thức thanh toán không hợp lệ",
    "Khach hang khong ton tai": "Không tìm thấy thông tin khách hàng",
    "Khong the chuyen sang trang thai nay": "Đơn hàng không thể hủy ở trạng thái hiện tại",
}


def dich_loi(msg: str) -> str:
    return LOI_VI.get(msg, msg)
