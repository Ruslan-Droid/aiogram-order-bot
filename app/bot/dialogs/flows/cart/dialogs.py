from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import (
    Back, Select, ScrollingGroup, Cancel, SwitchTo, Button
)
from aiogram_dialog.widgets.input import MessageInput

from app.bot.dialogs.flows.cart.states import CartSG
from app.bot.dialogs.flows.cart.getters import get_cart_data, get_comment_data, get_active_orders_for_adding_cart, \
    get_cart_items_for_edit, get_cart_item_for_edit, get_cart_history, get_active_orders_for_delivery, \
    get_carts_for_order
from app.bot.dialogs.flows.cart.handlers import (
    on_order_selected, on_comment_entered, on_cart_item_selected, on_update_amount, on_order_for_delivery_selected
)
from app.bot.dialogs.flows.menu_view.states import MenuViewSG
from app.bot.dialogs.utils.roles_utils import role_required
from app.infrastructure.database.enums import UserRole

cart_dialog = Dialog(
    # MAIN MENU
    ############################
    Window(
        Format(
            "🛒 <b>Ваша текущая корзина</b>\n"
            "Заведение:🏢 {restaurant_name}\n"
            "Статус: {cart_status}\n\n"
            "<b>Товары:</b>\n"
            "{cart_items}\n"
            "💰 <b>Итого: {total_price:.2f} ₽</b>\n"
            "Комментарий: {note}"
        ),
        SwitchTo(
            Const("📝 Добавить комментарий к заказу"),
            id="add_comment",
            state=CartSG.add_comment,
            when="is_attachable"  # Только для активной непустой корзины
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
        # только для выездников и админов
        SwitchTo(
            Const("💎 Посмотреть все корзины для доставки"),
            id="go_to_show_all_cart_for_order_button",
            state=CartSG.show_all_carts,
            when=role_required(
                [UserRole.DELIVERY, UserRole.ADMIN, UserRole.SUPER_ADMIN]
            ),
        ),
        SwitchTo(
            Const("📊 История заказов"),
            id="go_to_all_cart_button",
            state=CartSG.show_cart_history,
        ),
        Cancel(Const("⬅️ Назад")),
        getter=get_cart_data,
        state=CartSG.main,
    ),
    ############################
    # 📝 Окно добавления комментария
    Window(
        Format("✍️ <b>Введите комментарий к заказу:</b>\n\n"
               "Текущий комментарий:\n"
               "{current_comment}"),
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
    ############################
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
        SwitchTo(
            Const("⬅️ Назад"),
            id="go_to_main_menu_button",
            state=CartSG.main,
        ),
        getter=get_active_orders_for_adding_cart,
        state=CartSG.add_to_existing_order,
    ),
    ############################
    # ✏️ Окно редактирования корзины
    Window(
        Format(
            "🔄 <b>Редактирование корзины</b>\n"
            "🏢 {restaurant_name}\n"
            "💰 Итого: {total_price:.2f} ₽\n\n"
            "{cart_status}"
        ),
        ScrollingGroup(
            Select(
                Format("🍽 {item[0]}"),
                id="cart_item_select",
                item_id_getter=lambda x: x[1],
                items="cart_items_list",
                on_click=on_cart_item_selected,
                when="not cart_empty"
            ),
            id="cart_items_group",
            width=1,
            height=8,
        ),
        SwitchTo(
            Const("➕ Добавить ещё блюда"),
            id="add_more_dishes",
            state=MenuViewSG.restaurants,
            when="not cart_empty"
        ),
        SwitchTo(
            Const("⬅️ Назад"),
            id="back_to_main",
            state=CartSG.main,
        ),
        getter=get_cart_items_for_edit,
        state=CartSG.edit_cart,
    ),
    # 🔢 Окно редактирования количества блюда
    Window(
        Format(
            "🔢 <b>Изменение количества</b>\n\n"
            "Блюдо: <b>{dish_name}</b>\n"
            "Текущее количество: {current_amount}\n"
            "Цена за шт.: {price:.2f} ₽\n"
            "Итого: {total:.2f} ₽\n\n"
            "Введите новое количество (0 для удаления):"
        ),
        MessageInput(
            func=on_update_amount,
            content_types=["text"]
        ),
        Back(Const("⬅️ Назад")),
        getter=get_cart_item_for_edit,
        state=CartSG.edit_cart_item,
    ),

    # 📊 Окно истории заказов (НОВОЕ)
    Window(
        Format(
            "📊 <b>История ваших заказов</b>\n\n"
            "Всего заказов: {total_orders}\n"
            "Общая сумма: {total_spent:.2f} ₽\n\n"
            "Найдено корзин: {carts_count}"
        ),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="history_cart_select",
                item_id_getter=lambda x: x[1],
                items="carts",
            ),
            id="history_group",
            width=1,
            height=8,
        ),
        SwitchTo(
            Const("⬅️ Назад"),
            id="back_to_main_from_history",
            state=CartSG.main,
        ),
        getter=get_cart_history,
        state=CartSG.show_cart_history,
    ),

    # 💎 Окно выбора заказа для просмотра корзин (для доставки)
    Window(
        Format(
            "💎 <b>Активные заявки на доставку</b>\n"
            "Дата: {today_date}\n\n"
            "Найдено заявок: {orders_count}"
        ),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="delivery_order_select",
                item_id_getter=lambda x: x[1],
                items="orders",
                on_click=on_order_for_delivery_selected,
            ),
            id="delivery_orders_group",
            width=1,
            height=6,
        ),
        SwitchTo(
            Const("⬅️ Назад"),
            id="back_to_main_from_delivery",
            state=CartSG.main,
        ),
        getter=get_active_orders_for_delivery,
        state=CartSG.show_all_carts,
    ),

    # 📦 Окно просмотра корзин в заказе
    Window(
        Format(
            "📦 <b>Корзины в заказе</b>\n"
            "{order_info}\n"
            "Статус: {order_status}\n"
            "Общая сумма: {order_total:.2f} ₽\n\n"
            "Корзин в заказе: {carts_count}"
        ),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="order_cart_select",
                item_id_getter=lambda x: x[1],
                items="carts",
            ),
            id="order_carts_group",
            width=1,
            height=8,
        ),
        SwitchTo(
            Const("⬅️ Назад к заявкам"),
            id="back_to_delivery_orders",
            state=CartSG.show_all_carts,
        ),
        getter=get_carts_for_order,
        state=CartSG.show_carts_for_order,
    ),
)
