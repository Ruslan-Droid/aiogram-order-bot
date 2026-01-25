from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Multiselect, Button, Row, Cancel, Back,
    Radio, Group, ScrollingGroup
)
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput

from .states import AdminPanelSG
from .getters import get_pending_users, get_user_info, get_available_roles
from .handlers import (
    ban_selected_users, approve_selected_users,
    start_change_role, process_user_id, select_role,
    save_role_changes, validate_telegram_id, process_error_user_id
)

admin_roles_dialog = Dialog(
    Window(
        Format("👥 Пользователи ожидающие авторизации\n\n"
               "Найдено пользователей: {count_users}\n"
               "Выберите пользователей:"),
        ScrollingGroup(
            Multiselect(
                checked_text=Format("✓ {item.username}"),
                unchecked_text=Format("{item.username}"),
                id="ms_users",
                item_id_getter=lambda x: str(x.telegram_id),
                items="users",
            ),
            id="sg_users",
            width=1,
            height=10,
        ),
        Row(
            Button(
                Const("🚫 Забанить"),
                id="btn_ban",
                on_click=ban_selected_users,
                when=lambda data, widget, manager: data.get("count_users") != 0,
            ),
            Button(
                Const("✅ Авторизовать"),
                id="btn_approve",
                on_click=approve_selected_users,
                when=lambda data, widget, manager: data.get("count_users") != 0,
            ),
        ),
        Button(
            Const("🆔 Изменить права по ID"),
            id="btn_change_role",
            on_click=start_change_role,
        ),
        Cancel(Const("⬅️ Назад")),
        state=AdminPanelSG.pending_users,
        getter=get_pending_users
    ),

    Window(
        Const("Введите ID пользователя, чьи права вы хотите изменить:"),
        TextInput(
            id="input_user_id",
            type_factory=validate_telegram_id,
            on_success=process_user_id,
            on_error=process_error_user_id,
        ),
        Back(Const("⬅️ Назад")),
        state=AdminPanelSG.change_role_input,
    ),
    Window(
        Format("Пользователь: {user.full_name}\n"
               "Текущая роль: {user.role.value}\n\n"
               "Выберите новую роль:"),
        Group(
            Radio(
                checked_text=Format("🔘{item.value}"),
                unchecked_text=Format("⚪️ {item.value}"),
                id="rd_role",
                item_id_getter=lambda x: x.value,
                items="roles",
                on_click=select_role,
            ),
            id="gr_roles",
            width=1,
        ),
        Row(
            Back(Const("⬅️ Назад")),
            Button(
                Const("💾 Сохранить"),
                id="btn_save_role",
                on_click=save_role_changes,
            ),

        ),
        state=AdminPanelSG.change_role_select,
        getter=[get_user_info, get_available_roles],
    ),
)
