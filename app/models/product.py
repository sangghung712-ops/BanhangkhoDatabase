from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from .enums import ProductStatus


@dataclass
class Product:
    product_name: str
    price: Decimal
    category: str
    quantity: int = 0
    product_status: ProductStatus = ProductStatus.ACTIVE
    product_id: Optional[int] = None

    @classmethod
    def from_row(cls, row: dict) -> "Product":
        return cls(
            product_id=row["product_id"],
            product_name=row["product_name"],
            price=Decimal(row["price"]),
            category=row["category"],
            quantity=row["quantity"],
            product_status=ProductStatus(row["product_status"]),
        )

    def validate(self) -> None:
        if not self.product_name or not self.product_name.strip():
            raise ValueError("Tên sản phẩm không được để trống")
        if self.price is None or Decimal(self.price) <= 0:
            raise ValueError("Giá phải lớn hơn 0")
        if self.quantity is None or self.quantity < 0:
            raise ValueError("Số lượng tồn kho không hợp lệ")

    def is_active(self) -> bool:
        return self.product_status == ProductStatus.ACTIVE

    def can_sell(self, qty: int) -> bool:
        return self.is_active() and 0 < qty <= self.quantity

    def add_stock(self, qty: int) -> None:
        if qty <= 0:
            raise ValueError("Số lượng nhập phải lớn hơn 0")
        self.quantity += qty

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "price": str(self.price),
            "category": self.category,
            "quantity": self.quantity,
            "product_status": self.product_status.value,
        }