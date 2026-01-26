from aiogram.fsm.state import State, StatesGroup


class MenuSettingsSG(StatesGroup):
    # Главное меню настроек
    main = State()

    # Настройка заведений
    restaurant_menu = State()
    add_restaurant = State()
    delete_restaurant = State()
    rename_restaurant = State()

    # Настройка категорий
    categories_menu = State()
    select_restaurant_for_category = State()
    add_category = State()
    delete_category = State()
    rename_category = State()

    # Настройка блюд
    dishes_menu = State()
    select_category_for_dish = State()
    add_dish = State()
    delete_dish = State()
    rename_dish = State()
    change_dish_price = State()
    add_multiple_dishes = State()