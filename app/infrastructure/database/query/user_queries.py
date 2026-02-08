import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.infrastructure.database.enums.payment_methods import PaymentMethod
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
            role: UserRole = UserRole.UNKNOWN,
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

    async def update_phone_and_bank(
            self,
            telegram_id: int,
            phone_number: str,
            bank: PaymentMethod,
    ) -> None:
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.telegram_id == telegram_id)
                .values(
                    phone_number=phone_number,
                    preferred_bank=bank,
                )
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated is_active status for telegram id: %s", telegram_id)

        except Exception as e:
            logger.error("Error getting update_phone_and_bank: %s", str(e))
            raise

    async def get_active_users_except(
            self,
            exclude_telegram_id: int | None = None
    ) -> list[UserModel]:
        try:
            # Исключаем роли UNKNOWN и BANNED
            stmt = select(UserModel).where(
                UserModel.is_active == True,
                UserModel.role.not_in([UserRole.UNKNOWN, UserRole.BANNED])
            )

            # Исключаем конкретного пользователя, если указан
            if exclude_telegram_id:
                stmt = stmt.where(UserModel.telegram_id != exclude_telegram_id)

            result = await self.session.execute(stmt)
            users = list(result.scalars().all())

            logger.info("Fetched %s active users (excluding UNKNOWN/BANNED roles)", len(users))
            return users

        except Exception as e:
            logger.error("Error getting active users: %s", str(e))
            raise

    async def get_active_admins(
            self,
    ) -> list[UserModel]:
        try:
            stmt = select(UserModel).where(
                UserModel.is_active == True,
                UserModel.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN])
            )

            result = await self.session.execute(stmt)
            admins = list(result.scalars().all())

            logger.info("Fetched %s active users (ADMIN roles)", len(admins))
            return admins
        except Exception as e:
            logger.error("Error getting active admins: %s", str(e))
            raise

    async def update_user_role(
            self,
            role: UserRole,
            telegram_id: int,
    ) -> None:
        try:
            stmt = (
                update(UserModel)
                .where(UserModel.telegram_id == telegram_id)
                .values(
                    role=role,
                )
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated user role  for telegram id: %s", telegram_id)

        except Exception as e:
            logger.error("Error updating user_role: %s", str(e))
            raise

    async def update_users_roles(
            self,
            telegram_ids: list[int],
            role: UserRole,
    ) -> None:
        try:
            stmt = update(UserModel).where(
                UserModel.telegram_id.in_(telegram_ids)
            ).values(
                role=role,
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated user roles for telegram ids: %s", telegram_ids)

        except Exception as e:
            logger.error("Error updating users_roles: %s", str(e))
            raise

    async def get_users_by_role(
            self,
            role: UserRole,
    ) -> list[UserModel]:
        try:
            stmt = select(UserModel).where(
                UserModel.role == role,
                UserModel.is_active == True
            )

            result = await self.session.execute(stmt)
            users = list(result.scalars().all())
            return users

        except Exception as e:
            logger.error("Error getting users by role: %s", str(e))
        raise
