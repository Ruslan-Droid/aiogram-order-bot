from aiogram import Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Select, Button
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.dialogs.flows.cart.states import CartSG
from app.bot.dialogs.utils.message_with_all_carts_and_items import send_carts_summary_message
from app.infrastructure.database.enums import CartStatus
from app.infrastructure.database.models import CartModel, DeliveryOrderModel
from app.infrastructure.database.query.cart_queries import CartRepository, CartItemRepository
from app.infrastructure.database.query.order_queries import OrderRepository


async def on_comment_entered(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager
):
    session = dialog_manager.middleware_data["session"]
    cart_id = dialog_manager.dialog_data.get("cart_id")

    await CartRepository(session).update_cart_notes(cart_id, message.text)

    await message.answer("📝 Комментарий добавлен!")
    await dialog_manager.switch_to(CartSG.main)


async def on_order_selected(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
):
    session = manager.middleware_data["session"]
    cart_id = manager.dialog_data.get("cart_id")

    await CartRepository(session).attach_cart_to_order(cart_id, int(item_id))

    await callback.answer(f"✅ Корзина добавлена к заказу #{item_id}")
    await manager.switch_to(CartSG.main)


async def on_cart_item_selected(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
):
    """Выбор блюда для редактирования количества"""
    # Сохраняем ID блюда и переходим к окну редактирования количества
    manager.dialog_data["edit_dish_id"] = int(item_id)
    await manager.switch_to(CartSG.edit_cart_item)


async def on_update_amount(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager
):
    """Обработчик ввода нового количества"""
    session: AsyncSession = dialog_manager.middleware_data["session"]
    cart_id = dialog_manager.dialog_data.get("cart_id")
    dish_id = dialog_manager.dialog_data.get("edit_dish_id")

    try:
        new_amount = int(message.text)
        if new_amount < 0:
            await message.answer("❌ Количество не может быть отрицательным")
            return

        if new_amount == 0:
            # Удаляем блюдо из корзины
            await CartItemRepository(session).remove_cart_item(cart_id, dish_id)
            await message.answer("✅ Блюдо удалено из корзины")
        else:
            # Обновляем количество
            cart_item = await CartItemRepository(session).get_cart_item(cart_id, dish_id)
            if cart_item:
                await CartItemRepository(session).update_item_amount(
                    cart_id, dish_id, new_amount
                )
                await message.answer(f"✅ Количество обновлено: {new_amount}")

        # Обновляем общую сумму корзины
        await CartRepository(session).update_cart_total_price(cart_id)

        # Возвращаемся к редактированию корзины
        await dialog_manager.switch_to(CartSG.edit_cart)

    except ValueError:
        await message.answer("❌ Пожалуйста, введите число")
    except Exception:
        await message.answer("❌ Произошла ошибка")


async def on_order_for_delivery_selected(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
):
    """Выбор заказа для просмотра всех корзин в нём"""
    manager.dialog_data["selected_order_id"] = int(item_id)
    await manager.switch_to(CartSG.show_carts_for_order)


async def selected_order_from_history(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item: str
) -> None:
    session: AsyncSession = manager.middleware_data["session"]
    cart: CartModel = await CartRepository(session=session).get_cart_by_id(int(item))

    if cart.status == CartStatus.ORDERED:
        manager.dialog_data["cart_id"] = cart.id
        await manager.switch_to(CartSG.edit_cart)
    else:
        await callback.answer("Заказ уже собран и не может быть отредактирован.\n"
                              "Ожидайте доставку!")


async def send_all_carts_message(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager,
) -> None:
    """Отправить сообщение со всеми корзинами в заказе"""
    try:
        session: AsyncSession = dialog_manager.middleware_data["session"]
        order_id = dialog_manager.dialog_data.get("selected_order_id")

        if not order_id:
            await callback.answer("Заказ не выбран", show_alert=True)
            return

        # Получаем заказ с корзинами
        order = await OrderRepository(session).get_order_with_carts(order_id)

        if not order or not order.carts:
            await callback.answer("Заказ или корзины не найдены", show_alert=True)
            return

        # Получаем chat_id для отправки сообщения
        chat_id = callback.message.chat.id

        # Формируем сообщение со всеми корзинами
        await send_carts_summary_message(
            bot=callback.bot,
            chat_id=chat_id,
            order=order,
        )
        await callback.answer()

    except Exception:
        await callback.answer("Ошибка при отправке сообщения", show_alert=True)

