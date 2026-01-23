import re

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.infrastructure.database.enums.payment_methods import PaymentMethod
from app.infrastructure.database.enums.user_roles import UserRole
from app.infrastructure.database.models.base_model import Base
from sqlalchemy.dialects.postgresql import ENUM as PgEnum


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
    preferred_bank: Mapped[PaymentMethod | None] = mapped_column(PgEnum(PaymentMethod, name="payment_method"),
                                                                 default=PaymentMethod.ALFA)

    # Relationships
    carts: Mapped[list["Cart"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Cart.created_at.desc()"
    )

    created_orders: Mapped[list["DeliveryOrder"]] = relationship(
        back_populates="creator",
        foreign_keys="[DeliveryOrder.creator_id]",
        order_by="DeliveryOrder.created_at.desc()"
    )

    assigned_orders: Mapped[list["DeliveryOrder"]] = relationship(
        back_populates="delivery_person",
        foreign_keys="[DeliveryOrder.delivery_person_id]",
        order_by="DeliveryOrder.created_at.desc()"
    )

    @property
    def full_name(self) -> str:
        """Возвращает полное имя пользователя"""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def mention(self) -> str:
        """Возвращает упоминание пользователя в Telegram"""
        if self.username:
            return f"@{self.username}"
        return f'<a href="tg://user?id={self.telegram_id}">{self.full_name}</a>'

    @validates("phone_number")
    def validate_phone_number(self, key: str, phone_number: str | None) -> str | None:
        if phone_number is None:
            return None

        # Удаляем все нецифровые символы
        cleaned = re.sub(r'\D', '', phone_number)

        if len(cleaned) == 11 and cleaned.startswith(('7', '8')):
            return f'+7{cleaned[1:]}'
        elif len(cleaned) == 10:
            return f'+7{cleaned}'
        else:
            raise ValueError("Неверный формат номера телефона")

    def __repr__(self) -> str:
        return f"User(id={self.id}, username=@{self.username}, role={self.role.value})"
