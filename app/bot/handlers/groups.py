import logging
from aiogram import Router, Bot, F
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION, KICKED, LEFT, RESTRICTED, \
    MEMBER, IS_ADMIN
from aiogram.types import ChatMemberUpdated, Message

from sqlalchemy.ext.asyncio import AsyncSession
from fluentogram import TranslatorRunner

from app.bot.filters.chat_type_filters import ChatTypeFilterChatMember
from app.bot.utils.group_utils import update_or_create_group_in_groups_events
from app.infrastructure.database.query.group_queries import GroupChatRepository
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.models.group import GroupModel

logger = logging.getLogger(__name__)

groups_router = Router()
groups_router.my_chat_member.filter(ChatTypeFilterChatMember(chat_type=["group", "supergroup"]))
groups_router.chat_member.filter(ChatTypeFilterChatMember(chat_type=["group", "supergroup"]))


# bot added in chat
@groups_router.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def bot_added_to_group(
        event: ChatMemberUpdated,
        bot: Bot,
        user_row: UserModel,
        i18n: TranslatorRunner,
        session: AsyncSession,
) -> None:
    group: GroupModel = await update_or_create_group_in_groups_events(
        event=event,
        session=session,
        user_row=user_row,
    )

    if event.new_chat_member.status == "administrator":
        await event.answer(text=i18n.get("bot-added-as-admin"))

    elif event.new_chat_member.status in ["member", "restricted"]:
        await event.answer(text=i18n.get("bot-added-not-as-admin"))

    else:
        logger.warning("Bot added with unknown status: %s", event.new_chat_member.status)
        await event.answer(text=i18n.get("bot-added-not-as-admin"))


# bot kicked from chat
@groups_router.my_chat_member(ChatMemberUpdatedFilter(LEAVE_TRANSITION))
async def bot_kicked_from_group(
        event: ChatMemberUpdated,
        user_row: UserModel,
        session: AsyncSession,
) -> None:
    group: GroupModel = await update_or_create_group_in_groups_events(
        event=event,
        session=session,
        is_active=False,
        user_row=user_row,
    )


# group migrate to supergroup
@groups_router.message(F.migrate_to_chat_id)
async def group_to_supergroup_migration(
        message: Message,
        session: AsyncSession,
) -> None:
    group_repo = GroupChatRepository(session)

    old_chat_id = message.chat.id
    new_chat_id = message.migrate_to_chat_id
    logger.warning("Migration in group: %s -> %s", old_chat_id, new_chat_id)

    await group_repo.update_chat_id_in_database(old_chat_id, new_chat_id)


# bot get admin rights
@groups_router.my_chat_member(
    ChatMemberUpdatedFilter((KICKED | LEFT | RESTRICTED | MEMBER) >> IS_ADMIN)
)
async def bot_admin_promoted(
        event: ChatMemberUpdated,
        bot: Bot,
        user_row: UserModel,
        i18n: TranslatorRunner,
        session: AsyncSession,
) -> None:
    group = await update_or_create_group_in_groups_events(
        event=event,
        session=session,
        user_row=user_row,
    )
    await event.answer(text=i18n.get("bot-get-admin-rights"))


# bot lost admin rights
@groups_router.my_chat_member(
    ChatMemberUpdatedFilter((KICKED | LEFT | RESTRICTED | MEMBER) << IS_ADMIN)
)
async def bot_admin_demoted(
        event: ChatMemberUpdated,
        session: AsyncSession,
        user_row: UserModel,
        i18n: TranslatorRunner,
) -> None:
    group: GroupModel = await update_or_create_group_in_groups_events(
        event=event,
        session=session,
        user_row=user_row,
    )
    await event.answer(text=i18n.get("bot-lost-admin-rights"))


# user get admin rights
@groups_router.chat_member(
    ChatMemberUpdatedFilter((KICKED | LEFT | RESTRICTED | MEMBER) >> IS_ADMIN)
)
async def user_admin_promoted(
        event: ChatMemberUpdated,
        user_row: UserModel,
        session: AsyncSession,
        i18n: TranslatorRunner,
) -> None:
    group: GroupModel = await update_or_create_group_in_groups_events(
        event=event,
        session=session,
        user_row=user_row,
    )
    await event.answer(
        text=i18n.get("user-get-admin-rights", name=event.from_user.first_name)
    )


# user lost admin rights
@groups_router.chat_member(
    ChatMemberUpdatedFilter((KICKED | LEFT | RESTRICTED | MEMBER) << IS_ADMIN)
)
async def user_admin_demoted(
        event: ChatMemberUpdated,
        user_row: UserModel,
        session: AsyncSession,
        i18n: TranslatorRunner,
) -> None:
    group: GroupModel = await update_or_create_group_in_groups_events(
        event=event,
        session=session,
        user_row=user_row,
    )
    await event.answer(
        text=i18n.get("user-lost-admin-rights", name=event.from_user.first_name)
    )
