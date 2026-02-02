from aiogram.fsm.state import StatesGroup, State


class MenuViewSG(StatesGroup):
    restaurants = State()
    categories = State()
    dishes = State()

