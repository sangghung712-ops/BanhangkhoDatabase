import re
from dataclasses import dataclass
from typing import Optional

PHONE_RE = re.compile(r"^0[0-9]{9}$")
EMAIL_RE = re.compile(r"^.+@.+\..+$")


@dataclass
class Customer:
    user_id: int
    name: str
    email: str
    phone: str
    address: Optional[str] = None
    customer_id: Optional[int] = None

    @classmethod
    def from_row(cls, row: dict) -> "Customer":
        return cls(
            customer_id=row["customer_id"],
            user_id=row["user_id"],
            name=row["name"],
            email=row["email"],
            phone=row["phone"],
            address=row.get("address"),
        )

    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Tên không được để trống")
        if not EMAIL_RE.match(self.email or ""):
            raise ValueError("Email không hợp lệ")
        if not PHONE_RE.match(self.phone or ""):
            raise ValueError("Số điện thoại phải gồm 10 chữ số, bắt đầu bằng 0")

    def has_address(self) -> bool:
        return bool(self.address and self.address.strip())

    def to_dict(self) -> dict:
        return {
            "customer_id": self.customer_id,
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
        }