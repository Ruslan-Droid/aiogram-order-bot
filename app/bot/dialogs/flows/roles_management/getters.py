from typing import Any, Dict

from aiogram_dialog import DialogManager
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.enums.user_roles import UserRole
from app.infrastructure.database.query.user_queries import UserRepository


async def get_pending_users(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> Dict[str, Any]:
    users = await UserRepository(session).get_users_by_role(UserRole.UNKNOWN)

    return {
        "users": users,
        "count": len(users)
    }


async def get_user_info(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> Dict[str, Any]:
    user_id = dialog_manager.dialog_data.get("user_id_to_change")

    user = await UserRepository(session).get_user_by_telegram_id(telegram_id=user_id)

    return {
        "user": user,
        "user_found": user is not None
    }


async def get_available_roles(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Получение списка доступных ролей для текущего админа"""
    admin_user = dialog_manager.middleware_data.get("user")
    current_admin = await admin_user.get_user()

    # Определяем доступные роли в зависимости от прав админа
    all_roles = [role for role in UserRole if role != UserRole.UNKNOWN]

    if current_admin.role == UserRole.ADMIN:
        # Admin может назначать только до уровня DELIVERY
        available_roles = [
            role for role in all_roles
            if role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.BANNED]
        ]
    elif current_admin.role == UserRole.SUPER_ADMIN:
        # Super admin может назначать любые роли
        available_roles = all_roles
    else:
        available_roles = []

    return {
        "roles": available_roles,
        "current_admin_role": current_admin.role
    }


async def get_selected_users(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> Dict[str, Any]:
    """Получение выбранных пользователей"""
    selected_ids = dialog_manager.dialog_data.get("selected_user_ids", [])

    users = await UserRepository(session).get_users_by_telegram_ids(selected_ids)

    return {
        "selected_users": users,
        "has_selected": len(users)
    }
