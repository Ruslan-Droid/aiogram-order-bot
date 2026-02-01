from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from app.infrastructure.database.enums.cart_statuses import CartStatus
from app.infrastructure.database.models import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.user import UserModel
    from app.infrastructure.database.models.delivery_order import DeliveryOrderModel
    from app.infrastructure.database.models.restaurant import RestaurantModel
    from app.infrastructure.database.models.dish import DishModel


class CartModel(Base):
    __tablename__ = "carts"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    delivery_order_id: Mapped[int | None] = mapped_column(ForeignKey("delivery_orders.id"))
    status: Mapped[CartStatus] = mapped_column(
        PgEnum(CartStatus, name="cart_status"),
        default=CartStatus.ACTIVE
    )
    notes: Mapped[str | None] = mapped_column(String(300))
    is_current: Mapped[bool] = mapped_column(default=True)
    total_price: Mapped[float | None] = mapped_column(default=0.0)

    user: Mapped["UserModel"] = relationship(back_populates="carts")
    restaurant: Mapped["RestaurantModel"] = relationship()
    delivery_order: Mapped["DeliveryOrderModel"] = relationship(back_populates="carts")

    item_associations: Mapped[list["CartItemModel"]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan"
    )

    # Many-to-many through association
    dishes: Mapped[list["DishModel"]] = relationship(
        secondary="cart_items",
        back_populates="carts",
        viewonly=True
    )

    @property
    def items_count(self) -> int:
        """Общее количество позиций в корзине"""
        return sum(item.amount for item in self.item_associations)

    @property
    def is_attachable(self) -> bool:
        """Можно ли привязать к заказу"""
        return self.status == CartStatus.ACTIVE and self.items_count > 0


class CartItemModel(Base):
    __tablename__ = "cart_items"

    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"), primary_key=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id"), primary_key=True)
    amount: Mapped[int] = mapped_column(default=1)
    price_at_time: Mapped[float] = mapped_column()

    # Relationships
    cart: Mapped["CartModel"] = relationship(back_populates="item_associations")
    dish: Mapped["DishModel"] = relationship(back_populates="cart_associations")
