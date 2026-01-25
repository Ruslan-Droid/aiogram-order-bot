from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Multiselect, Button, Row, Cancel, Back,
    Radio, Group, ScrollingGroup
)
from aiogram_dialog.widgets.text import Const, Format, Multi
from aiogram_dialog.widgets.input import TextInput

from .states import AdminPanelSG
from .getters import get_pending_users, get_user_info, get_available_roles, get_selected_users
from .handlers import (
    on_user_selected, ban_selected_users, approve_selected_users,
    start_change_role, process_user_id, select_role,
    save_role_changes, cancel_role_change
)

admin_roles_dialog = Dialog(
    Window(
        Format("👥 Пользователи ожидающие авторизации\n\n"
               "Найдено пользователей: {count}\n"
               "Выберите пользователей:"),
        ScrollingGroup(
            Multiselect(
                checked_text=Format("✓ {item.username}"),
                unchecked_text=Format("{item.username}"),
                id="ms_users",
                item_id_getter=lambda x: str(x.telegram_id),
                items="users",
                on_click=on_user_selected,
            ),
            id="sg_users",
            width=1,
            height=10,
        ),
        Format("Выбрано: {has_selected} пользователей"),
        Row(
            Button(
                Const("🚫 Забанить"),
                id="btn_ban",
                on_click=ban_selected_users,
                when=lambda data, widget, manager: data.get("count") != 0,
            ),
            Button(
                Const("✅ Авторизовать"),
                id="btn_approve",
                on_click=approve_selected_users,
                when=lambda data, widget, manager: data.get("count") != 0,
            ),
        ),
        Button(
            Const("🆔 Изменить права по ID"),
            id="btn_change_role",
            on_click=start_change_role,
        ),
        Cancel(Const("⬅️ Назад")),
        state=AdminPanelSG.pending_users,
        getter=[get_pending_users, get_selected_users],
    ),

    #
    Window(
        Const("Введите ID пользователя, чьи права вы хотите изменить:"),
        TextInput(
            id="input_user_id",
            on_success=process_user_id,
        ),
        Back(Const("⬅️ Назад")),
        state=AdminPanelSG.change_role_input,
    ),
    Window(
        Multi(
            Format("Пользователь: {user.full_name if user else 'Не найден'}"),
            Format("Текущая роль: {user.role.value if user else 'N/A'}"),
            Const(""),
            Const("Выберите новую роль:"),
            sep="\n"
        ),

        Group(
            Radio(
                Format("◉ {item.value}"),
                Format("◎ {item.value}"),
                id="rd_role",
                item_id_getter=lambda x: x.value,
                items="roles",
                on_click=select_role,
            ),
            id="gr_roles",
            width=2,
        ),

        Row(
            Button(
                Const("💾 Сохранить"),
                id="btn_save_role",
                on_click=save_role_changes,
            ),
            Button(
                Const("❌ Отменить"),
                id="btn_cancel_role",
                on_click=cancel_role_change,
            ),
        ),

        Back(Const("⬅️ Назад")),

        state=AdminPanelSG.change_role_select,
        getter=[get_user_info, get_available_roles],
    ),
)
