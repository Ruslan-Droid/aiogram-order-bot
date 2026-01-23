import typing

from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models import Base

if typing.TYPE_CHECKING:
    from app.infrastructure.database.models.category import Category
    from app.infrastructure.database.models.delivery_order import DeliveryOrder
    from app.infrastructure.database.models.cart import Cart, CartItem


class Dish(Base):
    __tablename__ = "dishes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[float] = mapped_column()
    display_order: Mapped[int] = mapped_column(default=0)

    # Relationships
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["Category"] = relationship(back_populates="dishes")

    cart_associations: Mapped[list["CartItem"]] = relationship(
        back_populates="dish",
        cascade="all, delete-orphan"
    )

    order_associations: Mapped[list["OrderItem"]] = relationship(
        back_populates="dish",
        cascade="all, delete-orphan"
    )

    # Many-to-many through associations
    carts: Mapped[list["Cart"]] = relationship(
        secondary="cart_items",
        back_populates="dishes",
        viewonly=True
    )

    orders: Mapped[list["DeliveryOrder"]] = relationship(
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
