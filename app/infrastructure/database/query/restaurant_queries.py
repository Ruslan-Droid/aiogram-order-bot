import logging

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.restaurant import RestaurantModel

logger = logging.getLogger(__name__)


class RestaurantRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_restaurant_by_id(self, restaurant_id: int) -> RestaurantModel | None:
        try:
            stmt = select(RestaurantModel).filter(RestaurantModel.id == restaurant_id)
            restaurant = await self.session.scalar(stmt)

            if restaurant:
                logger.info("Fetched restaurant by id: %s", restaurant_id)
            else:
                logger.info("Restaurant not found by id: %s", restaurant_id)
            return restaurant

        except Exception as e:
            logger.error("Error getting restaurant by id %s: %s", restaurant_id, str(e))
            raise

    async def get_all_active_restaurants(self) -> list[RestaurantModel]:
        try:
            stmt = (
                select(RestaurantModel)
                .filter(RestaurantModel.is_active == True)
                .order_by(RestaurantModel.name)
            )
            result = await self.session.scalars(stmt)
            restaurants = list(result.all())
            logger.info("Fetched all active restaurants, count: %s", len(restaurants))
            return restaurants

        except Exception as e:
            logger.error("Error getting all active restaurants: %s", str(e))
            raise

    async def create_restaurant(self, name: str, is_active: bool = True) -> RestaurantModel:
        try:
            restaurant = RestaurantModel(name=name, is_active=is_active)
            self.session.add(restaurant)
            await self.session.commit()
            logger.info("Created restaurant: %s", name)
            return restaurant

        except Exception as e:
            await self.session.rollback()
            logger.error("Error creating restaurant %s: %s", name, str(e))
            raise

    async def delete_restaurant(self, restaurant_id: int) -> None:
        try:
            stmt = (
                delete(RestaurantModel)
                .where(RestaurantModel.id == restaurant_id)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Deleted restaurant: %s", restaurant_id)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error deleting restaurant %s: %s", restaurant_id, str(e))
            raise

    async def update_restaurant_status(self, restaurant_id: int, is_active: bool) -> None:
        try:
            stmt = (
                update(RestaurantModel)
                .where(RestaurantModel.id == restaurant_id)
                .values(is_active=is_active)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated restaurant status: id=%s, status=%s", restaurant_id, is_active)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating restaurant status for id %s: %s", restaurant_id, str(e))
            raise

    async def update_restaurant_name(self, restaurant_id: int, name: str) -> None:
        try:
            stmt = (
                update(RestaurantModel)
                .where(RestaurantModel.id == restaurant_id)
                .values(name=name)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated restaurant name: id=%s, name=%s", restaurant_id, name)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating restaurant name for id %s: %s", restaurant_id, str(e))
            raise

    async def get_restaurant_with_categories(self, restaurant_id: int) -> RestaurantModel | None:
        try:
            from sqlalchemy.orm import selectinload
            stmt = (
                select(RestaurantModel)
                .filter(RestaurantModel.id == restaurant_id)
                .options(selectinload(RestaurantModel.categories))
            )
            restaurant = await self.session.scalar(stmt)

            if restaurant:
                logger.info("Fetched restaurant with categories: %s", restaurant_id)
            return restaurant

        except Exception as e:
            logger.error("Error getting restaurant with categories for id %s: %s", restaurant_id, str(e))
            raise
