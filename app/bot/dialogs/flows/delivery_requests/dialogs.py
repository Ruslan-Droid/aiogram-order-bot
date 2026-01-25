from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Row, Column, SwitchTo, Button,
    Back, Select, ScrollingGroup, Cancel, Radio
)
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram_dialog.widgets.input import TextInput

from app.bot.dialogs.flows.delivery_requests.getters import get_restaurants, get_today_orders, \
    getter_create_enter_contact, getter_select_bank
from app.bot.dialogs.flows.delivery_requests.handlers import create_order, delete_order, \
    user_number_button_click, validate_phone, process_success_phone, process_error_phone, bank_selected, \
    on_restaurant_selected
from app.bot.dialogs.flows.delivery_requests.states import DeliverySG

delivery_dialog = Dialog(
    # Главное окно заявок 🚚
    Window(
        Const("🚚 Заявки на доставку"),
        Column(
            SwitchTo(
                Const("➕ Создать заявку"),
                id="create_request",
                state=DeliverySG.create_select_restaurant
            ),
            SwitchTo(
                Const("🗑️ Удалить заявку"),
                id="delete_request",
                state=DeliverySG.delete_list
            ),
            SwitchTo(
                Const("📋 Список заявок"),
                id="list_requests",
                state=DeliverySG.delivery_list
            ),
        ),
        Cancel(Const("⬅️ На главную")),
        state=DeliverySG.main
    ),

    # ➕ Создать заявку -> Окно выбора ресторана для создания заявки
    Window(
        Const("Выберите заведение для заявки:"),
        ScrollingGroup(
            Select(
                Format("{item[name]}"),
                id="select_restaurant",
                item_id_getter=lambda x: x["id"],
                items="restaurants",
                on_click=on_restaurant_selected,
            ),
            id="restaurants_group",
            width=1,
            height=5,
        ),
        Back(Const("⬅️ Назад")),
        state=DeliverySG.create_select_restaurant,
        getter=get_restaurants,
    ),

    # ➕ Создать заявку -> Окно выбора ресторана для создания заявки -> 📞 Окно ввода контактов
    Window(
        Const("📞 Введите номер телефона:\n\n"
              "Пример: <code>89161234567</code>"),
        Button(
            text=Format("{number}"),
            id="number_button_from_user",
            on_click=user_number_button_click,
            when=lambda data, widget, manager: data.get("number") is not None,
        ),
        TextInput(
            id="number_input",
            type_factory=validate_phone,
            on_success=process_success_phone,
            on_error=process_error_phone,
        ),
        Back(Const("⬅️ Назад")),
        getter=getter_create_enter_contact,
        state=DeliverySG.create_enter_contact
    ),

    # ➕ Создать заявку -> Окно выбора ресторана для создания заявки -> 📞 Окно ввода контактов -> окно выбора банка
    Window(
        Const("Выберите банк для оплаты:"),
        Column(
            Radio(
                checked_text=Format("🔘 {item[0]}"),
                unchecked_text=Format("⚪️ {item[0]}"),
                # Отображаем название банка
                id="bank_radio",
                item_id_getter=lambda item: item[0],  # Используем значение Enum как id
                items="banks",  # Будет получено из геттера
                on_click=bank_selected,  # Обработчик выбора банка
            )
        ),
        Button(
            text=Const("Сохранить"),
            id="save_button",
            on_click=lambda x: x,
        ),
        Back(Const("⬅️ Назад")),
        getter=getter_select_bank,
        state=DeliverySG.create_select_bank
    ),
    # Окно подтверждения
    Window(
        Multi(
            Format("📋 Подтверждение заявки:"),
            Format("Заведение: {dialog_data[restaurant_name]}"),
            Format("Телефон: {dialog_data[phone]}"),
            Format("Банк: {dialog_data[bank].value}"),
            Const(""),
            Const("Создать заявку?")
        ),
        Row(
            Button(Const("✅ Создать"), id="confirm_create", on_click=create_order),
            Back(Const("❌ Отмена"))
        ),
        state=DeliverySG.create_confirm
    ),
    # 🗑️ Удалить заявку
    Window(
        Const("🗑️ Выберите заявку для удаления:"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="delete_order",
                item_id_getter=lambda x: x[1],
                items="orders",
                on_click=delete_order
            ),
            id="orders_group",
            width=1,
            height=5,
        ),
        Back(Const("⬅️ Назад")),
        state=DeliverySG.delete_list,
        getter=get_today_orders
    ),
)
