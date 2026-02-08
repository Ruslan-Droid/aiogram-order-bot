import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.dish import DishModel

logger = logging.getLogger(__name__)


class DishRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_dish_by_id(self, dish_id: int) -> DishModel | None:
        try:
            stmt = select(DishModel).filter(DishModel.id == dish_id)
            dish = await self.session.scalar(stmt)

            if dish:
                logger.info("Fetched dish by id: %s", dish_id)
            else:
                logger.info("Dish not found by id: %s", dish_id)
            return dish

        except Exception as e:
            logger.error("Error getting dish by id %s: %s", dish_id, str(e))
            raise

    async def get_dishes_by_category(self, category_id: int) -> list[DishModel]:
        try:
            stmt = (
                select(DishModel)
                .filter(DishModel.category_id == category_id,
                        DishModel.is_active == True)
                .order_by(DishModel.display_order)
            )
            result = await self.session.scalars(stmt)
            dishes = list(result.all())
            logger.info("Fetched dishes for category: %s, count: %s", category_id, len(dishes))
            return dishes

        except Exception as e:
            logger.error("Error getting dishes for category %s: %s", category_id, str(e))
            raise

    async def create_dish(
            self,
            name: str,
            price: float,
            category_id: int,
            display_order: int = 0
    ) -> DishModel:
        try:
            dish = DishModel(
                name=name,
                price=price,
                category_id=category_id,
                display_order=display_order
            )
            self.session.add(dish)
            await self.session.commit()
            logger.info("Created dish: %s for category: %s", name, category_id)
            return dish

        except Exception as e:
            await self.session.rollback()
            logger.error("Error creating dish %s: %s", name, str(e))
            raise

    async def update_dish_price(self, dish_id: int, price: float) -> None:
        try:
            stmt = (
                update(DishModel)
                .where(DishModel.id == dish_id)
                .values(price=price)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated dish price: id=%s, price=%s", dish_id, price)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating dish price for id %s: %s", dish_id, str(e))
            raise

    async def update_dish_status(
            self,
            dish_id: int,
            status: bool
    ) -> None:
        try:
            stmt = (
                update(DishModel)
                .where(DishModel.id == dish_id)
                .values(is_active=status)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated dish status: id=%s, order=%s", dish_id, status)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating dish statys  for id %s: %s", dish_id, str(e))
            raise

    async def update_dish_name(
            self,
            dish_id: int,
            name: str
    ) -> None:
        try:
            stmt = (
                update(DishModel)
                .where(DishModel.id == dish_id)
                .values(name=name)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated dish name: id=%s, order=%s", dish_id, name)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating dish name  for id %s: %s", dish_id, str(e))
            raise
