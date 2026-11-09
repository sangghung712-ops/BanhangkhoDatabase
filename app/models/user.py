from dataclasses import dataclass
from typing import Optional

from .enums import UserRole


@dataclass
class User:
    user_name: str
    user_password: str
    user_role: UserRole = UserRole.CUSTOMER
    user_id: Optional[int] = None

    @classmethod
    def from_row(cls, row: dict) -> "User":
        return cls(
            user_id=row["user_id"],
            user_name=row["user_name"],
            user_password=row["user_password"],
            user_role=UserRole(row["user_role"]),
        )

    def is_admin(self) -> bool:
        return self.user_role == UserRole.ADMIN

    def to_dict(self, include_password: bool = False) -> dict:
        data = {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_role": self.user_role.value,
        }
        if include_password:
            data["user_password"] = self.user_password
        return data