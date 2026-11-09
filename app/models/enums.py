from enum import Enum


class UserRole(str, Enum):
    ADMIN = "Admin"
    CUSTOMER = "Customer"


class ProductStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class OrderStatus(str, Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    SHIPPING = "Shipping"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class PaymentMethod(str, Enum):
    CASH = "Cash"
    ONLINE = "Online"


class PaymentStatus(str, Enum):
    UNPAID = "Unpaid"
    PAID = "Paid"
    REFUNDED = "Refunded"


# Chuyển trạng thái hợp lệ (khớp với procedure cap_nhat_trang_thai_don_hang)
ORDER_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.SHIPPING, OrderStatus.CANCELLED},
    OrderStatus.SHIPPING: {OrderStatus.COMPLETED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}