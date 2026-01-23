from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.enums.order_statuses import OrderStatus
from app.infrastructure.database.enums.payment_methods import PaymentMethod
from app.infrastructure.database.models import Base


class DeliveryOrder(Base):
    __tablename__ = "delivery_orders"

    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    delivery_person_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[OrderStatus] = mapped_column(default=OrderStatus.COLLECTING)
    phone_number: Mapped[str | None] = mapped_column(ForeignKey("users.phone_number"))
    payment_method: Mapped[PaymentMethod | None] = mapped_column(ForeignKey("users.preferred_bank"))
    total_amount: Mapped[float] = mapped_column(default=0.0)
    collected_at: Mapped[datetime | None] = mapped_column()
    delivered_at: Mapped[datetime | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(String(255))  # дополнительные заметки

    # Relationships
    restaurant: Mapped["Restaurant"] = relationship(back_populates="orders")
    creator: Mapped["User"] = relationship(
        foreign_keys=[creator_id],
        back_populates="created_orders"
    )
    delivery_person: Mapped[Optional["User"]] = relationship(
        foreign_keys=[delivery_person_id],
        back_populates="assigned_orders"
    )
    carts: Mapped[List["Cart"]] = relationship(back_populates="delivery_order")

    item_associations: Mapped[List["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan"
    )

    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="delivery_order",
        cascade="all, delete-orphan"
    )

    # Many-to-many through association
    dishes: Mapped[List["Dish"]] = relationship(
        secondary="order_items",
        back_populates="orders",
        viewonly=True
    )

    __table_args__ = (
        Index("ix_orders_status_date", "status", "created_at"),
        Index("ix_orders_restaurant_date", "restaurant_id", "created_at"),
    )

    @property
    def is_active(self) -> bool:
        """Проверяет, активен ли заказ"""
        active_statuses = {
            OrderStatus.COLLECTING,
            OrderStatus.PROCESSING,
            OrderStatus.PREPARING,
            OrderStatus.READY,
            OrderStatus.DELIVERING
        }
        return self.status in active_statuses

    @property
    def is_collecting(self) -> bool:
        """Проверяет, идет ли сбор заказов"""
        return self.status == OrderStatus.COLLECTING

    @property
    def time_left(self) -> Optional[int]:
        """Возвращает оставшееся время до дедлайна в минутах"""
        if not self.deadline_time:
            return None

        from datetime import datetime
        now = datetime.utcnow()
        if now > self.deadline_time:
            return 0

        delta = self.deadline_time - now
        return int(delta.total_seconds() // 60)

    def calculate_total(self) -> Decimal:
        """Пересчитывает общую сумму заказа"""
        total = Decimal('0')
        for item in self.item_associations:
            total += item.price * Decimal(str(item.quantity))
        self.total_amount = total
        return total

    def add_dish(self, dish: Dish, quantity: int = 1, user: Optional["User"] = None) -> None:
        """Добавляет блюдо в заказ"""
        order_item = OrderItem(
            dish=dish,
            quantity=quantity,
            price=dish.price,
            user=user
        )
        self.item_associations.append(order_item)
        self.calculate_total()

    def change_status(self, new_status: OrderStatus) -> None:
        """Изменяет статус заказа"""
        self.status = new_status
        now = datetime.utcnow()

        if new_status == OrderStatus.COLLECTING:
            self.collected_at = None
            self.delivered_at = None
        elif new_status == OrderStatus.DELIVERED:
            self.delivered_at = now
        elif new_status in [OrderStatus.PROCESSING, OrderStatus.PREPARING]:
            self.collected_at = now

    def __repr__(self) -> str:
        return f"DeliveryOrder(id={self.id}, status={self.status.value}, total={self.total_amount})"


class OrderItem(Base):
    __tablename__ = "order_items"

    order_id: Mapped[int] = mapped_column(ForeignKey("delivery_orders.id"), primary_key=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id"), primary_key=True)
    quantity: Mapped[int] = mapped_column()
    price: Mapped[float] = mapped_column()
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    # Relationships
    order: Mapped["DeliveryOrder"] = relationship(back_populates="item_associations")
    dish: Mapped["Dish"] = relationship(back_populates="order_associations")
    user: Mapped["User" | None] = relationship()
