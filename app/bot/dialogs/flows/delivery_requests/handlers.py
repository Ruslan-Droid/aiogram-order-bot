import re

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput
from aiogram_dialog.widgets.kbd import Button, Select, ManagedRadio
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.dialogs.flows.delivery_requests.states import DeliverySG
from app.bot.dialogs.flows.delivery_requests.utils import send_order_notifications, send_status_notification_to_all
from app.bot.dialogs.utils.message_with_all_carts_and_items import send_carts_summary_message
from app.infrastructure.database.enums import CartStatus
from app.infrastructure.database.enums.order_statuses import OrderStatus
from app.infrastructure.database.enums.payment_methods import PaymentMethod
from app.infrastructure.database.models import UserModel
from app.infrastructure.database.query.cart_queries import CartRepository
from app.infrastructure.database.query.order_queries import OrderRepository
from app.infrastructure.database.query.user_queries import UserRepository


async def on_restaurant_selected(
        callback: CallbackQuery,
        button: Select,
        dialog_manager: DialogManager,
        item_id: int,
        **kwargs,
) -> None:
    restaurants = dialog_manager.dialog_data["_restaurants_cache"]

    for rest in restaurants:
        if rest["id"] == int(item_id):
            dialog_manager.dialog_data["restaurant_id"] = int(item_id)
            dialog_manager.dialog_data["restaurant_name"] = rest["name"]
            break

    await dialog_manager.switch_to(DeliverySG.create_enter_contact)


async def user_number_button_click(
        callback: CallbackQuery,
        widget: Button,
        manager: DialogManager
) -> None:
    await manager.switch_to(DeliverySG.create_select_bank)


def validate_phone(text: str) -> str:
    phone = text.strip()

    # Очищаем номер от пробелов, скобок, дефисов
    phone_clean = re.sub(r'[\s\-\(\)]', '', phone)

    # Проверяем, что остались только цифры
    if not phone_clean.isdigit():
        raise ValueError("Номер телефона должен содержать только цифры")

    # Проверяем различные форматы российских номеров
    if len(phone_clean) == 10 and phone_clean[0] in ['9', '4']:
        # Формат 9161234567 -> 89161234567
        phone_clean = '8' + phone_clean
    elif len(phone_clean) == 11 and phone_clean[0] in ['7', '8']:
        # Формат 79161234567 -> 89161234567
        if phone_clean[0] == '7':
            phone_clean = '8' + phone_clean[1:]
    elif len(phone_clean) == 12 and phone_clean[:2] == '+7':
        # Формат +79161234567 -> 89161234567
        phone_clean = '8' + phone_clean[2:]
    else:
        raise ValueError("Неверный формат номера. Используйте российский номер\n"
                         "Примеры: 89161234567, +79161234567, 9161234567")

    # Дополнительная проверка: российские номера начинаются с 8 или +7
    if not phone_clean.startswith('8'):
        raise ValueError("Неверный российский номер")

    # Проверяем, что номер имеет правильную длину (11 цифр)
    if len(phone_clean) != 11:
        raise ValueError("Номер должен содержать 11 цифр")

    return phone_clean


async def process_success_phone(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str
) -> None:
    # Сохраняем номер в dialog_data
    dialog_manager.dialog_data['phone'] = text

    # Переходим к выбору банка
    await dialog_manager.switch_to(DeliverySG.create_select_bank)


async def process_error_phone(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: Exception
) -> None:
    error_message = str(error)

    await message.answer(
        f"❌ Ошибка: {error_message}\n\n"
        f"📞 Введите номер телефона:\n"
        f"Пример: <code>89161234567</code>"
    )


async def user_bank_button_on_click(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(DeliverySG.create_confirm)


async def bank_selected(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager,
) -> None:
    # Получаем выбранный банк по ID
    radio_lang: ManagedRadio = dialog_manager.find("bank_radio")
    item_id = radio_lang.get_checked()
    print(item_id)

    try:
        selected_bank = PaymentMethod(item_id)
    except ValueError:
        await callback.answer("❌ Ошибка выбора банка")
        return

    # Сохраняем банк в dialog_data
    dialog_manager.dialog_data['bank'] = selected_bank.value

    # Можно сохранить предпочтение пользователя в БД

    await callback.answer(f"✅ Выбран банк: {selected_bank.value}")

    # Переходим к подтверждению заявки
    await dialog_manager.switch_to(DeliverySG.create_confirm)


async def on_comment_entered_for_delivery(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager
):
    dialog_manager.dialog_data["comment"] = message.text

    await dialog_manager.switch_to(DeliverySG.create_confirm)


async def create_order(
        callback: CallbackQuery,
        button: Button,
        manager: DialogManager
) -> None:
    session = manager.middleware_data["session"]
    user: UserModel = manager.middleware_data["user_row"]

    restaurant_name = manager.dialog_data["restaurant_name"]
    restaurant_id = manager.dialog_data["restaurant_id"]
    phone = manager.dialog_data["phone"]
    bank = manager.dialog_data["bank"]
    comment = manager.dialog_data.get("comment", "Отсутствует")

    order = await OrderRepository(session).create_order(
        restaurant_id=restaurant_id,
        creator_id=user.id,
        phone_number=phone,
        payment_method=bank,
        notes=comment,
    )

    await UserRepository(session).update_phone_and_bank(
        telegram_id=user.telegram_id,
        phone_number=phone,
        bank=bank,
    )

    await send_order_notifications(
        bot=callback.bot,
        deliverer=user,
        session=session,
        order_id=order.id,
        restaurant_name=restaurant_name,
        phone=phone,
        bank=bank,
        comment=comment,
    )

    await callback.message.answer(f"✅ Заявка #{order.id} в <b>{restaurant_name}</b> создана!")
    await manager.done()


async def delete_order(
        callback: CallbackQuery,
        widget: Select, manager: DialogManager,
        order_id: int
) -> None:
    session = manager.middleware_data["session"]

    await OrderRepository(session).delete_order(int(order_id))
    await callback.answer("✅ Заявка удалена!", show_alert=True)
    await manager.switch_to(DeliverySG.main)


async def on_order_selected(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
):
    manager.dialog_data["selected_order_id"] = int(item_id)
    # Переходим к выбору статуса
    await manager.switch_to(DeliverySG.delivery_list_choose_status)


async def on_status_selected(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
):
    session: AsyncSession = manager.middleware_data["session"]
    order_id = manager.dialog_data.get("selected_order_id")
    user: UserModel = manager.middleware_data["user_row"]

    new_status = OrderStatus[item_id]

    # Получаем текущий статус заказа
    order = await OrderRepository(session).get_order_with_carts(order_id)
    old_status = order.status if order else None

    # Обновляем статус заказа
    await OrderRepository(session).update_order_status(order_id, status=new_status)

    # 2. Отправляем всем сообщение о смене статуса
    if order and old_status:
        await send_status_notification_to_all(
            bot=callback.bot,
            session=session,
            order=order,
            old_status=old_status,
            new_status=new_status,
            deliverer=user,
        )

    # 3. При смене статуса на "Собран" отправляем все корзины выезднику
    if new_status == OrderStatus.COLLECTED and order:
        await send_carts_summary_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            order=order,
        )

    # 4. При смене статуса на "Доставлен" обновляем статусы всех корзин
    if new_status == OrderStatus.DELIVERED and order:
        for cart in order.carts:
            await CartRepository(session).update_cart_status(cart.id, CartStatus.DELIVERED)

    await callback.answer(f"Статус обновлен на: {new_status.value}", show_alert=True)
    await manager.switch_to(DeliverySG.delivery_list)