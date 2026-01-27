import logging

from sqlalchemy import select, update, delete
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

    async def get_dishes_by_ids(self, dish_ids: list[int]) -> list[DishModel]:
        try:
            if not dish_ids:
                return []

            stmt = (
                select(DishModel)
                .filter(DishModel.id.in_(dish_ids))
                .order_by(DishModel.name)
            )
            result = await self.session.scalars(stmt)
            dishes = list(result.all())
            logger.info("Fetched dishes by ids, count: %s", len(dishes))
            return dishes

        except Exception as e:
            logger.error("Error getting dishes by ids: %s", str(e))
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

    async def delete_dish(self, dish_id: int) -> None:
        try:
            stmt = delete(DishModel).filter(DishModel.id == dish_id)
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Deleted dish %s", dish_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Error deleting dish %s: %s", dish_id, str(e))
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

    async def update_dish_order(self, dish_id: int, display_order: int) -> None:
        try:
            stmt = (
                update(DishModel)
                .where(DishModel.id == dish_id)
                .values(display_order=display_order)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated dish display order: id=%s, order=%s", dish_id, display_order)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating dish display order for id %s: %s", dish_id, str(e))
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
                .values(status=status)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated dish status: id=%s, order=%s", dish_id, status)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating dish statys  for id %s: %s", dish_id, str(e))
            raise
