from typing import Any
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, StartMode, Window, Dialog
from aiogram_dialog.widgets.kbd import Button, Multiselect, Cancel, Back
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.enums.user_roles import UserRole
from .states import AdminPanelSG
from .getters import get_pending_users, get_user_info, get_available_roles, get_selected_users

router = Router()


async def on_user_selected(callback: CallbackQuery, widget: Any,
                           dialog_manager: DialogManager, item_id: str):
    selected_ids = dialog_manager.dialog_data.get("selected_user_ids", [])

    if item_id in selected_ids:
        selected_ids.remove(item_id)
    else:
        selected_ids.append(int(item_id))


async def ban_selected_users(callback: CallbackQuery, button: Button,
                             dialog_manager: DialogManager):
    """Бан выбранных пользователей"""
    selected_ids = dialog_manager.dialog_data.get("selected_user_ids", [])
    session: AsyncSession = dialog_manager.middleware_data["session"]

    if selected_ids:
        stmt = update(UserModel).where(
            UserModel.id.in_(selected_ids)
        ).values(
            role=UserRole.BANNED,
            is_active=False
        )
        await session.execute(stmt)
        await session.commit()

    # Очищаем выбранные ID
    dialog_manager.dialog_data["selected_user_ids"] = []
    await callback.answer("Пользователи забанены")
    await dialog_manager.switch_to(AdminPanelSG.pending_users)


async def approve_selected_users(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
) -> None:
    selected_ids = dialog_manager.dialog_data.get("selected_user_ids", [])
    session: AsyncSession = dialog_manager.middleware_data["session"]

    if selected_ids:
        stmt = update(UserModel).where(
            UserModel.id.in_(selected_ids)
        ).values(
            role=UserRole.MEMBER,
            is_active=True
        )
        await session.execute(stmt)
        await session.commit()

    # Очищаем выбранные ID
    dialog_manager.dialog_data["selected_user_ids"] = []
    await callback.answer("Пользователи одобрены")
    await dialog_manager.switch_to(AdminPanelSG.pending_users)


async def start_change_role(callback: CallbackQuery, button: Button,
                            dialog_manager: DialogManager):
    await dialog_manager.switch_to(AdminPanelSG.change_role_input)


async def process_user_id(message: Message,
                          widget: Any,
                          dialog_manager: DialogManager,
                          text: str
                          ) -> None:
    """Обработка введенного ID пользователя"""
    if not text.isdigit():
        await message.answer("ID должен быть числом. Попробуйте снова:")
        return

    user_id = int(text)
    dialog_manager.dialog_data["user_id_to_change"] = user_id

    # Проверяем существование пользователя
    async with dialog_manager.middleware_data["session"] as session:
        query = select(UserModel).where(UserModel.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("Пользователь с таким ID не найден. Попробуйте снова:")
            return

    await dialog_manager.switch_to(AdminPanelSG.change_role_select)


async def select_role(callback: CallbackQuery, button: Button,
                      dialog_manager: DialogManager, item_id: str):
    """Выбор роли для пользователя"""
    dialog_manager.dialog_data["selected_role"] = item_id


async def save_role_changes(callback: CallbackQuery, button: Button,
                            dialog_manager: DialogManager):
    """Сохранение изменений роли"""
    user_id = dialog_manager.dialog_data.get("user_id_to_change")
    selected_role = dialog_manager.dialog_data.get("selected_role")

    if not user_id or not selected_role:
        await callback.answer("Ошибка: данные не заполнены")
        return

    # Получаем текущего админа для проверки прав
    admin_user = dialog_manager.middleware_data.get("user")
    current_admin = await admin_user.get_user()

    # Проверяем, может ли админ назначить эту роль
    try:
        role_enum = UserRole(selected_role)
    except ValueError:
        await callback.answer("Неверная роль")
        return

    if current_admin.role == UserRole.ADMIN:
        # Admin не может назначать роли ADMIN и SUPER_ADMIN
        if role_enum in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            await callback.answer("У вас недостаточно прав для назначения этой роли")
            return

    session: AsyncSession = dialog_manager.middleware_data["session"]

    stmt = update(UserModel).where(
        UserModel.id == user_id
    ).values(
        role=role_enum,
        is_active=role_enum != UserRole.BANNED
    )

    await session.execute(stmt)
    await session.commit()

    await callback.answer(f"Роль успешно изменена на {role_enum}")
    await dialog_manager.switch_to(AdminPanelSG.pending_users)


async def cancel_role_change(callback: CallbackQuery, button: Button,
                             dialog_manager: DialogManager):
    """Отмена изменения роли"""
    # Очищаем временные данные
    dialog_manager.dialog_data.pop("user_id_to_change", None)
    dialog_manager.dialog_data.pop("selected_role", None)
    await dialog_manager.switch_to(AdminPanelSG.pending_users)
