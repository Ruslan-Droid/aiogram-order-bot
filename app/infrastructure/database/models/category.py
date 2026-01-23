import typing

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models import Base

if typing.TYPE_CHECKING:
    from app.infrastructure.database.models.restaurant import Restaurant
    from app.infrastructure.database.models.dish import Dish

class Category(Base):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(255))
    display_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    restaurant: Mapped["Restaurant"] = relationship(back_populates="categories")

    dishes: Mapped[list["Dish"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
        order_by="Dish.display_order"
    )

    __table_args__ = (
        Index("ix_categories_restaurant_order", "restaurant_id", "display_order"),
    )


    def __repr__(self) -> str:
        return f"Category(id={self.id}, name='{self.name}')"