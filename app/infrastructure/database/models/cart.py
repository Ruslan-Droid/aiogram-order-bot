from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models import Base


class Cart(Base):
    __tablename__ = "carts"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    delivery_order_id: Mapped[int | None] = mapped_column(ForeignKey("delivery_orders.id"))
    is_active: Mapped[bool] = mapped_column(default=True)
    total_amount: Mapped[float] = mapped_column(default=0.0)

    user: Mapped["User"] = relationship(back_populates="carts")
    restaurant: Mapped["Restaurant"] = relationship()
    delivery_order: Mapped["DeliveryOrder" | None] = relationship(back_populates="carts")

    item_associations: Mapped[list["CartItem"]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan"
    )

    # Many-to-many through association
    dishes: Mapped[list["Dish"]] = relationship(
        secondary="cart_items",
        back_populates="carts",
        viewonly=True
    )

    __table_args__ = (
        Index("ix_carts_user_active", "user_id", "is_active"),
    )

    @property
    def items_count(self) -> int:
        """Общее количество позиций в корзине"""
        return sum(item.amount for item in self.item_associations)


class CartItem(Base):
    __tablename__ = "cart_items"

    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"), primary_key=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id"), primary_key=True)
    amount: Mapped[int] = mapped_column(default=1)
    price_at_time: Mapped[float] = mapped_column()

    # Relationships
    cart: Mapped["Cart"] = relationship(back_populates="item_associations")
    dish: Mapped["Dish"] = relationship(back_populates="cart_associations")
