from aiogram.filters.state import State, StatesGroup

class AdminPanelSG(StatesGroup):
    pending_users = State()  # Список пользователей на авторизацию
    change_role_input = State()  # Ввод ID для смены роли
    change_role_select = State()  # Выбор новой роли
    choose_member_list = State()