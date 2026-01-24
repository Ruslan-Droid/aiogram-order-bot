import logging

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models.cart import CartModel, CartItemModel

logger = logging.getLogger(__name__)


class CartRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_cart_by_user(self, user_id: int, restaurant_id: int) -> CartModel | None:
        try:
            stmt = (
                select(CartModel)
                .filter(
                    CartModel.user_id == user_id,
                    CartModel.restaurant_id == restaurant_id,
                    CartModel.is_active == True
                )
                .options(
                    selectinload(CartModel.item_associations).selectinload(CartItemModel.dish),
                    selectinload(CartModel.restaurant)
                )
            )
            cart = await self.session.scalar(stmt)

            if cart:
                logger.info("Fetched active cart for user: %s, restaurant: %s", user_id, restaurant_id)
            else:
                logger.info("No active cart found for user: %s, restaurant: %s", user_id, restaurant_id)
            return cart

        except Exception as e:
            logger.error("Error getting active cart for user %s, restaurant %s: %s",
                         user_id, restaurant_id, str(e))
            raise

    async def create_cart(
            self,
            user_id: int,
            restaurant_id: int,
            is_active: bool = True
    ) -> CartModel:
        try:
            cart = CartModel(
                user_id=user_id,
                restaurant_id=restaurant_id,
                is_active=is_active,
                total_amount=0.0
            )
            self.session.add(cart)
            await self.session.commit()
            logger.info("Created cart for user: %s, restaurant: %s", user_id, restaurant_id)
            return cart

        except Exception as e:
            await self.session.rollback()
            logger.error("Error creating cart for user %s, restaurant %s: %s",
                         user_id, restaurant_id, str(e))
            raise

    async def add_item_to_cart(
            self,
            cart_id: int,
            dish_id: int,
            amount: int,
            price_at_time: float
    ) -> CartItemModel:
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
                await self.update_cart_total(cart_id)
                logger.info("Updated item in cart: cart=%s, dish=%s, new_amount=%s",
                            cart_id, dish_id, existing_item.amount)
                return existing_item
            else:
                # Добавляем новый товар
                cart_item = CartItemModel(
                    cart_id=cart_id,
                    dish_id=dish_id,
                    amount=amount,
                    price_at_time=price_at_time
                )
                self.session.add(cart_item)
                await self.update_cart_total(cart_id)
                await self.session.commit()
                logger.info("Added item to cart: cart=%s, dish=%s, amount=%s",
                            cart_id, dish_id, amount)
                return cart_item

        except Exception as e:
            await self.session.rollback()
            logger.error("Error adding item to cart %s: %s", cart_id, str(e))
            raise

    async def remove_item_from_cart(self, cart_id: int, dish_id: int) -> None:
        try:
            stmt = delete(CartItemModel).filter(
                CartItemModel.cart_id == cart_id,
                CartItemModel.dish_id == dish_id
            )
            await self.session.execute(stmt)
            await self.update_cart_total(cart_id)
            await self.session.commit()
            logger.info("Removed item from cart: cart=%s, dish=%s", cart_id, dish_id)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error removing item from cart %s: %s", cart_id, str(e))
            raise

    async def update_cart_total(self, cart_id: int) -> None:
        try:
            from sqlalchemy import func

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
                .values(total_amount=subquery)
            )
            await self.session.execute(stmt)

        except Exception as e:
            logger.error("Error updating cart total for cart %s: %s", cart_id, str(e))
            raise

    async def clear_cart(self, cart_id: int) -> None:
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
