from aiogram.fsm.state import StatesGroup, State


class RolesSG(StatesGroup):
    main = State()
    users_list = State()
    groups_list = State()
    change_user_select = State()
    change_user_role = State()
    change_group_select = State()
    change_group_role = State()
    ban_user = State()
