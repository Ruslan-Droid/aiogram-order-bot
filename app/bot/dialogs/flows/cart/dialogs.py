from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import (
    Back, Select, ScrollingGroup, Cancel, SwitchTo, Button
)
from aiogram_dialog.widgets.input import MessageInput

from app.bot.dialogs.flows.cart.states import CartSG
from app.bot.dialogs.flows.cart.getters import get_cart_data, get_comment_data, get_active_orders_for_adding_cart
from app.bot.dialogs.flows.cart.handlers import (
    on_order_selected, on_comment_entered, on_edit_cart_clicked
)

cart_dialog = Dialog(
    # Основное окно корзины
    Window(
        Format(
            "🛒 <b>Ваша корзина</b>\n"
            "Заведение:🏢 {restaurant_name}\n"
            "Статус: {cart_status}\n\n"
            "<b>Товары:</b>\n"
            "{cart_items}\n"
            "💰 <b>Итого: {total_price:.2f} ₽</b>\n"
            "Комментарий: {note}"
        ),
        SwitchTo(
            Const("🚚 Включить в доставку"),
            id="add_to_active_order",
            state=CartSG.add_to_existing_order,
            when="is_attachable",  # Только для активной непустой корзины
        ),
        SwitchTo(
            Const("✏️ Отредактировать корзину"),
            id="go_to_edit_cart_button",
            state=CartSG.edit_cart,
            when="is_attachable",  # Только для активной непустой корзины
        ),
        SwitchTo(
            Const("📝 Добавить комментарий к заказу"),
            id="add_comment",
            state=CartSG.add_comment,
            when="is_attachable"  # Только для активной непустой корзины
        ),
        Cancel(Const("⬅️ Назад")),
        getter=get_cart_data,
        state=CartSG.main,
    ),
    # 📝 Окно добавления комментария
    Window(
        Const("✍️ <b>Введите комментарий к заказу:</b>\n\n"
              "Текущий комментарий: {current_comment}"),
        MessageInput(
            func=on_comment_entered,
            content_types=["text"]
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="go_to_main_window_button",
                 state=CartSG.main, ),
        getter=get_comment_data,
        state=CartSG.add_comment,
    ),
    # 🚚 Окно выбора заказа для привязки
    Window(
        Format(
            "🚚 <b>Выберите активный заказ</b>\n\n"
            "Найдено активных заказов: {orders_count}"
        ),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="order_select",
                item_id_getter=lambda x: x[1],
                items="orders",
                on_click=on_order_selected,
            ),
            id="order_group",
            width=1,
            height=6,
        ),
        Back(Const("⬅️ Назад")),
        getter=get_active_orders_for_adding_cart,
        state=CartSG.add_to_existing_order,
    ),
    Window(
        Const("🔄 <b>Редактирование корзины</b>\n\n"
              "Вы будете перенаправлены в меню для изменения состава корзины."),
        Button(
            Const("✏️ Перейти в меню"),
            id="go_to_menu",
            on_click=on_edit_cart_clicked,
        ),
        Back(Const("⬅️ Назад")),
        state=CartSG.edit_cart,
    ),
)
