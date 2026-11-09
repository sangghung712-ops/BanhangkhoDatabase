from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class OrderItem:
    order_id: int
    product_id: int
    quantity: int
    order_item_id: Optional[int] = None
    # Chỉ có khi bảng order_items đã thêm cột unit_price
    unit_price: Optional[Decimal] = None
    # Tên sản phẩm khi JOIN để hiển thị (không phải cột của bảng)
    product_name: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> "OrderItem":
        price = row.get("unit_price") if row.get("unit_price") is not None else row.get("price")
        return cls(
            order_item_id=row.get("order_item_id"),
            order_id=row["order_id"],
            product_id=row["product_id"],
            quantity=row["quantity"],
            unit_price=Decimal(price) if price is not None else None,
            product_name=row.get("product_name"),
        )

    def validate(self) -> None:
        if self.quantity <= 0:
            raise ValueError("Số lượng phải lớn hơn 0")

    @property
    def subtotal(self) -> Decimal:
        return (self.unit_price or Decimal(0)) * self.quantity

    def to_dict(self) -> dict:
        return {
            "order_item_id": self.order_item_id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "unit_price": str(self.unit_price) if self.unit_price is not None else None,
            "subtotal": str(self.subtotal),
        }