from .commands import commands_router
from .user_statuses import user_status_router
from .callback import callback_router

__all__ = ["routers", "commands_router", "user_status_router", "callback_router"]

routers = [
    commands_router,
    user_status_router,
    callback_router
]
