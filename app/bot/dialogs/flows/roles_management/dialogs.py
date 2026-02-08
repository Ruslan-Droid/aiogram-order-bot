from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Multiselect, Button, Row, Cancel, Back,
    Radio, Group, ScrollingGroup, SwitchTo, Select
)
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput

from .states import AdminPanelSG
from .getters import get_pending_users, get_user_info, get_available_roles, get_users_for_role_change
from .handlers import (
    ban_selected_users, approve_selected_users,
    start_change_role, process_user_id, select_role,
    save_role_changes, validate_telegram_id, process_error_user_id, on_user_selected
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
        SwitchTo(
            Const("👥 Выбрать пользователя из списка"),
            id="btn_choose_member",
            state=AdminPanelSG.choose_member_list,
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
            SwitchTo(
                Const("⬅️ Назад"),
                id="btn_back_member",
                state=AdminPanelSG.pending_users
            ),
            Button(
                Const("💾 Сохранить"),
                id="btn_save_role",
                on_click=save_role_changes,
            ),

        ),
        state=AdminPanelSG.change_role_select,
        getter=[get_user_info, get_available_roles],
    ),
    Window(
        Const("👥 Выберите пользователя:"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="sg_users",
                item_id_getter=lambda x: x[1],
                items="users",
                on_click=on_user_selected,
            ),
            id="sg_users_group",
            width=1,
            height=10,
        ),
        SwitchTo(
            Const("⬅️ Назад"),
            id="btn_back_choose_member",
            state=AdminPanelSG.pending_users
        ),
        state=AdminPanelSG.choose_member_list,
        getter=get_users_for_role_change,
    ),
)
