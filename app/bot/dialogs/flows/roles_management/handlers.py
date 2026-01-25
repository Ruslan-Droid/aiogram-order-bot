from typing import Any
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Multiselect
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.enums.user_roles import UserRole
from app.infrastructure.database.query.user_queries import UserRepository
from .states import AdminPanelSG

router = Router()


# authorization block
async def ban_selected_users(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
) -> None:
    session: AsyncSession = dialog_manager.middleware_data["session"]
    # Получаем виджет Multiselect
    multiselect: Multiselect = dialog_manager.find("ms_users")
    selected_ids = [int(telegram_id) for telegram_id in multiselect.get_checked()]

    await UserRepository(session).update_users_roles(selected_ids, role=UserRole.BANNED)
    await multiselect.reset_checked()

    await callback.answer("Пользователи забанены")
    await dialog_manager.switch_to(AdminPanelSG.pending_users)


async def approve_selected_users(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
) -> None:
    session: AsyncSession = dialog_manager.middleware_data["session"]
    # Получаем виджет Multiselect
    multiselect: Multiselect = dialog_manager.find("ms_users")

    # Получаем список выбранных telegram_id
    selected_ids = [int(telegram_id) for telegram_id in multiselect.get_checked()]

    await UserRepository(session).update_users_roles(selected_ids, role=UserRole.MEMBER)

    await multiselect.reset_checked()

    await callback.answer("Пользователи одобрены")
    await dialog_manager.switch_to(AdminPanelSG.pending_users)


# change role block
async def start_change_role(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
) -> None:
    await dialog_manager.switch_to(AdminPanelSG.change_role_input)


def validate_telegram_id(text: str) -> str:
    if not text.isdigit():
        raise ValueError("ID должен быть числом. Попробуйте снова:")

    return text


async def process_user_id(
        message: Message,
        widget: Any,
        dialog_manager: DialogManager,
        text: str
) -> None:
    session: AsyncSession = dialog_manager.middleware_data["session"]
    user_telegram_id = int(text)
    # Проверяем существование пользователя
    user = await UserRepository(session).get_user_by_telegram_id(user_telegram_id)

    if not user:
        await message.answer("Пользователь с таким ID не найден. Попробуйте снова:")
        return

    dialog_manager.dialog_data["user_id_to_change"] = user_telegram_id
    await dialog_manager.switch_to(AdminPanelSG.change_role_select)


async def process_error_user_id(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: Exception
) -> None:
    error_message = str(error)

    await message.answer(
        f"❌ Ошибка: {error_message}")


async def select_role(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager,
        item_id: str
) -> None:
    dialog_manager.dialog_data["selected_role"] = item_id
    print(item_id)


async def save_role_changes(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
) -> None:
    session: AsyncSession = dialog_manager.middleware_data["session"]
    user_id = dialog_manager.dialog_data.get("user_id_to_change")
    selected_role = dialog_manager.dialog_data.get("selected_role")

    if not user_id or not selected_role:
        await callback.answer("Ошибка: данные не заполнены")
        return

    await UserRepository(session).update_user_role(telegram_id=int(user_id), role=selected_role)

    await callback.answer(f"Роль успешно изменена на {selected_role}")
    await dialog_manager.switch_to(AdminPanelSG.pending_users)
