from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from .enums import (ORDER_TRANSITIONS, OrderStatus, PaymentMethod,
                    PaymentStatus)
from .order_item import OrderItem


@dataclass
class Order:
    customer_id: int
    shipping_address: str
    payment_method: PaymentMethod = PaymentMethod.CASH
    order_status: OrderStatus = OrderStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    total_amount: Decimal = Decimal(0)
    order_date: Optional[datetime] = None
    shipping_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    order_id: Optional[int] = None
    items: List[OrderItem] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: dict) -> "Order":
        return cls(
            order_id=row["order_id"],
            customer_id=row["customer_id"],
            order_date=row["order_date"],
            shipping_date=row.get("shipping_date"),
            payment_date=row.get("payment_date"),
            order_status=OrderStatus(row["order_status"]),
            shipping_address=row["shipping_address"],
            total_amount=Decimal(row["total_amount"]),
            payment_method=PaymentMethod(row["payment_method"]),
            payment_status=PaymentStatus(row["payment_status"]),
        )

    def can_change_to(self, new_status: OrderStatus) -> bool:
        if new_status == OrderStatus.COMPLETED:
            if (self.payment_method == PaymentMethod.ONLINE
                    and self.payment_status != PaymentStatus.PAID):
                return False
        return new_status in ORDER_TRANSITIONS[self.order_status]

    def can_add_items(self) -> bool:
        return self.order_status == OrderStatus.PENDING

    def compute_total(self) -> Decimal:
        return sum((i.subtotal for i in self.items), Decimal(0))

    def to_dict(self) -> dict:
        fmt = lambda d: d.isoformat(sep=" ") if d else None
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "order_date": fmt(self.order_date),
            "shipping_date": fmt(self.shipping_date),
            "payment_date": fmt(self.payment_date),
            "order_status": self.order_status.value,
            "shipping_address": self.shipping_address,
            "total_amount": str(self.total_amount),
            "payment_method": self.payment_method.value,
            "payment_status": self.payment_status.value,
            "items": [i.to_dict() for i in self.items],
        }