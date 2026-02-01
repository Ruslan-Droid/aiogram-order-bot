from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import (
    Cancel, Select, ScrollingGroup, SwitchTo, Row, Button
)

from app.bot.dialogs.flows.menu_view.getters import get_restaurants_for_menu, get_categories_for_menu, \
    get_dishes_for_menu
from app.bot.dialogs.flows.menu_view.handlers import on_restaurant_selected_for_menu_view, \
    on_category_selected_for_menu_view, on_add_to_cart_clicked, go_to_cart_clicked
from app.bot.dialogs.flows.menu_view.states import MenuViewSG
from app.bot.dialogs.widgets.MultiSelectCounter import MultiSelectCounter

menu_view_dialog = Dialog(
    # Выбор заведения
    Window(
        Format("🏢 <b>Выберите заведение</b>\n\n"
               "Найдено заведений: {count}"),
        ScrollingGroup(
            Select(
                Format("🏢 {item[0]}"),
                id="restaurant_select_for_menu_view",
                item_id_getter=lambda x: x[1],
                items="restaurants",
                on_click=on_restaurant_selected_for_menu_view,
            ),
            id="restaurant_group_for_menu_view",
            width=1,
            height=6,
        ),
        Cancel(Const("⬅️ Назад")),
        getter=get_restaurants_for_menu,
        state=MenuViewSG.restaurants,
    ),
    # Выбор категории
    Window(
        Format(
            "📁 <b>Выберите категорию</b>\n"
            "Заведение: 🏢 <b>{restaurant_name}</b>\n\n"
            "Найдено категорий: {count}"),
        ScrollingGroup(
            Select(
                Format("📁 {item[0]}"),
                id="category_select_for_menu_view",
                item_id_getter=lambda x: x[1],
                items="categories",
                on_click=on_category_selected_for_menu_view,
            ),
            id="category_group_for_menu_view",
            width=1,
            height=6,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuViewSG.restaurants),

        getter=get_categories_for_menu,
        state=MenuViewSG.categories,
    ),
    # Выбор блюд
    Window(
        Format("🍽 <b>Меню</b>\n"
               "Категория: 📁 {category_name} <b></b>\n\n"
               "Найдено блюд: {count}:"),
        ScrollingGroup(
            MultiSelectCounter(
                checked_text=Format("✓ {item[0]}"),
                unchecked_text=Format("{item[0]}"),
                id="multi_counter",
                item_id_getter=lambda x: x[1],
                items="dishes",
                min_selected=0,
                max_selected=10,
                # Настройки счетчика
                counter_text=Format("{value:.0f}"),
                counter_max_value=10,
                counter_increment=1,
            ),
            id="items_group",
            height=8,
        ),
        Row(
            SwitchTo(
                Const("⬅️ Назад"),
                id="back_to_categories",
                state=MenuViewSG.categories
            ),
            Button(
                Const("🛒 Корзина"),
                id="open_cart_button",
                on_click=go_to_cart_clicked,
            ),
            Button(
                Const("✅ Добавить"),
                id="add_to_cart",
                on_click=on_add_to_cart_clicked,
            ),

        ),
        getter=get_dishes_for_menu,
        state=MenuViewSG.dishes,
    ),
)
