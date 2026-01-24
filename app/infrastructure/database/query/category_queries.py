import logging

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models.category import CategoryModel

logger = logging.getLogger(__name__)


class CategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_category_by_id(self, category_id: int) -> CategoryModel | None:
        try:
            stmt = select(CategoryModel).filter(CategoryModel.id == category_id)
            category = await self.session.scalar(stmt)

            if category:
                logger.info("Fetched category by id: %s", category_id)
            else:
                logger.info("Category not found by id: %s", category_id)
            return category

        except Exception as e:
            logger.error("Error getting category by id %s: %s", category_id, str(e))
            raise

    async def get_categories_by_restaurant(self, restaurant_id: int) -> list[CategoryModel]:
        try:
            stmt = (
                select(CategoryModel)
                .filter(
                    CategoryModel.restaurant_id == restaurant_id,
                    CategoryModel.is_active == True
                )
                .order_by(CategoryModel.display_order)
            )
            result = await self.session.scalars(stmt)
            categories = list(result.all())
            logger.info("Fetched categories for restaurant: %s, count: %s", restaurant_id, len(categories))
            return categories

        except Exception as e:
            logger.error("Error getting categories for restaurant %s: %s", restaurant_id, str(e))
            raise

    async def get_category_with_dishes(self, category_id: int) -> CategoryModel | None:
        try:
            stmt = (
                select(CategoryModel)
                .filter(CategoryModel.id == category_id)
                .options(selectinload(CategoryModel.dishes))
            )
            category = await self.session.scalar(stmt)

            if category:
                logger.info("Fetched category with dishes: %s", category_id)
            return category

        except Exception as e:
            logger.error("Error getting category with dishes for id %s: %s", category_id, str(e))
            raise

    async def create_category(
            self,
            name: str,
            restaurant_id: int,
            display_order: int = 0,
            is_active: bool = True
    ) -> CategoryModel:
        try:
            category = CategoryModel(
                name=name,
                restaurant_id=restaurant_id,
                display_order=display_order,
                is_active=is_active
            )
            self.session.add(category)
            await self.session.commit()
            logger.info("Created category: %s for restaurant: %s", name, restaurant_id)
            return category

        except Exception as e:
            await self.session.rollback()
            logger.error("Error creating category %s: %s", name, str(e))
            raise

    async def delete_category(self, category_id: int) -> None:
        try:
            stmt = delete(CategoryModel).filter(CategoryModel.id == category_id)
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Deleted category: %s", category_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Error deleting category %s: %s", category_id, str(e))
            raise

    async def update_category_display_order(self, category_id: int, display_order: int) -> None:
        try:
            stmt = (
                update(CategoryModel)
                .where(CategoryModel.id == category_id)
                .values(display_order=display_order)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated category display order: id=%s, order=%s", category_id, display_order)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating category display order for id %s: %s", category_id, str(e))
            raise

    async def update_category_status(self, category_id: int, is_active: bool) -> None:
        try:
            stmt = (
                update(CategoryModel)
                .where(CategoryModel.id == category_id)
                .values(is_active=is_active)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated category status: id=%s, status=%s", category_id, is_active)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating category status for id %s: %s", category_id, str(e))
            raise
