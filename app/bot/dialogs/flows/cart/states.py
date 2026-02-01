from aiogram.fsm.state import StatesGroup, State


class CartSG(StatesGroup):
    main = State()
    add_comment = State()
    add_to_existing_order = State()
    edit_cart = State()