from aiogram.fsm.state import StatesGroup, State


class MenuSettingsSG(StatesGroup):
    main = State()
    restaurant_select_action = State()
    restaurant_add = State()
    restaurant_delete = State()
    restaurant_rename = State()
    category_select_restaurant = State()
    category_select_action = State()
    category_add = State()
    category_delete = State()
    category_rename = State()
    dish_select_category = State()
    dish_select_action = State()
    dish_add = State()
    dish_delete = State()
    dish_rename = State()
    dish_change_price = State()
    dish_bulk_add = State()
