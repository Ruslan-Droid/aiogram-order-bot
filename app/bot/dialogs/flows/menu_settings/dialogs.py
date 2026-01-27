from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Back, Cancel, Select, ScrollingGroup, Column, SwitchTo
)
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput, TextInput

from .states import MenuSettingsSG
from .getters import (
    get_restaurants,
    get_categories_for_restaurant,
    get_dishes_for_category,
    get_selected_restaurant,
    get_selected_category, get_deleted_restaurants
)
from .handlers import (
    add_multiple_dishes_handler, validate_name, process_success_restaurant_name,
    process_error_name, on_restaurant_selected_delete, on_restaurant_selected_rename,
    process_success_restaurant_rename, on_restaurant_selected_for_categories, on_restaurant_selected_recover,
    process_success_category_name, process_success_category_rename, on_category_selected_delete,
    on_category_selected_rename, on_restaurant_selected_for_dishes, on_category_selected_for_dishes,
    process_success_dish_name,
)

menu_settings_dialog = Dialog(
    ## MAIN MENU✅
    # ⚙️ Главное меню настроек ✅
    Window(
        Const("⚙️ <b>Меню настроек</b>\n\nВыберите раздел для настройки:"),
        Column(
            SwitchTo(
                Const("🏢 Заведения"),
                id="restaurant_settings",
                state=MenuSettingsSG.restaurant_menu,
            ),
            SwitchTo(
                Const("📁 Категории"),
                id="category_settings",
                state=MenuSettingsSG.select_restaurant_for_category,
            ),
            SwitchTo(
                Const("🍽️ Блюда"),
                id="dish_settings",
                state=MenuSettingsSG.select_category_for_dish,
            ),
        ),
        Cancel(Const("⬅️ Назад")),
        state=MenuSettingsSG.main,
    ),
    ## 🏢 RESTAURANT BLOCK✅
    # 🏢 Меню настройки заведений ✅
    Window(
        Const("🏢 <b>Настройка заведений</b>\n\nВыберите действие:"),
        Column(
            SwitchTo(Const("➕ Добавить"),
                     id="add_restaurant_btn",
                     state=MenuSettingsSG.add_restaurant),
            SwitchTo(Const("❌ Удалить"),
                     id="delete_restaurant_btn",
                     state=MenuSettingsSG.delete_restaurant),
            SwitchTo(Const("💾 Восстановить"),
                     id="recover_restaurant_btn",
                     state=MenuSettingsSG.recover_restaurant),
            SwitchTo(Const("✏️ Переименовать"),
                     id="rename_restaurant_btn",
                     state=MenuSettingsSG.rename_restaurant),
        ),
        Back(Const("⬅️ Назад")),
        state=MenuSettingsSG.restaurant_menu,
    ),
    # 🏢 Добавление заведения ✅
    Window(
        Const("Введите название нового заведения:"),
        TextInput(
            id="restaurant_name_input",
            type_factory=validate_name,
            on_success=process_success_restaurant_name,
            on_error=process_error_name,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.restaurant_menu),
        state=MenuSettingsSG.add_restaurant,
    ),
    # 🏢 ❌ Удаление заведения ✅
    Window(
        Const("Выберите заведение которое хотите удалить:"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="restaurant_select_for_delete",
                item_id_getter=lambda x: x[1],
                items="restaurants",
                on_click=on_restaurant_selected_delete,
            ),
            id="restaurant_group_for_deleting",
            width=1,
            height=6,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.restaurant_menu),
        getter=get_restaurants,
        state=MenuSettingsSG.delete_restaurant,
    ),
    # 🏢 💾 Восстановить заведение ✅
    Window(
        Const("Выберите удаленное заведение которое хотите восстановить:"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="restaurant_select_for_recover",
                item_id_getter=lambda x: x[1],
                items="restaurants",
                on_click=on_restaurant_selected_recover,
            ),
            id="restaurant_group_for_recover",
            width=1,
            height=6,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.restaurant_menu),
        getter=get_deleted_restaurants,
        state=MenuSettingsSG.recover_restaurant,
    ),
    # 🏢 ️✏️ Переименование заведения ✅
    Window(
        Const("Выберите заведение которое хотите переименование:"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="restaurant_select_for_rename",
                item_id_getter=lambda x: x[1],
                items="restaurants",
                on_click=on_restaurant_selected_rename,
            ),
            id="restaurant_group_for_renaming",
            width=1,
            height=6,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.restaurant_menu),
        getter=get_restaurants,
        state=MenuSettingsSG.rename_restaurant,
    ),
    Window(
        Const("Напишите название для заведения:"),
        TextInput(
            id="restaurant_rename_input",
            type_factory=validate_name,
            on_success=process_success_restaurant_rename,
            on_error=process_error_name,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.rename_restaurant),
        state=MenuSettingsSG.rename_restaurant_input,
    ),
    ## CATEGORY BLOCK✅
    # Выбор заведения для работы с категориями ✅
    Window(
        Format("🏢 <b>Выберите заведение для работы с категориями</b>\n\nНайдено заведений: {count}"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="restaurant_select_for_category",
                item_id_getter=lambda x: x[1],
                items="restaurants",
                on_click=on_restaurant_selected_for_categories,
            ),
            id="restaurant_group_for_category",
            width=1,
            height=6,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.main),
        getter=get_restaurants,
        state=MenuSettingsSG.select_restaurant_for_category,
    ),
    # Меню настройки категорий для выбранного заведения ✅
    Window(
        Format("📁 <b>Настройка категорий</b>\n\n"
               "Заведение:🏢 <b>{restaurant_name}</b>\n\n"
               "Выберите действие:"),
        Column(
            SwitchTo(Const("➕ Добавить"),
                     id="add_category_btn",
                     state=MenuSettingsSG.add_category),
            SwitchTo(Const("🗑️ Удалить"),
                     id="delete_category_btn",
                     state=MenuSettingsSG.delete_category),
            SwitchTo(Const("✏️ Переименовать"),
                     id="rename_category_btn",
                     state=MenuSettingsSG.rename_category),
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.select_restaurant_for_category),
        getter=get_selected_restaurant,
        state=MenuSettingsSG.categories_menu,
    ),
    # Добавление категории ✅
    Window(
        Const("Введите название новой категории:"),
        TextInput(
            id="category_name_input",
            type_factory=validate_name,
            on_success=process_success_category_name,
            on_error=process_error_name,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.categories_menu),
        state=MenuSettingsSG.add_category,
    ),
    # Удаление категории ✅
    Window(
        Const("Выберите категорию которою хотите удалить:"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="category_select_for_delete",
                item_id_getter=lambda x: x[1],
                items="categories",
                on_click=on_category_selected_delete,
            ),
            id="category_group_for_deleting",
            width=1,
            height=6,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.categories_menu),
        getter=get_categories_for_restaurant,
        state=MenuSettingsSG.delete_category,
    ),
    # Переименование категории ✅
    Window(
        Const("Выберите категорию которую хотите переименовать:"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="category_select_for_rename",
                item_id_getter=lambda x: x[1],
                items="categories",
                on_click=on_category_selected_rename,
            ),
            id="category_group_for_renaming",
            width=1,
            height=6,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.categories_menu),
        getter=get_categories_for_restaurant,
        state=MenuSettingsSG.rename_category,
    ),
    Window(
        Const("Напишите название для категории:"),
        TextInput(
            id="category_rename_input",
            type_factory=validate_name,
            on_success=process_success_category_rename,
            on_error=process_error_name,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.rename_category),
        state=MenuSettingsSG.rename_category_input,
    ),
    ## DISH BLOCK
    # Выбор заведения для работы с блюдами ✅
    Window(
        Format("🏢 <b>Выберите заведение для работы с блюдами</b>\n\n"
               "Найдено заведений: {count}"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="restaurant_select_for_dish",
                item_id_getter=lambda x: x[1],
                items="restaurants",
                on_click=on_restaurant_selected_for_dishes,
            ),
            id="restaurant_group_for_dish",
            width=1,
            height=6,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.main),
        getter=get_restaurants,
        state=MenuSettingsSG.select_restaurant_for_dish,
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
                on_click=on_category_selected_for_dishes,
            ),
            id="category_group_for_dish",
            width=1,
            height=6,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.select_restaurant_for_dish),
        getter=get_categories_for_restaurant,
        state=MenuSettingsSG.select_category_for_dish,
    ),
    # Меню настройки блюд для выбранной категории
    Window(
        Format("🍽️ <b>Настройка блюд</b>\n\n"
               "Категория: <b>{category_name}</b>\n\n"
               "Выберите действие:"),
        Column(SwitchTo(Const("➕ Добавить"),
                        id="add_dish_btn",
                        state=MenuSettingsSG.add_dish),
               SwitchTo(Const("🗑️ Удалить"),
                        id="delete_dish_btn",
                        state=MenuSettingsSG.delete_dish),
               SwitchTo(Const("✏️ Переименовать"),
                        id="rename_dish_btn",
                        state=MenuSettingsSG.rename_dish),
               SwitchTo(Const("💰 Изменить цену"),
                        id="rename_dish_btn",
                        state=MenuSettingsSG.change_dish_price),
               SwitchTo(Const("📋 Добавить списком"),
                        id="rename_dish_btn",
                        state=MenuSettingsSG.add_multiple_dishes),
               ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.select_category_for_dish),
        getter=get_selected_category,
        state=MenuSettingsSG.dishes_menu,
    ),
    # Добавление блюдо
    Window(
        Const("Введите название нового блюда:"),
        TextInput(
            id="dish_name_input",
            type_factory=validate_name,
            on_success=process_success_dish_name,
            on_error=process_error_name,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.dishes_menu),
        state=MenuSettingsSG.add_dish,
    ),
    # Удаление блюда
    Window(
        Const("Выберите блюдо которое хотите удалить:"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="dish_select_for_delete",
                item_id_getter=lambda x: x[1],
                items="dishes",
                on_click=,
            ),
            id="dish_group_for_deleting",
            width=1,
            height=6,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.dishes_menu),
        getter=get_dishes_for_category,
        state=MenuSettingsSG.delete_dish,
    ),
    # Переименование блюда
    Window(
        Const("Выберите блюдо которое хотите переименовать:"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="dish_select_for_rename",
                item_id_getter=lambda x: x[1],
                items="categories",
                on_click=on_category_selected_rename,
            ),
            id="dish_group_for_renaming",
            width=1,
            height=6,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.dishes_menu),
        getter=,
        state=MenuSettingsSG.rename_dish,
    ),
    Window(
        Const("Напишите название для блюда:"),
        TextInput(
            id="dish_rename_input",
            type_factory=validate_name,
            on_success=,
            on_error=process_error_name,
        ),
        SwitchTo(Const("⬅️ Назад"),
                 id="back_btn",
                 state=MenuSettingsSG.rename_dish),
        state=MenuSettingsSG.rename_dish_input,
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
