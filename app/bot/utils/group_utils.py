from aiogram.types import ChatMemberUpdated
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.enums.group_data import GroupData, extract_group_data
from app.infrastructure.database.models.group import GroupModel
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.query.group_queries import GroupChatRepository


async def update_or_create_group_in_groups_events(
        event: ChatMemberUpdated,
        session: AsyncSession,
        user_row: UserModel | None,
        is_active: bool = True,
) -> GroupModel:
    if user_row and user_row.language_code:
        language_code = user_row.language_code
    else:
        language_code = "en"

    if user_row and user_row.tz_region:
        tz_region = user_row.tz_region
    else:
        tz_region = "Europe/Moscow"

    group_data: GroupData = extract_group_data(event)

    group_repo = GroupChatRepository(session)
    group = await group_repo.create_or_update_group(
        telegram_chat_id=group_data.chat_id,
        title=group_data.title,
        chat_type=group_data.chat_type,
        added_by_telegram_id=group_data.added_by_telegram_id,
        bot_status=group_data.bot_status,
        admin_permissions=group_data.bot_permissions,
        is_active=is_active,
        language_code=language_code,
        tz_region=tz_region,
    )
    return group
