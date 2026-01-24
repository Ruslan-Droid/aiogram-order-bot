from aiogram.fsm.state import StatesGroup, State


class DeliverySG(StatesGroup):
    main = State()
    create_select_restaurant = State()
    create_enter_contact = State()
    create_select_bank = State()
    create_confirm = State()
    delete_list = State()
    delete_confirm = State()
    delivery_list = State()
