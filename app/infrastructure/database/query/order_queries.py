import logging
from datetime import datetime

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models.delivery_order import DeliveryOrder, OrderItemModel
from app.infrastructure.database.enums.order_statuses import OrderStatus
from app.infrastructure.database.enums.payment_methods import PaymentMethod

logger = logging.getLogger(__name__)


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_order_by_id(self, order_id: int) -> DeliveryOrder | None:
        try:
            stmt = (
                select(DeliveryOrder)
                .filter(DeliveryOrder.id == order_id)
                .options(
                    selectinload(DeliveryOrder.item_associations).selectinload(OrderItemModel.dish),
                    selectinload(DeliveryOrder.restaurant),
                    selectinload(DeliveryOrder.creator),
                    selectinload(DeliveryOrder.delivery_person)
                )
            )
            order = await self.session.scalar(stmt)

            if order:
                logger.info("Fetched order by id: %s", order_id)
            else:
                logger.info("Order not found by id: %s", order_id)
            return order

        except Exception as e:
            logger.error("Error getting order by id %s: %s", order_id, str(e))
            raise

    async def get_active_orders_by_restaurant(self, restaurant_id: int) -> list[DeliveryOrder]:
        try:
            stmt = (
                select(DeliveryOrder)
                .filter(
                    DeliveryOrder.restaurant_id == restaurant_id,
                    DeliveryOrder.status.in_([
                        OrderStatus.COLLECTING,
                    ])
                )
                .order_by(DeliveryOrder.created_at)
                .options(
                    selectinload(DeliveryOrder.item_associations).selectinload(OrderItemModel.dish),
                    selectinload(DeliveryOrder.creator)
                )
            )
            result = await self.session.scalars(stmt)
            orders = list(result.all())
            logger.info("Fetched active orders for restaurant: %s, count: %s",
                        restaurant_id, len(orders))
            return orders

        except Exception as e:
            logger.error("Error getting active orders for restaurant %s: %s",
                         restaurant_id, str(e))
            raise

    async def get_orders_by_user(self, user_id: int, limit: int = 10) -> list[DeliveryOrder]:
        try:
            stmt = (
                select(DeliveryOrder)
                .filter(
                    (DeliveryOrder.creator_id == user_id) |
                    (DeliveryOrder.delivery_person_id == user_id)
                )
                .order_by(DeliveryOrder.created_at.desc())
                .limit(limit)
                .options(
                    selectinload(DeliveryOrder.item_associations).selectinload(OrderItemModel.dish),
                    selectinload(DeliveryOrder.restaurant)
                )
            )
            result = await self.session.scalars(stmt)
            orders = list(result.all())
            logger.info("Fetched orders for user: %s, count: %s", user_id, len(orders))
            return orders

        except Exception as e:
            logger.error("Error getting orders for user %s: %s", user_id, str(e))
            raise

    async def create_order(
            self,
            restaurant_id: int,
            creator_id: int,
            phone_number: str | None = None,
            payment_method: PaymentMethod | None = None,
            notes: str | None = None
    ) -> DeliveryOrder:
        try:
            order = DeliveryOrder(
                restaurant_id=restaurant_id,
                creator_id=creator_id,
                delivery_person_id=creator_id,  # по умолчанию создатель является доставщиком
                status=OrderStatus.COLLECTING,
                phone_number=phone_number,
                payment_method=payment_method,
                notes=notes,
                total_amount=0.0
            )
            self.session.add(order)
            await self.session.commit()
            logger.info("Created order: id=%s, restaurant=%s, creator=%s",
                        order.id, restaurant_id, creator_id)
            return order

        except Exception as e:
            await self.session.rollback()
            logger.error("Error creating order: %s", str(e))
            raise

    async def add_items_to_order(
            self,
            order_id: int,
            items: list[tuple[int, int, float, int | None]]  # (dish_id, quantity, price, user_id)
    ) -> None:
        try:
            for dish_id, quantity, price, user_id in items:
                order_item = OrderItemModel(
                    order_id=order_id,
                    dish_id=dish_id,
                    quantity=quantity,
                    price=price,
                    user_id=user_id
                )
                self.session.add(order_item)

            await self.update_order_total(order_id)
            await self.session.commit()
            logger.info("Added %s items to order: %s", len(items), order_id)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error adding items to order %s: %s", order_id, str(e))
            raise

    async def update_order_total(self, order_id: int) -> None:
        try:
            # Вычисляем общую сумму заказа
            subquery = (
                select(
                    func.sum(OrderItemModel.quantity * OrderItemModel.price)
                )
                .filter(OrderItemModel.order_id == order_id)
                .scalar_subquery()
            )

            stmt = (
                update(DeliveryOrder)
                .where(DeliveryOrder.id == order_id)
                .values(total_amount=subquery)
            )
            await self.session.execute(stmt)

        except Exception as e:
            logger.error("Error updating order total for order %s: %s", order_id, str(e))
            raise

    async def assign_delivery_person(self, order_id: int, delivery_person_id: int) -> None:
        try:
            stmt = (
                update(DeliveryOrder)
                .where(DeliveryOrder.id == order_id)
                .values(delivery_person_id=delivery_person_id)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Assigned delivery person: order=%s, person=%s",
                        order_id, delivery_person_id)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error assigning delivery person for order %s: %s", order_id, str(e))
            raise

    async def get_order_statistics(
            self,
            restaurant_id: int,
            start_date: datetime,
            end_date: datetime
    ) -> dict:
        try:
            # Общая статистика по заказам
            stmt = (
                select(
                    func.count(DeliveryOrder.id).label('total_orders'),
                    func.sum(DeliveryOrder.total_amount).label('total_revenue'),
                    func.avg(DeliveryOrder.total_amount).label('avg_order_value')
                )
                .filter(
                    DeliveryOrder.restaurant_id == restaurant_id,
                    DeliveryOrder.created_at >= start_date,
                    DeliveryOrder.created_at <= end_date,
                    DeliveryOrder.status == OrderStatus.DELIVERED
                )
            )
            result = await self.session.execute(stmt)
            stats = result.first()

            # Статистика по статусам
            status_stmt = (
                select(
                    DeliveryOrder.status,
                    func.count(DeliveryOrder.id).label('count')
                )
                .filter(
                    DeliveryOrder.restaurant_id == restaurant_id,
                    DeliveryOrder.created_at >= start_date,
                    DeliveryOrder.created_at <= end_date
                )
                .group_by(DeliveryOrder.status)
            )
            status_result = await self.session.execute(status_stmt)
            status_stats = {row.status: row.count for row in status_result}

            return {
                'total_orders': stats.total_orders or 0,
                'total_revenue': float(stats.total_revenue or 0),
                'avg_order_value': float(stats.avg_order_value or 0),
                'status_distribution': status_stats
            }

        except Exception as e:
            logger.error("Error getting order statistics for restaurant %s: %s",
                         restaurant_id, str(e))
            raise
