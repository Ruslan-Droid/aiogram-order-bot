from typing import Any

from aiogram_dialog import DialogManager

from app.infrastructure.database.enums.user_roles import UserRole
from app.infrastructure.database.models import UserModel


async def get_user_role(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    user: UserModel = dialog_manager.middleware_data["user_row"]

    if not user:
        return {"role": UserRole.UNKNOWN}

    return {"role": user.role}
