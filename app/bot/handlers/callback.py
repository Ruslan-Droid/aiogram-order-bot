from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.dialogs.utils.message_with_all_carts_and_items import send_grouped_items_message
from app.bot.filters.chat_type_filters import ChatTypeFilterMessage, ChatTypeFilterCallback

callback_router = Router()
callback_router.message.filter(ChatTypeFilterMessage("private"))
callback_router.callback_query.filter(ChatTypeFilterCallback("private"))

@callback_router.callback_query(F.data.startswith("order_summary:"))
async def handle_order_summary(
        callback: CallbackQuery,
        session: AsyncSession
) -> None:
    """Обработчик кнопки сводного списка товаров"""
    try:
        order_id = int(callback.data.split(":")[1])
        await send_grouped_items_message(callback, order_id, session)

    except Exception as e:
        await callback.answer("Ошибка", show_alert=True)
