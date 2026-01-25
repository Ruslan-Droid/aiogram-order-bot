import logging
from datetime import datetime, date, timedelta
from typing import Any

from sqlalchemy import select, update, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models.delivery_order import DeliveryOrderModel, OrderItemModel
from app.infrastructure.database.enums.order_statuses import OrderStatus
from app.infrastructure.database.enums.payment_methods import PaymentMethod

logger = logging.getLogger(__name__)


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_order_by_id(self, order_id: int) -> DeliveryOrderModel | None:
        try:
            stmt = (
                select(DeliveryOrderModel)
                .filter(DeliveryOrderModel.id == order_id)
                .options(
                    selectinload(DeliveryOrderModel.item_associations).selectinload(OrderItemModel.dish),
                    selectinload(DeliveryOrderModel.restaurant),
                    selectinload(DeliveryOrderModel.creator),
                    selectinload(DeliveryOrderModel.delivery_person)
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

    async def get_active_orders_by_restaurant(self, restaurant_id: int) -> list[DeliveryOrderModel]:
        try:
            stmt = (
                select(DeliveryOrderModel)
                .filter(
                    DeliveryOrderModel.restaurant_id == restaurant_id,
                    DeliveryOrderModel.status.in_([
                        OrderStatus.COLLECTING,
                    ])
                )
                .order_by(DeliveryOrderModel.created_at)
                .options(
                    selectinload(DeliveryOrderModel.item_associations).selectinload(OrderItemModel.dish),
                    selectinload(DeliveryOrderModel.creator)
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

    async def get_orders_by_user(self, user_id: int, limit: int = 10) -> list[DeliveryOrderModel]:
        try:
            stmt = (
                select(DeliveryOrderModel)
                .filter(
                    (DeliveryOrderModel.creator_id == user_id) |
                    (DeliveryOrderModel.delivery_person_id == user_id)
                )
                .order_by(DeliveryOrderModel.created_at.desc())
                .limit(limit)
                .options(
                    selectinload(DeliveryOrderModel.item_associations).selectinload(OrderItemModel.dish),
                    selectinload(DeliveryOrderModel.restaurant)
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
    ) -> DeliveryOrderModel:
        try:
            order = DeliveryOrderModel(
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

    async def delete_order(self, order_id: int) -> None:
        try:
            stmt = delete(DeliveryOrderModel).where(DeliveryOrderModel.id == order_id)
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Deleted order: id=%s", order_id)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error deleting order: %s", str(e))
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
                update(DeliveryOrderModel)
                .where(DeliveryOrderModel.id == order_id)
                .values(total_amount=subquery)
            )
            await self.session.execute(stmt)

        except Exception as e:
            logger.error("Error updating order total for order %s: %s", order_id, str(e))
            raise

    async def assign_delivery_person(self, order_id: int, delivery_person_id: int) -> None:
        try:
            stmt = (
                update(DeliveryOrderModel)
                .where(DeliveryOrderModel.id == order_id)
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
                    func.count(DeliveryOrderModel.id).label('total_orders'),
                    func.sum(DeliveryOrderModel.total_amount).label('total_revenue'),
                    func.avg(DeliveryOrderModel.total_amount).label('avg_order_value')
                )
                .filter(
                    DeliveryOrderModel.restaurant_id == restaurant_id,
                    DeliveryOrderModel.created_at >= start_date,
                    DeliveryOrderModel.created_at <= end_date,
                    DeliveryOrderModel.status == OrderStatus.DELIVERED
                )
            )
            result = await self.session.execute(stmt)
            stats = result.first()

            # Статистика по статусам
            status_stmt = (
                select(
                    DeliveryOrderModel.status,
                    func.count(DeliveryOrderModel.id).label('count')
                )
                .filter(
                    DeliveryOrderModel.restaurant_id == restaurant_id,
                    DeliveryOrderModel.created_at >= start_date,
                    DeliveryOrderModel.created_at <= end_date
                )
                .group_by(DeliveryOrderModel.status)
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

    async def get_orders_by_date(
            self,
            order_date: date,
            status: OrderStatus | None = None,
    ) -> list[DeliveryOrderModel]:
        try:
            # Определяем временные границы для дня
            start_datetime = datetime.combine(order_date, datetime.min.time())
            end_datetime = datetime.combine(order_date + timedelta(days=1), datetime.min.time())

            # Базовый запрос с загрузкой связанных данных
            stmt = select(DeliveryOrderModel).where(
                DeliveryOrderModel.created_at >= start_datetime,
                DeliveryOrderModel.created_at < end_datetime
            )
            if status:
                stmt = stmt.where(DeliveryOrderModel.status == status)
            # Сортировка по дате создания (новые сначала)
            stmt = stmt.order_by(DeliveryOrderModel.created_at.desc())

            result = await self.session.execute(stmt)
            logger.info("Successfully fetched orders by date %s", order_date)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Error getting order by date for  date %s: %s", order_date, str(e))
            raise

    async def update_order_status(
            self,
            order_id: int,
            status: OrderStatus
    ) -> None:
        try:
            stmt = (
                update(DeliveryOrderModel)
                .where(DeliveryOrderModel.id == order_id)
                .values(status=status)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Successfully updated order status for order %s", order_id)

        except Exception as e:
            logger.error("Error updating order %s status: %s", order_id, str(e))
            await self.session.rollback()
            raise
