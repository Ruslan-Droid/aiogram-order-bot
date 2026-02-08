import logging
from app.infrastructure.database.enums import UserRole
from app.infrastructure.database.query.user_queries import UserRepository
from config.config import AppConfig

logger = logging.getLogger(__name__)


async def create_admin(
        config: AppConfig,
        async_session_maker,
) -> None:
    """Создает супер-админа при старте, если его не существует"""
    async with async_session_maker() as session:
        repo = UserRepository(session)

        # Проверяем, существует ли уже пользователь с указанным ID
        existing_user = await repo.get_user_by_telegram_id(config.admin.admin_id)

        if not existing_user:
            # Создаем супер-админа
            await repo.create_or_update_user(
                telegram_id=config.admin.admin_id,
                username="super_admin",
                first_name="Super",
                last_name="Admin",
                language_code="ru",
                is_active=True,
                role=UserRole.SUPER_ADMIN
            )
            logger.info(f"Created super_admin with telegram_id: {config.admin.admin_id}")
        elif existing_user.role != UserRole.SUPER_ADMIN:
            # Обновляем роль существующего пользователя на SUPER_ADMIN
            await repo.update_user_role(UserRole.SUPER_ADMIN, config.admin.admin_id)
            logger.info(f"Updated user role to SUPER_ADMIN for telegram_id: {config.admin.admin_id}")
        else:
            logger.info(f"Super admin already exists with telegram_id: {config.admin.admin_id}")
