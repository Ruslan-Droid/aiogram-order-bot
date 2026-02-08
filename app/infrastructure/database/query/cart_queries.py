import logging

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models.cart import CartModel, CartItemModel, CartStatus
from app.infrastructure.database.query.order_queries import OrderRepository

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
            await OrderRepository(self.session).update_order_total_amount(order_id)
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
                    CartModel.status.in_([CartStatus.ORDERED])
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

    async def update_item_amount(
            self,
            cart_id: int,
            dish_id: int,
            amount: int = 1
    ) -> CartItemModel:
        try:
            # Получаем существующую запись в корзине
            stmt = (
                select(CartItemModel)
                .where(CartItemModel.cart_id == cart_id)
                .where(CartItemModel.dish_id == dish_id)
            )
            result = await self.session.execute(stmt)
            cart_item = result.scalar_one_or_none()
            cart_item.amount = amount
            await self.session.commit()
            await self.session.refresh(cart_item)
            return cart_item

        except Exception as e:
            logger.error("Error updating item amount for cart %s: %s", cart_id, amount, exc_info=e)
            await self.session.rollback()
            raise

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
