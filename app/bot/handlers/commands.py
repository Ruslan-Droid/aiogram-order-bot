from aiogram import Bot, Router
from aiogram.enums import BotCommandScopeType
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BotCommandScopeChat, LinkPreviewOptions

from aiogram_dialog import DialogManager, StartMode
from fluentogram import TranslatorRunner
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.dialogs.flows.settings.states import SettingsSG
from app.bot.dialogs.flows.start.states import StartSG
from app.bot.filters.chat_type_filters import ChatTypeFilterMessage, ChatTypeFilterCallback
from app.bot.keyboards.inline_keyboards import get_help_keyboard
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.query.user_queries import UserRepository
from app.bot.keyboards.menu_button import get_main_menu_commands

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
    if user_row is None:
        user_rep: UserRepository = UserRepository(session)
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

    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)


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
