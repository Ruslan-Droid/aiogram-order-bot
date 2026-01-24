from aiogram.fsm.state import StatesGroup, State


class MenuViewSG(StatesGroup):
    select_restaurant = State()
    select_category = State()
    view_dishes = State()
    dish_detail = State()
