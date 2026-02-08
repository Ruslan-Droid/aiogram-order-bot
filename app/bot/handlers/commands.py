import logging

from datetime import datetime
from aiogram import Bot, Router
from aiogram.enums import BotCommandScopeType
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BotCommandScopeChat, LinkPreviewOptions, CallbackQuery

from aiogram_dialog import DialogManager, StartMode
from fluentogram import TranslatorRunner
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.dialogs.flows.main_menu.states import MainMenuSG
from app.bot.dialogs.flows.settings.states import SettingsSG
from app.bot.filters.chat_type_filters import ChatTypeFilterMessage, ChatTypeFilterCallback
from app.bot.keyboards.inline_keyboards import get_help_keyboard
from app.bot.utils.notifications_for_admins import notify_admins_about_new_user, AdminActionCallback
from app.infrastructure.database.enums.user_roles import UserRole
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.query.user_queries import UserRepository
from app.bot.keyboards.menu_button import get_main_menu_commands

logger = logging.getLogger(__name__)

commands_router = Router()
commands_router.message.filter(ChatTypeFilterMessage("private"))
commands_router.callback_query.filter(ChatTypeFilterCallback("private"))


@commands_router.message(CommandStart())
async def command_start_handler(
        message: Message,
        dialog_manager: DialogManager,
        bot: Bot,
        i18n: TranslatorRunner,
        session: AsyncSession,
        user_row: UserModel | None,
) -> None:
    user_rep: UserRepository = UserRepository(session)
    if user_row is None:
        user_row: UserModel = await user_rep.create_or_update_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code,
        )

        await notify_admins_about_new_user(bot, session, user_row)
    else:
        user_row: UserModel = await user_rep.create_or_update_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code,
        )

    await bot.set_my_commands(
        commands=get_main_menu_commands(i18n=i18n),
        scope=BotCommandScopeChat(
            type=BotCommandScopeType.CHAT, chat_id=message.from_user.id
        ),
    )

    if user_row.role == UserRole.UNKNOWN:
        username = message.from_user.full_name or message.from_user.username or i18n.stranger()
        await message.answer(i18n.bot.description(username=username))
        await dialog_manager.start(state=MainMenuSG.menu, mode=StartMode.RESET_STACK)

    else:
        await dialog_manager.start(state=MainMenuSG.menu, mode=StartMode.RESET_STACK)


@commands_router.message(Command("main_menu"))
async def command_main_menu_handler(
        message: Message,
        dialog_manager: DialogManager,
        bot: Bot,
) -> None:
    await dialog_manager.start(state=MainMenuSG.menu)


@commands_router.message(Command("help"))
async def command_help_handler(
        message: Message,
        i18n: TranslatorRunner
) -> None:
    await message.answer(
        text=i18n.get("help-command"),
        link_preview_options=LinkPreviewOptions(
            url="https://github.com/Ruslan-Droid/aiogram-weather-bot",
            prefer_small_media=True,
        ),
        reply_markup=get_help_keyboard(i18n)
    )


@commands_router.message(Command("lang"))
async def process_lang_command_sg(
        message: Message,
        dialog_manager: DialogManager,
) -> None:
    await dialog_manager.start(state=SettingsSG.lang)


@commands_router.callback_query(AdminActionCallback.filter())
async def handle_admin_action(
        callback_query: CallbackQuery,
        callback_data: AdminActionCallback,
        session: AsyncSession,
        bot: Bot
):
    action = callback_data.action
    user_id = callback_data.user_id

    user_rep = UserRepository(session)
    target_user = await user_rep.get_user_by_telegram_id(user_id)

    if not target_user:
        await callback_query.answer("Пользователь не найден")
        await callback_query.message.edit_text(
            f"{callback_query.message.text}\n\n❌ Пользователь не найден в базе"
        )
        return

    if target_user.role != UserRole.UNKNOWN:
        # Уже обработан другим админом
        role_text = {
            UserRole.MEMBER: "авторизован",
            UserRole.BANNED: "заблокирован",
        }.get(target_user.role, "обработан")

        await callback_query.answer(f"Пользователь уже {role_text}", show_alert=True)

        # Обновляем текст сообщения, убираем кнопки
        await callback_query.message.edit_text(
            f"{callback_query.message.text}\n\n"
            f"⚠️ <b>Статус изменен другим администратором</b>\n"
            f"Текущая роль: {target_user.role.value}\n"
            f"Время проверки: {datetime.now().strftime('%H:%M:%S')}",
            reply_markup=None  # Убираем кнопки
        )
        return

    if action == "authorize":
        await UserRepository(session).update_user_role(telegram_id=target_user.telegram_id, role=UserRole.MEMBER)
        # Отправляем уведомление пользователю
        try:
            await bot.send_message(
                chat_id=user_id,
                text="🎉 Ваша заявка одобрена! Теперь у вас есть доступ к боту."
            )

        except Exception as e:
            logger.error(f"Failed to notify user %s: %s", user_id, str(e))

        # Обновляем сообщение админу
        await callback_query.message.edit_text(
            f"{callback_query.message.text}\n\n✅ <b>Пользователь авторизован</b>\n"
            f"Роль: {UserRole.MEMBER.value}\n"
            f"Время: {datetime.now().strftime('%H:%M:%S')}",
            parse_mode="HTML"
        )
        await callback_query.answer("Пользователь авторизован")

    elif action == "reject":
        await user_rep.update_user_role(telegram_id=target_user.telegram_id, role=UserRole.BANNED)
        try:
            await bot.send_message(
                chat_id=user_id,
                text="❌ Ваша заявка была отклонена администратором."
            )
        except Exception as e:
            logger.error("Failed to notify user %s: %s", user_id, str(e))

        # Обновляем сообщение админу
        await callback_query.message.edit_text(
            f"{callback_query.message.text}\n\n❌ <b>Пользователь отклонен</b>\n"
            f"Время: {datetime.now().strftime('%H:%M:%S')}",
            parse_mode="HTML"
        )
        await callback_query.answer("Пользователь отклонен")
