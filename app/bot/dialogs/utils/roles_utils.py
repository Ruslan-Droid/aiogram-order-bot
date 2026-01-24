from typing import Callable

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.common import Whenable

from app.infrastructure.database.models.user import UserModel, UserRole


def role_required(required_roles: list[UserRole]) -> Callable:
    def check_role(data: dict, widghet: Whenable, dialog_manager: DialogManager) -> bool:
        user: UserModel = dialog_manager.middleware_data["user_row"]
        if not user:
            return False
        return user.role in required_roles

    return check_role
