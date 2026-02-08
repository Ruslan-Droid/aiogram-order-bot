from typing import Any, Dict

from aiogram_dialog import DialogManager
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.enums.user_roles import UserRole
from app.infrastructure.database.models import UserModel
from app.infrastructure.database.query.user_queries import UserRepository


async def get_pending_users(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> Dict[str, Any]:
    users = await UserRepository(session).get_users_by_role(UserRole.UNKNOWN)

    return {
        "users": users,
        "count_users": len(users)
    }


async def get_user_info(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> Dict[str, Any]:
    user_id = dialog_manager.dialog_data.get("user_id_to_change")

    user = await UserRepository(session).get_user_by_telegram_id(telegram_id=int(user_id))

    return {
        "user": user,
        "user_found": user is not None
    }


async def get_available_roles(
        dialog_manager: DialogManager,
        user_row: UserModel,
        **kwargs
) -> Dict[str, Any]:
    # Определяем доступные роли в зависимости от прав админа
    all_roles = [role for role in UserRole if role != UserRole.UNKNOWN]

    if user_row.role == UserRole.ADMIN:
        # Admin может назначать только до уровня DELIVERY
        available_roles = [
            role for role in all_roles
            if role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
        ]
    elif user_row.role == UserRole.SUPER_ADMIN:
        # Super admin может назначать любые роли
        available_roles = all_roles
    else:
        available_roles = []

    return {
        "roles": available_roles,
        "current_admin_role": user_row.role
    }


async def get_users_for_role_change(
        dialog_manager: DialogManager,
        session: AsyncSession,
        user_row: UserModel,
        **kwargs
) -> Dict[str, Any]:
    # Получаем всех пользователей кроме UNKNOWN (неавторизованных)
    all_users: list[UserModel] = await UserRepository(session).get_all_users_except_unknown()

    # Фильтруем пользователей в зависимости от роли админа
    filtered_users = []

    for user in all_users:
        # Для всех ролей: исключаем самого себя
        if user.telegram_id == user_row.telegram_id:
            continue

        # Для ADMIN: скрываем ADMIN и SUPER_ADMIN
        if user_row.role == UserRole.ADMIN:
            if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                filtered_users.append(user)
        # Для SUPER_ADMIN: показываем всех (уже исключили себя выше)
        elif user_row.role == UserRole.SUPER_ADMIN:
            filtered_users.append(user)

    # Форматируем пользователей для отображения
    users_for_display = []
    for user in filtered_users:
        display_name = user.full_name or user.username or f"Пользователь {user.telegram_id}"
        role_display = user.role.value
        text = f"{display_name} -👔 {role_display}"
        users_for_display.append((text, str(user.telegram_id)))

    return {
        "users": users_for_display,
        "count_users": len(filtered_users)
    }
