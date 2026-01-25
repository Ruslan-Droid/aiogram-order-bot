import asyncio
import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import UserModel
from app.infrastructure.database.query.user_queries import UserRepository

logger = logging.getLogger(__name__)


class AdminActionCallback(CallbackData, prefix="admin"):
    action: str  # "authorize", "reject"
    user_id: int


async def notify_admins_about_new_user(
        bot: Bot,
        session: AsyncSession,
        new_user: UserModel,
):
    try:
        admins = await UserRepository(session).get_active_admins()

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=AdminActionCallback(
                        action="reject",
                        user_id=new_user.telegram_id
                    ).pack()
                ),
                InlineKeyboardButton(
                    text="✅ Авторизовать",
                    callback_data=AdminActionCallback(
                        action="authorize",
                        user_id=new_user.telegram_id
                    ).pack()
                ),

            ]
        ])

        # Формируем текст сообщения
        user_info = (
            f"👤 <b>Новый пользователь</b>\n\n"
            f"TELEGRAM ID: <code>{new_user.telegram_id}</code>\n"
            f"Имя: {new_user.first_name or 'Не указано'}\n"
            f"Фамилия: {new_user.last_name or 'Не указано'}\n"
            f"Username: @{new_user.username or 'Не указано'}\n"
            f"Язык: {new_user.language_code or 'Не указан'}\n"
            f"Дата регистрации: {new_user.created_at.strftime('%d.%m.%Y %H:%M')}"
        )

        # Отправляем сообщение всем админам
        for admin in admins:
            try:
                await bot.send_message(
                    chat_id=admin.telegram_id,
                    text=user_info,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                await asyncio.sleep(0.05)

            except Exception as e:
                logger.error("Failed to send notification to admin %s: %s", admin.telegram_id, str(e))

    except Exception as e:
        logger.error("Error in notify_admins_about_new_user: %s", str(e))
