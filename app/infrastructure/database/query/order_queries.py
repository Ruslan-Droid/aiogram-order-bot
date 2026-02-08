import logging
from datetime import datetime, date, timedelta

from sqlalchemy import select, update, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.enums import CartStatus
from app.infrastructure.database.models import CartModel, CartItemModel, DishModel
from app.infrastructure.database.models.delivery_order import DeliveryOrderModel
from app.infrastructure.database.enums.order_statuses import OrderStatus
from app.infrastructure.database.enums.payment_methods import PaymentMethod

logger = logging.getLogger(__name__)


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

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
            stmt = (
                select(DeliveryOrderModel)
                .options(
                    selectinload(DeliveryOrderModel.restaurant)  # Жадная загрузка ресторана
                )
                .where(
                    DeliveryOrderModel.created_at >= start_datetime,
                    DeliveryOrderModel.created_at < end_datetime
                )
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

    async def get_order_with_carts(self, order_id: int) -> DeliveryOrderModel | None:
        """Получить заказ вместе с корзинами и их содержимым"""
        try:
            stmt = (
                select(DeliveryOrderModel)
                .filter(DeliveryOrderModel.id == order_id)
                .options(
                    selectinload(DeliveryOrderModel.restaurant),
                    selectinload(DeliveryOrderModel.carts).selectinload(CartModel.user),
                    selectinload(DeliveryOrderModel.carts)
                    .selectinload(CartModel.item_associations)
                    .selectinload(CartItemModel.dish)
                    .selectinload(DishModel.category),
                )
            )
            order = await self.session.scalar(stmt)

            if order:
                await self.update_order_total_amount(order_id)
                # Перезагружаем заказ с обновленной суммой
                await self.session.refresh(order)
                logger.info("Fetched order with carts by id: %s", order_id)
            else:
                logger.info("Order not found by id: %s", order_id)
            return order

        except Exception as e:
            logger.error("Error getting order with carts by id %s: %s", order_id, str(e))
            raise

    async def update_order_total_amount(self, order_id: int) -> float:
        """Пересчитать и обновить общую сумму заказа на основе корзин"""
        try:
            # Получаем все корзины заказа с их суммами
            stmt = (
                select(func.coalesce(func.sum(CartModel.total_price), 0))
                .filter(CartModel.delivery_order_id == order_id)
                .filter(CartModel.status.in_([CartStatus.ORDERED]))
            )
            total_sum = await self.session.scalar(stmt) or 0.0

            # Обновляем сумму в заказе
            update_stmt = (
                update(DeliveryOrderModel)
                .where(DeliveryOrderModel.id == order_id)
                .values(total_amount=total_sum)
            )
            await self.session.execute(update_stmt)
            await self.session.commit()

            logger.info("Updated total amount for order %s: %.2f", order_id, total_sum)
            return total_sum

        except Exception as e:
            logger.error("Error updating total amount for order %s: %s", order_id, str(e))
            await self.session.rollback()
            raise
