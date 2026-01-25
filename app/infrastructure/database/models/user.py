import re
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.enums.payment_methods import PaymentMethod
from app.infrastructure.database.enums.user_roles import UserRole
from app.infrastructure.database.models.base_model import Base
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

if TYPE_CHECKING:
    from app.infrastructure.database.models.cart import CartModel
    from app.infrastructure.database.models.delivery_order import DeliveryOrderModel


class UserModel(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True
    )
    username: Mapped[str | None] = mapped_column(String(32))
    first_name: Mapped[str | None] = mapped_column(String(64))
    last_name: Mapped[str | None] = mapped_column(String(64))
    language_code: Mapped[str | None] = mapped_column(String(10), default="ru")
    role: Mapped[UserRole] = mapped_column(PgEnum(UserRole, name="user_role"), default=UserRole.UNKNOWN)
    is_active: Mapped[bool] = mapped_column(default=True)
    phone_number: Mapped[str | None] = mapped_column(String(20))

    preferred_bank: Mapped[PaymentMethod | None] = mapped_column(
        PgEnum(PaymentMethod, name="payment_method"),
        default=PaymentMethod.ALFA
    )

    # Relationships
    carts: Mapped[list["CartModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="CartModel.created_at.desc()"
    )
    created_orders: Mapped[list["DeliveryOrderModel"]] = relationship(
        back_populates="creator",
        foreign_keys="[DeliveryOrderModel.creator_id]",
        order_by="DeliveryOrderModel.created_at.desc()"
    )

    assigned_orders: Mapped[list["DeliveryOrderModel"]] = relationship(
        back_populates="delivery_person",
        foreign_keys="[DeliveryOrderModel.delivery_person_id]",
        order_by="DeliveryOrderModel.created_at.desc()"
    )

    @property
    def full_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def mention(self) -> str:
        if self.username:
            return f"@{self.username}"
        return f'<a href="tg://user?id={self.telegram_id}">{self.full_name}</a>'

    def __repr__(self) -> str:
        return f"User(id={self.id}, username=@{self.username}, role={self.role.value})"
