from aiogram.fsm.state import State, StatesGroup


class MenuSettingsSG(StatesGroup):
    # Главное меню настроек
    main = State()

    # Настройка заведений
    restaurant_menu = State()
    add_restaurant = State()
    delete_restaurant = State()
    recover_restaurant = State()
    rename_restaurant = State()
    rename_restaurant_input = State()

    # Настройка категорий
    categories_menu = State()
    select_restaurant_for_category = State()
    add_category = State()
    delete_category = State()
    rename_category = State()
    rename_category_input = State()

    # Настройка блюд
    select_restaurant_for_dish = State()
    select_category_for_dish = State()
    dishes_menu = State()
    add_dish = State()
    delete_dish = State()
    rename_dish = State()
    rename_dish_input = State()
    change_dish_price = State()
    add_multiple_dishes = State()