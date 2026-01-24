from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.category import CategoryModel
    from app.infrastructure.database.models.delivery_order import DeliveryOrder


class RestaurantModel(Base):
    __tablename__ = "restaurants"

    name: Mapped[str] = mapped_column(String(255), unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    categories: Mapped[list["CategoryModel"]] = relationship(
        back_populates="restaurant",
        cascade="all, delete-orphan",
        order_by="Category.display_order"
    )

    orders: Mapped[list["DeliveryOrder"]] = relationship(
        back_populates="restaurant",
        order_by="DeliveryOrder.created_at.desc()"
    )

    def __repr__(self) -> str:
        return f"Restaurant(id={self.id}, name='{self.name}')"
