from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.category import CategoryModel
    from app.infrastructure.database.models.delivery_order import DeliveryOrderModel, OrderItemModel
    from app.infrastructure.database.models.cart import CartModel, CartItemModel


class DishModel(Base):
    __tablename__ = "dishes"

    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[float] = mapped_column()
    display_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["CategoryModel"] = relationship(back_populates="dishes")

    cart_associations: Mapped[list["CartItemModel"]] = relationship(
        back_populates="dish",
        cascade="all, delete-orphan"
    )

    order_associations: Mapped[list["OrderItemModel"]] = relationship(
        back_populates="dish",
        cascade="all, delete-orphan"
    )

    # Many-to-many through associations
    carts: Mapped[list["CartModel"]] = relationship(
        secondary="cart_items",
        back_populates="dishes",
        viewonly=True
    )

    orders: Mapped[list["DeliveryOrderModel"]] = relationship(
        secondary="order_items",
        back_populates="dishes",
        viewonly=True
    )

    __table_args__ = (
        Index("ix_dishes_category_order", "category_id", "display_order"),
    )

    @property
    def formatted_price(self) -> str:
        """Отформатированная цена"""
        return f"{self.price:.2f} ₽"

    def __repr__(self) -> str:
        return f"Dish(id={self.id}, name='{self.name}', price={self.price})"
