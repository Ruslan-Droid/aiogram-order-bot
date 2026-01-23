import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.infrastructure.database.models.user import UserModel, UserRole

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_telegram_id(self, telegram_id: int) -> UserModel | None:
        try:
            stmt = select(UserModel).filter(UserModel.telegram_id == telegram_id)
            user = await self.session.scalar(stmt)

            if user:
                logger.info("Fetched user by telegram id: %s", telegram_id)
            else:
                logger.info("User not found by telegram id: %s", telegram_id)
            return user

        except Exception as e:
            logger.error("Error getting user by telegram id %s: %s", telegram_id, str(e))
            raise

    async def create_or_update_user(
            self,
            telegram_id: int,
            username: str | None,
            first_name: str | None,
            last_name: str | None,
            language_code: str | None = "en",
            is_active: bool = True,
            role: UserRole = UserRole.MEMBER,
    ) -> UserModel:
        insert_stmt = pg_insert(UserModel).values(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            role=role,
            is_active=is_active,
        )

        # Define what to update on conflict
        update_dict = {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'language_code': language_code,
            "role": role,
        }

        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=['telegram_id'],
            set_=update_dict
        ).returning(UserModel)

        try:
            # Execute the upsert
            result = await self.session.execute(on_conflict_stmt)
            user = result.scalar_one_or_none()
            logger.info("Created/Updated user with telegram id: %s", telegram_id)
            await self.session.commit()
            return user

        except Exception as e:
            await self.session.rollback()
            logger.error("Error creating/updating user by telegram id: %s, error: %s", telegram_id, str(e))
            raise

    async def update_user_tz_region(self, telegram_id: int, tz_region: str) -> None:
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.telegram_id == telegram_id)
                .values(tz_region=tz_region)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated time_zone for telegram id: %s", telegram_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating time_zone for telegram id: %s, error: %s", telegram_id, str(e))
            raise

    async def update_users_coordinates(
            self,
            telegram_id: int,
            latitude: float,
            longitude: float
    ) -> None:
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.telegram_id == telegram_id)
                .values(latitude=latitude, longitude=longitude)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated coordinates for telegram id: %s", telegram_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating coordinates for telegram id: %s, error: %s", telegram_id, str(e))
            raise

    async def update_users_language(
            self,
            telegram_id: int,
            language_code: str
    ) -> None:
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.telegram_id == telegram_id)
                .values(language_code=language_code)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated coordinates for telegram id: %s", telegram_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating coordinates for telegram id: %s error: %s", telegram_id, str(e))
            raise

    async def update_user_city(
            self,
            telegram_id: int,
            city: str
    ) -> None:
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.telegram_id == telegram_id)
                .values(city=city)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated city for telegram id: %s", telegram_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating city for telegram id: %s error: %s", telegram_id, str(e))
            raise

    async def update_activity_status(
            self,
            telegram_id: int,
            status: bool
    ) -> None:
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.telegram_id == telegram_id)
                .values(is_active=status)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated is_active status for telegram id: %s", telegram_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating is_active status for telegram id: %s error: %s", telegram_id, str(e))
            raise

    async def get_users_by_telegram_ids(
            self,
            telegram_ids: list[int]
    ) -> dict[int, UserModel]:
        try:
            stmt = select(UserModel).filter(
                UserModel.telegram_id.in_(telegram_ids)
            )
            users = await self.session.scalars(stmt)
            return {user.telegram_id: user for user in users}
        except Exception as e:
            logger.error("Error getting users by ids: %s", str(e))
            return {}
