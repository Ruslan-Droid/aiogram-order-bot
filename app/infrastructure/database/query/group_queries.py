import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.infrastructure.database.models.group import GroupModel

logger = logging.getLogger(__name__)


class GroupChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_or_update_group(
            self,
            telegram_chat_id: int,
            title: str | None,
            chat_type: str,
            added_by_telegram_id: int | None,
            bot_status: str,
            admin_permissions: dict | None,
            language_code: str | None = "en",
            is_active: bool = True,
            tz_region: str | None = "Europe/Moscow",
    ) -> GroupModel:
        insert_stmt = pg_insert(GroupModel).values(
            group_telegram_id=telegram_chat_id,
            title=title,
            chat_type=chat_type,
            added_by_telegram_id=added_by_telegram_id,
            bot_status=bot_status,
            admin_permissions=admin_permissions,
            is_active=is_active,
            language_code=language_code,
            tz_region=tz_region,
        )

        update_dict = {
            'title': title,
            'chat_type': chat_type,
            'bot_status': bot_status,
            'admin_permissions': admin_permissions,
            'is_active': is_active,
        }

        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=['group_telegram_id'],
            set_=update_dict
        ).returning(GroupModel)

        try:
            result = await self.session.execute(on_conflict_stmt)
            group = result.scalar_one()
            await self.session.commit()
            logger.info("Created/Updated group with chat id: %s", telegram_chat_id)
            return group

        except Exception as e:
            await self.session.rollback()
            logger.error("Error creating/updating group by chat id: %s, error: %s", telegram_chat_id, str(e))
            raise

    async def get_group_by_chat_id(
            self,
            telegram_chat_id: int,
    ) -> GroupModel | None:
        try:
            stmt = select(GroupModel).filter(GroupModel.group_telegram_id == telegram_chat_id)
            group = await self.session.scalar(stmt)

            if group:
                logger.info("Fetched group by telegram id: %s", telegram_chat_id)
            else:
                logger.info("User not found by telegram id: %s", telegram_chat_id)
            return group

        except Exception as e:
            logger.error("Error getting user by telegram id %s: %s", telegram_chat_id, str(e))
            raise

    async def update_group_language(
            self,
            telegram_chat_id: int,
            language_code: str
    ) -> None:
        try:
            stmt = (
                update(GroupModel)
                .where(GroupModel.group_telegram_id == telegram_chat_id)
                .values(language_code=language_code)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated coordinates for telegram id: %s", telegram_chat_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating coordinates for telegram id: %s error: %s", telegram_chat_id, str(e))
            raise

    async def update_activity_status_for_group(
            self,
            chat_id: int,
            status: bool
    ) -> None:
        try:
            stmt = (
                update(GroupModel)
                .where(GroupModel.group_telegram_id == chat_id)
                .values(is_active=status)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Updated is_active status for group id: %s", chat_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating is_active status for group id: %s error: %s", chat_id, str(e))
            raise

    async def update_chat_id_in_database(
            self,
            old_chat_id: int,
            new_chat_id: int
    ) -> None:
        try:
            await self.session.execute(
                update(GroupModel)
                .where(GroupModel.group_telegram_id == old_chat_id)
                .values(
                    group_telegram_id=new_chat_id,
                    chat_type="supergroup"
                )
            )
            await self.session.commit()
            logger.info(f"Migration group: %s -> %s", old_chat_id, new_chat_id)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error while migration group: %s -> %s, error: %s", old_chat_id, new_chat_id, str(e))

    async def update_group_timezone(
            self,
            group_telegram_id: int,
            timezone: str
    ) -> None:
        try:
            await self.session.execute(
                update(GroupModel)
                .where(GroupModel.group_telegram_id == group_telegram_id)
                .values(
                    tz_region=timezone,
                )
            )
            await self.session.commit()
            logger.info(f"Time zone updated for group: %s, timezone: %s", group_telegram_id, timezone)

        except Exception as e:
            await self.session.rollback()
            logger.error("Error while updating timezone for group: %s, error: %s", group_telegram_id, str(e))
