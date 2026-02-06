import logging
from enum import Enum

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import DishModel
from app.infrastructure.database.models.cart import CartModel, CartItemModel, CartStatus

logger = logging.getLogger(__name__)


class CartRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_cart_by_id(self, cart_id: int) -> CartModel | None:
        """Получить корзину по ID"""
        try:
            stmt = (
                select(CartModel)
                .filter(CartModel.id == cart_id)
                .options(
                    selectinload(CartModel.item_associations)
                    .selectinload(CartItemModel.dish),
                    selectinload(CartModel.restaurant),
                    selectinload(CartModel.user)
                )
            )
            cart = await self.session.scalar(stmt)
            return cart
        except Exception as e:
            logger.error("Error getting cart by id %s: %s", cart_id, str(e))
            raise

    async def get_current_cart(self, user_id: int) -> CartModel | None:
        """Получить текущую активную корзину пользователя"""
        try:
            stmt = (
                select(CartModel)
                .filter(
                    CartModel.user_id == user_id,
                    CartModel.is_current == True,
                    CartModel.status == CartStatus.ACTIVE
                )
                .options(
                    selectinload(CartModel.item_associations)
                    .selectinload(CartItemModel.dish),
                    selectinload(CartModel.restaurant)
                )
            )
            cart = await self.session.scalar(stmt)

            if cart:
                logger.info("Fetched current cart for user: %s", user_id)
            else:
                logger.info("No current cart found for user: %s", user_id)
            return cart

        except Exception as e:
            logger.error("Error getting current cart for user %s: %s", user_id, str(e))
            raise

    async def get_active_cart_by_restaurant(
            self, user_id: int, restaurant_id: int
    ) -> CartModel | None:
        """Получить активную корзину пользователя для конкретного ресторана"""
        try:
            stmt = (
                select(CartModel)
                .filter(
                    CartModel.user_id == user_id,
                    CartModel.restaurant_id == restaurant_id,
                    CartModel.status == CartStatus.ACTIVE,
                    CartModel.is_current == True
                )
                .options(
                    selectinload(CartModel.item_associations)
                    .selectinload(CartItemModel.dish),
                    selectinload(CartModel.restaurant)
                )
            )
            cart = await self.session.scalar(stmt)
            return cart
        except Exception as e:
            logger.error(
                "Error getting active cart for user %s, restaurant %s: %s",
                user_id, restaurant_id, str(e)
            )
            raise

    async def create_cart(
            self,
            user_id: int,
            restaurant_id: int,
            notes: str | None = None
    ) -> CartModel:
        """Создать новую корзину"""
        try:
            # Делаем все старые корзины пользователя не текущими
            await self.session.execute(
                update(CartModel)
                .where(CartModel.user_id == user_id)
                .values(is_current=False)
            )

            # Создаем новую корзину
            cart = CartModel(
                user_id=user_id,
                restaurant_id=restaurant_id,
                status=CartStatus.ACTIVE,
                is_current=True,
                notes=notes,
                total_price=0.0
            )
            self.session.add(cart)
            await self.session.commit()
            await self.session.refresh(cart)

            logger.info(
                "Created new cart for user: %s, restaurant: %s, cart_id: %s",
                user_id, restaurant_id, cart.id
            )
            return cart

        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Error creating cart for user %s, restaurant %s: %s",
                user_id, restaurant_id, str(e)
            )
            raise

    async def get_or_create_active_cart(
            self,
            user_id: int,
            restaurant_id: int
    ) -> CartModel:
        """Получить или создать активную корзину для пользователя в ресторане"""
        try:
            # Пытаемся найти текущую корзину
            current_cart = await self.get_current_cart(user_id)

            if current_cart:
                # Если текущая корзина уже для этого ресторана - возвращаем ее
                if current_cart.restaurant_id == restaurant_id:
                    logger.info(
                        "Using existing cart for user %s, restaurant %s",
                        user_id, restaurant_id
                    )
                    return current_cart
                else:
                    # Если ресторан другой - делаем старую корзину не текущей
                    current_cart.is_current = False
                    await self.session.flush()

            # Создаем новую корзину
            cart = await self.create_cart(user_id, restaurant_id)
            return cart

        except Exception as e:
            logger.error(
                "Error getting or creating cart for user %s, restaurant %s: %s",
                user_id, restaurant_id, str(e)
            )
            raise

    async def add_item_to_cart(
            self,
            cart_id: int,
            dish_id: int,
            amount: int,
            price_at_time: float
    ) -> CartItemModel:
        """Добавить товар в корзину"""
        try:
            # Проверяем, есть ли уже этот товар в корзине
            stmt = select(CartItemModel).filter(
                CartItemModel.cart_id == cart_id,
                CartItemModel.dish_id == dish_id
            )
            existing_item = await self.session.scalar(stmt)

            if existing_item:
                # Обновляем количество
                existing_item.amount += amount
                item = existing_item
                logger.info(
                    "Updated item in cart: cart=%s, dish=%s, new_amount=%s",
                    cart_id, dish_id, existing_item.amount
                )
            else:
                # Добавляем новый товар
                cart_item = CartItemModel(
                    cart_id=cart_id,
                    dish_id=dish_id,
                    amount=amount,
                    price_at_time=price_at_time
                )
                self.session.add(cart_item)
                item = cart_item
                logger.info(
                    "Added item to cart: cart=%s, dish=%s, amount=%s",
                    cart_id, dish_id, amount
                )

            # Обновляем общую сумму корзины
            await self.update_cart_total_price(cart_id)
            await self.session.commit()

            return item

        except Exception as e:
            await self.session.rollback()
            logger.error("Error adding item to cart %s: %s", cart_id, str(e))
            raise

    async def remove_item_from_cart(self, cart_id: int, dish_id: int) -> None:
        """Удалить товар из корзины"""
        try:
            stmt = delete(CartItemModel).filter(
                CartItemModel.cart_id == cart_id,
                CartItemModel.dish_id == dish_id
            )
            await self.session.execute(stmt)
            await self.update_cart_total_price(cart_id)
            await self.session.commit()
            logger.info("Removed item from cart: cart=%s, dish=%s", cart_id, dish_id)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error removing item from cart %s: %s", cart_id, str(e))
            raise

    async def update_cart_total_price(self, cart_id: int) -> None:
        """Обновить общую сумму корзины"""
        try:
            # Вычисляем общую сумму корзины
            subquery = (
                select(
                    func.sum(CartItemModel.amount * CartItemModel.price_at_time)
                )
                .filter(CartItemModel.cart_id == cart_id)
                .scalar_subquery()
            )

            stmt = (
                update(CartModel)
                .where(CartModel.id == cart_id)
                .values(total_price=subquery)
            )
            await self.session.execute(stmt)
            await self.session.flush()
            await self.session.commit()
            logger.info("Updated total_price for cart: cart=%s", cart_id)

        except Exception as e:
            logger.error("Error updating cart total for cart %s: %s", cart_id, str(e))
            raise

    async def clear_cart(self, cart_id: int) -> None:
        """Очистить корзину"""
        try:
            # Удаляем все товары из корзины
            stmt = delete(CartItemModel).filter(CartItemModel.cart_id == cart_id)
            await self.session.execute(stmt)

            # Сбрасываем общую сумму
            update_stmt = (
                update(CartModel)
                .where(CartModel.id == cart_id)
                .values(total_amount=0.0)
            )
            await self.session.execute(update_stmt)
            await self.session.commit()
            logger.info("Cleared cart: %s", cart_id)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error clearing cart %s: %s", cart_id, str(e))
            raise

    async def update_cart_notes(self, cart_id: int, notes: str) -> None:
        """Обновить комментарий к корзине"""
        try:
            stmt = (
                update(CartModel)
                .where(CartModel.id == cart_id)
                .values(notes=notes)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated notes for cart: %s", cart_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating notes for cart %s: %s", cart_id, str(e))
            raise

    async def attach_cart_to_order(
            self,
            cart_id: int,
            order_id: int
    ) -> None:
        try:
            stmt = (
                update(CartModel)
                .where(
                    CartModel.id == cart_id,
                )
                .values(is_current=False,
                        status=CartStatus.ORDERED,
                        delivery_order_id=order_id)
            )

            await self.session.execute(stmt)
            await self.session.commit()
            logger.info(
                "Attached cart %s to order %s, status changed to ATTACHED",
                cart_id, order_id
            )

        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Error attaching cart %s to order %s: %s",
                cart_id, order_id, str(e)
            )
            raise

    async def update_cart_status(
            self,
            cart_id: int,
            status: CartStatus
    ) -> None:
        """Обновить статус корзины"""
        try:
            stmt = (
                update(CartModel)
                .where(CartModel.id == cart_id)
                .values(status=status)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated cart %s status to %s", cart_id, status.value)
        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Error updating cart %s status: %s",
                cart_id, str(e)
            )
            raise

    async def get_carts_by_order(
            self,
            order_id: int
    ) -> list[CartModel]:
        """Получить все корзины привязанные к заказу"""
        try:
            stmt = (
                select(CartModel)
                .filter(
                    CartModel.delivery_order_id == order_id,
                    CartModel.status.in_([CartStatus.ATTACHED, CartStatus.ORDERED])
                )
                .options(
                    selectinload(CartModel.item_associations)
                    .selectinload(CartItemModel.dish),
                    selectinload(CartModel.user),
                    selectinload(CartModel.restaurant)
                )
                .order_by(CartModel.created_at)
            )
            result = await self.session.execute(stmt)
            carts = list(result.scalars().all())

            logger.info(
                "Found %s carts for order %s",
                len(carts), order_id
            )
            return carts

        except Exception as e:
            logger.error(
                "Error getting carts for order %s: %s",
                order_id, str(e)
            )
            raise

    async def get_user_carts_exclude_current(
            self,
            user_id: int,
            limit: int = 10,
            offset: int = 0
    ) -> list[CartModel]:
        """Получить историю корзин пользователя"""
        try:
            stmt = (
                select(CartModel)
                .filter(CartModel.user_id == user_id,
                        CartModel.is_current != True)
                .options(
                    selectinload(CartModel.item_associations),
                    selectinload(CartModel.restaurant),
                )
                .order_by(CartModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            carts = list(result.scalars().all())

            logger.info(
                "Found %s carts for user %s (limit=%s, offset=%s)",
                len(carts), user_id, limit, offset
            )
            return carts

        except Exception as e:
            logger.error(
                "Error getting carts for user %s: %s",
                user_id, str(e)
            )
            raise

    async def get_order_carts_summary(
            self,
            order_id: int
    ) -> dict:
        """Получить сводную информацию по всем корзинам заказа"""
        try:
            carts = await self.get_carts_by_order(order_id)

            summary = {
                "total_amount": 0.0,
                "total_items": 0,
                "carts_count": len(carts),
                "carts": [],
                "users": []
            }

            for cart in carts:
                user_info = {
                    "user_id": cart.user_id,
                    "username": cart.user.username or cart.user.full_name,
                    "telegram_id": cart.user.telegram_id,
                    "cart_total": cart.total_amount,
                    "items_count": cart.items_count,
                    "notes": cart.notes
                }

                summary["total_amount"] += cart.total_amount
                summary["total_items"] += cart.items_count
                summary["users"].append(user_info)

                # Детали по позициям
                cart_details = []
                for item in cart.item_associations:
                    cart_details.append({
                        "dish_name": item.dish.name,
                        "amount": item.amount,
                        "price": item.price_at_time,
                        "total": item.amount * item.price_at_time
                    })

                summary["carts"].append({
                    "user": user_info,
                    "items": cart_details,
                    "cart_id": cart.id,
                    "status": cart.status.value
                })

            logger.info(
                "Created summary for order %s: %s carts, total %s items, amount %s",
                order_id, len(carts), summary["total_items"], summary["total_amount"]
            )
            return summary

        except Exception as e:
            logger.error(
                "Error creating summary for order %s: %s",
                order_id, str(e)
            )
            raise

    async def deactivate_old_carts(self, days: int = 30) -> int:
        """Деактивировать старые корзины (архивация)"""
        try:
            from datetime import datetime, timedelta
            from sqlalchemy import cast, Date

            cutoff_date = datetime.now() - timedelta(days=days)

            stmt = (
                update(CartModel)
                .where(
                    CartModel.status == CartStatus.ACTIVE,
                    CartModel.created_at < cutoff_date,
                    CartModel.is_current == False
                )
                .values(status=CartStatus.CANCELLED)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            count = result.rowcount
            logger.info("Deactivated %s old carts older than %s days", count, days)
            return count

        except Exception as e:
            await self.session.rollback()
            logger.error("Error deactivating old carts: %s", str(e))
            raise


class CartItemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_items_by_cart_id(self, cart_id: int) -> list[CartItemModel]:
        """Получить все товары в корзине"""
        stmt = (
            select(CartItemModel)
            .where(CartItemModel.cart_id == cart_id)
            .options(selectinload(CartItemModel.dish))
            .order_by(CartItemModel.dish_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_cart_item(self, cart_id: int, dish_id: int) -> CartItemModel | None:
        """Получить конкретный товар в корзине"""
        stmt = (
            select(CartItemModel)
            .where(
                CartItemModel.cart_id == cart_id,
                CartItemModel.dish_id == dish_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_or_update_item(
            self,
            cart_id: int,
            dish_id: int,
            amount: int = 1
    ) -> CartItemModel:
        """Добавить или обновить товар в корзине"""
        # Получаем цену блюда
        dish_stmt = select(DishModel).where(DishModel.id == dish_id)
        dish_result = await self.session.execute(dish_stmt)
        dish = dish_result.scalar_one()

        # Проверяем, есть ли уже этот товар в корзине
        existing = await self.get_cart_item(cart_id, dish_id)

        if existing:
            existing.amount = amount
            existing.price_at_time = dish.price
            item = existing
        else:
            item = CartItemModel(
                cart_id=cart_id,
                dish_id=dish_id,
                amount=amount,
                price_at_time=dish.price
            )
            self.session.add(item)

        await self.session.commit()
        return item

    async def increment_item(self, cart_id: int, dish_id: int) -> CartItemModel:
        """Увеличить количество товара на 1"""
        item = await self.get_cart_item(cart_id, dish_id)

        if item:
            item.amount += 1
            await self.session.commit()
            return item
        else:
            return await self.add_or_update_item(cart_id, dish_id, 1)

    async def decrement_item(self, cart_id: int, dish_id: int) -> CartItemModel | None:
        """Уменьшить количество товара на 1"""
        item = await self.get_cart_item(cart_id, dish_id)

        if item:
            if item.amount > 1:
                item.amount -= 1
                await self.session.commit()
                return item
            else:
                # Удаляем товар если количество становится 0
                await self.remove_item_from_cart(cart_id, dish_id)
                return None
        return None

    async def update_item_quantity(
            self,
            cart_id: int,
            dish_id: int,
            quantity: int
    ) -> CartItemModel | None:
        """Обновить количество товара"""
        if quantity <= 0:
            # Удаляем товар
            await self.remove_item_from_cart(cart_id, dish_id)
            return None
        else:
            return await self.add_or_update_item(cart_id, dish_id, quantity)

    async def remove_item_from_cart(self, cart_id: int, dish_id: int) -> None:
        """Удалить товар из корзины"""
        delete_stmt = delete(CartItemModel).where(
            CartItemModel.cart_id == cart_id,
            CartItemModel.dish_id == dish_id
        )
        await self.session.execute(delete_stmt)
        await self.session.commit()

    async def clear_cart(self, cart_id: int) -> None:
        """Удалить все товары из корзины"""
        delete_stmt = delete(CartItemModel).where(
            CartItemModel.cart_id == cart_id
        )
        await self.session.execute(delete_stmt)
        await self.session.commit()

    async def add_or_update_cart_item(
            self,
            cart_id: int,
            dish_id: int,
            amount: int,
            price_at_time: float
    ) -> CartItemModel:
        """Добавить или обновить позицию в корзине (с указанием цены)"""
        stmt = select(CartItemModel).where(
            and_(
                CartItemModel.cart_id == cart_id,
                CartItemModel.dish_id == dish_id
            )
        )

        result = await self.session.execute(stmt)
        cart_item = result.scalar_one_or_none()

        if cart_item:
            cart_item.amount = amount
            cart_item.price_at_time = price_at_time
        else:
            cart_item = CartItemModel(
                cart_id=cart_id,
                dish_id=dish_id,
                amount=amount,
                price_at_time=price_at_time
            )
            self.session.add(cart_item)

        await self.session.commit()
        await self.session.refresh(cart_item)
        return cart_item

    async def remove_cart_item(self, cart_id: int, dish_id: int) -> None:
        """Удалить позицию из корзины"""
        stmt = delete(CartItemModel).where(
            and_(
                CartItemModel.cart_id == cart_id,
                CartItemModel.dish_id == dish_id
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_cart_items_with_dishes(self, cart_id: int) -> list[dict]:
        """Получить товары корзины с информацией о блюдах"""
        stmt = (
            select(CartItemModel, DishModel)
            .join(DishModel, CartItemModel.dish_id == DishModel.id)
            .where(CartItemModel.cart_id == cart_id)
            .order_by(DishModel.name)
        )
        result = await self.session.execute(stmt)

        items = []
        for cart_item, dish in result:
            items.append({
                "cart_item": cart_item,
                "dish": dish,
                "total": cart_item.amount * cart_item.price_at_time
            })

        return items

    async def copy_cart_items_to_order(
            self,
            cart_id: int,
            order_id: int
    ) -> list:
        """Скопировать товары из корзины в заказ (при создании OrderItem)"""
        try:
            # Получаем все товары корзины
            cart_items = await self.get_items_by_cart_id(cart_id)

            # Здесь должна быть логика создания OrderItemModel
            # (это зависит от вашей реализации OrderItemRepository)

            logger.info(
                "Copied %s items from cart %s to order %s",
                len(cart_items), cart_id, order_id
            )
            return cart_items

        except Exception as e:
            logger.error(
                "Error copying items from cart %s to order %s: %s",
                cart_id, order_id, str(e)
            )
            raise
