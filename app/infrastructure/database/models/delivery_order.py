from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import ForeignKey, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from app.infrastructure.database.enums.order_statuses import OrderStatus
from app.infrastructure.database.enums.payment_methods import PaymentMethod
from app.infrastructure.database.models import Base
from app.infrastructure.database.models.dish import DishModel

if TYPE_CHECKING:
    from app.infrastructure.database.models.restaurant import RestaurantModel
    from app.infrastructure.database.models.user import UserModel
    from app.infrastructure.database.models.cart import CartModel


class DeliveryOrderModel(Base):
    __tablename__ = "delivery_orders"

    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    delivery_person_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[OrderStatus] = mapped_column(
        PgEnum(OrderStatus, name="order_status"), default=OrderStatus.COLLECTING
    )
    phone_number: Mapped[str | None] = mapped_column(String(20))
    payment_method: Mapped[PaymentMethod | None] = mapped_column(
        PgEnum(PaymentMethod, name="payment_method")
    )
    total_amount: Mapped[float] = mapped_column(default=0.0)
    collected_at: Mapped[datetime | None] = mapped_column()
    delivered_at: Mapped[datetime | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(String(255))  # дополнительные заметки

    # Relationships
    restaurant: Mapped["RestaurantModel"] = relationship(back_populates="orders")
    creator: Mapped["UserModel"] = relationship(
        foreign_keys=[creator_id],
        back_populates="created_orders"
    )
    delivery_person: Mapped["UserModel"] = relationship(
        foreign_keys=[delivery_person_id],
        back_populates="assigned_orders"
    )
    carts: Mapped[list["CartModel"]] = relationship(back_populates="delivery_order")

    item_associations: Mapped[list["OrderItemModel"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan"
    )

    # Many-to-many through association
    dishes: Mapped[list["DishModel"]] = relationship(
        secondary="order_items",
        back_populates="orders",
        viewonly=True
    )

    __table_args__ = (
        Index("ix_orders_status_date", "status", "created_at"),
        Index("ix_orders_restaurant_date", "restaurant_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"DeliveryOrder(id={self.id}, status={self.status.value}, total={self.total_amount})"


class OrderItemModel(Base):
    __tablename__ = "order_items"

    order_id: Mapped[int] = mapped_column(ForeignKey("delivery_orders.id"), primary_key=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id"), primary_key=True)
    quantity: Mapped[int] = mapped_column()
    price: Mapped[float] = mapped_column()
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    # Relationships
    order: Mapped["DeliveryOrderModel"] = relationship(back_populates="item_associations")
    dish: Mapped["DishModel"] = relationship(back_populates="order_associations")
    user: Mapped["UserModel"] = relationship()
