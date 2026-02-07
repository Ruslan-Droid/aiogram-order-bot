import asyncio
import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import UserModel
from app.infrastructure.database.query.user_queries import UserRepository

logger = logging.getLogger(__name__)


async def send_order_notifications(
        bot: Bot,
        session: AsyncSession,
        order_id: int,
        restaurant_name: str,
        phone: str,
        bank: str,
        deliverer: UserModel,
        comment: str,
        delay_seconds: float = 0.06  # 20 сообщений в секунду (меньше лимита Telegram 30/сек)
) -> None:
    try:
        # Получаем активных пользователей (исключая определенные роли и создателя)
        users = await UserRepository(session).get_active_users_except(
            exclude_telegram_id=deliverer.telegram_id
        )

        message_text = (
            f"@{deliverer.username}\n"
            f"📦 <b>Новая заявка #{order_id}</b>\n"
            f"📍 Ресторан: {restaurant_name}\n"
            f"📞 Телефон: <code>{phone}</code>\n"
            f"🏦 Банк: {bank}\n\n"
            f"Комментарий: {comment}\n\n"
            f"<i>Чтобы сделать заказ, перейдите в раздел 'Меню'</i>"
        )

        success_count = 0
        error_count = 0

        # Отправляем сообщения с задержкой
        for user in users:
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=message_text,
                    parse_mode=ParseMode.HTML
                )
                success_count += 1

                # Задержка между сообщениями
                await asyncio.sleep(delay_seconds)

            except TelegramForbiddenError:
                # Пользователь заблокировал бота
                logger.warning("User  blocked the bot", user.telegram_id)
                error_count += 1

            except TelegramRetryAfter as e:
                # Превышение лимитов, ждем указанное время
                logger.warning("Rate limit exceeded. Waiting %s seconds", e.retry_after)
                await asyncio.sleep(e.retry_after)

            except Exception as e:
                logger.error(f"Failed to send notification to %s: %s", user.telegram_id, str(e))
                error_count += 1

        logger.info("Notifications sent: %s successful, %s failed", success_count, error_count)

    except Exception as e:
        logger.error("Error in send_order_notifications: %s", str(e))
