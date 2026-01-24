from aiogram.fsm.state import StatesGroup, State


class CartSG(StatesGroup):
    view = State()
    details = State()
