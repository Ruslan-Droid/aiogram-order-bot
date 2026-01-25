import re

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Select, Radio

from app.bot.dialogs.flows.delivery_requests.states import DeliverySG
from app.infrastructure.database.enums.payment_methods import PaymentMethod
from app.infrastructure.database.models import UserModel
from app.infrastructure.database.query.order_queries import OrderRepository


async def on_restaurant_selected(
        callback: CallbackQuery,
        button: Select,
        dialog_manager: DialogManager,
        item_id: int,
) -> None:
    dialog_manager.dialog_data.update({
        "restaurant_id": dialog_manager.dialog_data["restaurant_id"],
        "restaurant_name": dialog_manager.dialog_data["restaurant_name"]
    })
    print(dialog_manager.dialog_data["restaurant_id"])
    print(dialog_manager.dialog_data["restaurant_name"])

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
    dialog_manager.current_context().dialog_data['phone'] = text

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


async def bank_selected(
        callback: CallbackQuery,
        widget: Radio,
        dialog_manager: DialogManager,
        item_id: str
) -> None:
    """
    Обработка выбора банка
    """
    # Получаем выбранный банк по ID
    try:
        selected_bank = PaymentMethod(item_id)
    except ValueError:
        await callback.answer("❌ Ошибка выбора банка")
        return

    # Сохраняем банк в dialog_data
    dialog_manager.current_context().dialog_data['bank'] = selected_bank.value

    # Можно сохранить предпочтение пользователя в БД

    await callback.answer(f"✅ Выбран банк: {selected_bank.value}")

    # Переходим к подтверждению заявки
    await dialog_manager.switch_to(DeliverySG.create_confirm)


async def create_order(
        callback: CallbackQuery,
        button: Button,
        manager: DialogManager
) -> None:
    session = manager.middleware_data["session"]
    user: UserModel = manager.middleware_data["user_row"]

    order = await OrderRepository(session).create_order(
        restaurant_id=manager.dialog_data["restaurant_id"],
        creator_id=user.id,
        phone_number=manager.dialog_data["phone"],
        payment_method=manager.dialog_data["bank"]
    )

    # Отправка уведомлений всем активным пользователям
    # TODO
    # Здесь нужно реализовать рассылку

    await callback.answer(f"✅ Заявка #{order.id} создана!", show_alert=True)
    await manager.done()


async def delete_order(
        callback: CallbackQuery,
        widget: Select, manager: DialogManager,
        order_id: str
) -> None:
    session = manager.middleware_data["session"]

    await OrderRepository(session).delete_order(int(order_id))
    await callback.answer("✅ Заявка удалена!", show_alert=True)
    await manager.switch_to(DeliverySG.delete_list)
