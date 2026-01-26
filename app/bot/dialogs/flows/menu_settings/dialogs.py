from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Button, Row, Back, Cancel, Select, Group, ScrollingGroup, Column
)
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput

from .states import MenuSettingsSG
from .getters import (
    get_restaurants,
    get_categories_for_restaurant,
    get_dishes_for_category,
    get_selected_restaurant,
    get_selected_category
)
from .handlers import (
    on_restaurant_selected,
    on_category_selected,
    add_restaurant_handler,
    delete_restaurant_handler,
    rename_restaurant_handler,
    add_category_handler,
    delete_category_handler,
    rename_category_handler,
    add_dish_handler,
    delete_dish_handler,
    rename_dish_handler,
    change_dish_price_handler,
    add_multiple_dishes_handler,
    go_to_restaurant_settings,
    go_to_category_settings,
    go_to_dish_settings,
    go_back
)

menu_settings_dialog = Dialog(
    # Главное меню настроек
    Window(
        Const("⚙️ <b>Меню настроек</b>\n\nВыберите раздел для настройки:"),
        Column(
            Button(Const("🏢 Заведения"), id="restaurant_settings", on_click=go_to_restaurant_settings),
            Button(Const("📁 Категории"), id="category_settings", on_click=go_to_category_settings),
            Button(Const("🍽️ Блюда"), id="dish_settings", on_click=go_to_dish_settings),
        ),
        Cancel(Const("❌ Назад")),
        state=MenuSettingsSG.main,
    ),

    # Меню настройки заведений
    Window(
        Const("🏢 <b>Настройка заведений</b>\n\nВыберите действие:"),
        Column(
            Button(Const("➕ Добавить"), id="add_restaurant_btn",
                   on_click=lambda c, b, m: m.switch_to(MenuSettingsSG.add_restaurant)),
            Button(Const("🗑️ Удалить"), id="delete_restaurant_btn",
                   on_click=lambda c, b, m: m.switch_to(MenuSettingsSG.delete_restaurant)),
            Button(Const("✏️ Переименовать"), id="rename_restaurant_btn",
                   on_click=lambda c, b, m: m.switch_to(MenuSettingsSG.rename_restaurant)),
        ),
        Back(Const("⬅️ Назад")),
        state=MenuSettingsSG.restaurant_menu,
    ),

    # Добавление заведения
    Window(
        Const("Введите название нового заведения:"),
        MessageInput(add_restaurant_handler),
        Back(Const("⬅️ Назад")),
        state=MenuSettingsSG.add_restaurant,
    ),

    # Удаление заведения
    Window(
        Const("Введите ID заведения для удаления:"),
        MessageInput(delete_restaurant_handler),
        Back(Const("⬅️ Назад")),
        state=MenuSettingsSG.delete_restaurant,
    ),

    # Переименование заведения
    Window(
        Const("Введите данные в формате:\n<code>ID|новое_название</code>\n\nПример: <code>1|Название ресторана</code>"),
        MessageInput(rename_restaurant_handler),
        Back(Const("⬅️ Назад")),
        state=MenuSettingsSG.rename_restaurant,
    ),

    # Выбор заведения для работы с категориями
    Window(
        Format("🏢 <b>Выберите заведение для работы с категориями</b>\n\nНайдено заведений: {count}"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="restaurant_select_for_category",
                item_id_getter=lambda x: x[1],
                items="restaurants",
                on_click=on_restaurant_selected,
            ),
            id="restaurant_group_for_category",
            width=1,
            height=6,
        ),
        Back(Const("⬅️ Назад")),
        getter=get_restaurants,
        state=MenuSettingsSG.select_restaurant_for_category,
    ),

    # Меню настройки категорий для выбранного заведения
    Window(
        Format("📁 <b>Настройка категорий</b>\n\nЗаведение: <b>{restaurant_name}</b>\n\nВыберите действие:"),
        Row(
            Button(Const("➕ Добавить"), id="add_category_btn",
                   on_click=lambda c, b, m: m.switch_to(MenuSettingsSG.add_category)),
            Button(Const("🗑️ Удалить"), id="delete_category_btn",
                   on_click=lambda c, b, m: m.switch_to(MenuSettingsSG.delete_category)),
            Button(Const("✏️ Переименовать"), id="rename_category_btn",
                   on_click=lambda c, b, m: m.switch_to(MenuSettingsSG.rename_category)),
        ),
        Back(Const("⬅️ Назад")),
        getter=get_selected_restaurant,
        state=MenuSettingsSG.categories_menu,
    ),

    # Добавление категории
    Window(
        Const("Введите название новой категории:"),
        MessageInput(add_category_handler),
        Back(Const("⬅️ Назад")),
        state=MenuSettingsSG.add_category,
    ),

    # Удаление категории
    Window(
        Const("Введите ID категории для удаления:"),
        MessageInput(delete_category_handler),
        Back(Const("⬅️ Назад")),
        state=MenuSettingsSG.delete_category,
    ),

    # Переименование категории
    Window(
        Const("Введите данные в формате:\n<code>ID|новое_название</code>\n\nПример: <code>1|Новая категория</code>"),
        MessageInput(rename_category_handler),
        Back(Const("⬅️ Назад")),
        state=MenuSettingsSG.rename_category,
    ),

    # Выбор категории для работы с блюдами
    Window(
        Format(
            "📁 <b>Выберите категорию для работы с блюдами</b>\n\nЗаведение: <b>{restaurant_name}</b>\n\nНайдено категорий: {count}"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="category_select_for_dish",
                item_id_getter=lambda x: x[1],
                items="categories",
                on_click=on_category_selected,
            ),
            id="category_group_for_dish",
            width=1,
            height=6,
        ),
        Back(Const("⬅️ Назад")),
        getter=get_categories_for_restaurant,
        state=MenuSettingsSG.select_category_for_dish,
    ),

    # Меню настройки блюд для выбранной категории
    Window(
        Format("🍽️ <b>Настройка блюд</b>\n\nКатегория: <b>{category_name}</b>\n\nВыберите действие:"),
        Group(
            Row(
                Button(Const("➕ Добавить"), id="add_dish_btn",
                       on_click=lambda c, b, m: m.switch_to(MenuSettingsSG.add_dish)),
                Button(Const("🗑️ Удалить"), id="delete_dish_btn",
                       on_click=lambda c, b, m: m.switch_to(MenuSettingsSG.delete_dish)),
            ),
            Row(
                Button(Const("✏️ Переименовать"), id="rename_dish_btn",
                       on_click=lambda c, b, m: m.switch_to(MenuSettingsSG.rename_dish)),
                Button(Const("💰 Изменить цену"), id="change_price_btn",
                       on_click=lambda c, b, m: m.switch_to(MenuSettingsSG.change_dish_price)),
            ),
            Button(Const("📋 Добавить списком"), id="add_multiple_dishes_btn",
                   on_click=lambda c, b, m: m.switch_to(MenuSettingsSG.add_multiple_dishes)),
            width=2,
        ),
        Back(Const("⬅️ Назад")),
        getter=get_selected_category,
        state=MenuSettingsSG.dishes_menu,
    ),

    # Добавление блюда
    Window(
        Const("Введите данные в формате:\n<code>название|цена</code>\n\nПример: <code>Пицца Маргарита|12.50</code>"),
        MessageInput(add_dish_handler),
        Back(Const("⬅️ Назад")),
        state=MenuSettingsSG.add_dish,
    ),

    # Удаление блюда
    Window(
        Const("Введите ID блюда для удаления:"),
        MessageInput(delete_dish_handler),
        Back(Const("⬅️ Назад")),
        state=MenuSettingsSG.delete_dish,
    ),

    # Переименование блюда
    Window(
        Const(
            "Введите данные в формате:\n<code>ID|новое_название</code>\n\nПример: <code>1|Новое название блюда</code>"),
        MessageInput(rename_dish_handler),
        Back(Const("⬅️ Назад")),
        state=MenuSettingsSG.rename_dish,
    ),

    # Изменение цены блюда
    Window(
        Const("Введите данные в формате:\n<code>ID|новая_цена</code>\n\nПример: <code>1|15.99</code>"),
        MessageInput(change_dish_price_handler),
        Back(Const("⬅️ Назад")),
        state=MenuSettingsSG.change_dish_price,
    ),

    # Добавление нескольких блюд
    Window(
        Const(
            "Введите список блюд (каждое с новой строки):\n\nФормат для каждого блюда:\n<code>название|цена</code>\n\nПример:\n<code>Пицца Маргарита|12.50\nСалат Цезарь|8.99\nСуп Грибной|5.50</code>"),
        MessageInput(add_multiple_dishes_handler),
        Back(Const("⬅️ Назад")),
        state=MenuSettingsSG.add_multiple_dishes,
    ),
)
