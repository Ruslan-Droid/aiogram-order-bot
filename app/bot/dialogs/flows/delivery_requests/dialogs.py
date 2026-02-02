from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Row, Column, SwitchTo, Button,
    Back, Select, ScrollingGroup, Cancel, Radio
)
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram_dialog.widgets.input import TextInput, MessageInput

from app.bot.dialogs.flows.delivery_requests.getters import get_restaurants, get_today_orders, \
    getter_create_enter_contact, getter_select_bank, getter_confirm_create, get_order_statuses
from app.bot.dialogs.flows.delivery_requests.handlers import create_order, delete_order, \
    user_number_button_click, validate_phone, process_success_phone, process_error_phone, bank_selected, \
    on_restaurant_selected, user_bank_button_on_click, on_order_selected, on_status_selected, \
    on_comment_entered_for_delivery
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
    #########################################################################
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
                id="bank_radio",
                item_id_getter=lambda item: item[0],
                items="banks",
            )
        ),
        Row(
            Back(Const("⬅️ Назад")),
            Button(
                text=Format("{preferred_bank}"),
                id="preferred_bank_button_from_user",
                on_click=user_bank_button_on_click,
                when=lambda data, widget, manager: data.get("preferred_bank") is not None,
            ),
            Button(
                text=Const("✅ Сохранить"),
                id="save_button",
                on_click=bank_selected,
            ),
        ),
        getter=getter_select_bank,
        state=DeliverySG.create_select_bank
    ),

    # Окно подтверждения
    Window(
        Format("📋 Подтверждение заявки:\n"
               "Заведение: {restaurant_name}\n"
               "Телефон: {phone}\n"
               "Банк: {bank}\n\n"
               "Комментарий: {comment}\n"
               "Создать заявку?"),
        SwitchTo(
            Const("✍️ Добавить комментарий"),
            id="go_to_input_commet",
            state=DeliverySG.input_commet,
        ),
        Row(
            Back(Const("❌ Отмена")),

            Button(
                Const("✅ Создать"),
                id="confirm_create",
                on_click=create_order
            ),
        ),
        getter=getter_confirm_create,
        state=DeliverySG.create_confirm
    ),

    # 📝 Окно добавления комментария
    Window(
        Const("✍️ <b>Введите комментарий к заказу:</b>"),
        MessageInput(
            func=on_comment_entered_for_delivery,
            content_types=["text"]
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="go_to_main_window_button",
                 state=DeliverySG.create_confirm, ),
        state=DeliverySG.input_commet,
    ),

    #########################################################################
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
        SwitchTo(Const("⬅️ Назад"), state=DeliverySG.main, id="back_button"),
        state=DeliverySG.delete_list,
        getter=get_today_orders
    ),
    #########################################################################
    # today orders list
    Window(
        Const("Выберите заявку для изменения статуса:"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="select_order",
                item_id_getter=lambda x: x[1],
                items="orders",
                on_click=on_order_selected,
            ),
            id="order_list",
            width=1,
            height=5,
        ),
        SwitchTo(Const("⬅️ Назад"), state=DeliverySG.main, id="back_button"),
        state=DeliverySG.delivery_list,
        getter=get_today_orders
    ),
    # choosing status for order
    Window(
        Const("🔄 Выберите статус для заказа:"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="select_status",
                item_id_getter=lambda x: x[1],
                items="statuses",
                on_click=on_status_selected,
            ),
            id="status_list",
            width=1,
            height=5,
        ),
        SwitchTo(Const("⬅️ Назад"), state=DeliverySG.delivery_list, id="back_button"),
        state=DeliverySG.delivery_list_choose_status,
        getter=get_order_statuses,
    ),
)
