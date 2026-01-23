import logging
import redis

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import ChatAdministratorRights


from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.entities import DIALOG_EVENT_NAME
from aiogram_dialog.api.exceptions import UnknownIntent, UnknownState
from fluentogram import TranslatorHub

from app.bot.dialogs.flows import dialogs
from app.bot.handlers import routers
from app.bot.handlers.errors import on_unknown_intent, on_unknown_state
from app.bot.i18n.translator_hub import create_translator_hub
from app.bot.middlewares.database import DbSessionMiddleware
from app.bot.middlewares.get_user import GetUserMiddleware
from app.bot.middlewares.i18n import TranslatorRunnerMiddleware
from app.bot.middlewares.shadow_ban import ShadowBanMiddleware

from app.infrastructure.database.db import async_session_maker
from app.infrastructure.cache import get_redis_pool

from app.services.scheduler.taskiq_broker import broker, redis_source

from config.config import get_config

logger = logging.getLogger(__name__)


async def setup_bot_admin_rights(bot: Bot) -> None:
    logger.info("Setting default bot admin rights")
    bot_rights = ChatAdministratorRights(
        is_anonymous=False,
        can_manage_chat=True,
        can_delete_messages=True,
        can_manage_video_chats=False,
        can_restrict_members=False,
        can_promote_members=False,
        can_change_info=False,
        can_invite_users=False,
        can_post_stories=False,
        can_edit_stories=False,
        can_delete_stories=False,
    )
    await bot.set_my_default_administrator_rights(rights=bot_rights, for_channels=False)


async def main():
    config = get_config()

    redis_client: redis.asyncio.Redis = await get_redis_pool(
        host=config.redis.host,
        port=config.redis.port,
        db=config.redis.database,
        username=config.redis.username,
        password=config.redis.password,
    )

    bot = Bot(token=config.bot.token,
              default=DefaultBotProperties(parse_mode=ParseMode(config.bot.parse_mode)))

    await setup_bot_admin_rights(bot=bot)

    storage = RedisStorage(
        redis=redis_client,
        key_builder=DefaultKeyBuilder(
            with_destiny=True,
        ),
    )

    dp = Dispatcher(storage=storage)

    cache_pool: redis.asyncio.Redis = redis_client

    translator_hub: TranslatorHub = create_translator_hub()

    dp.workflow_data.update(
        bot_locales=sorted(config.i18n.locales),
        translator_hub=translator_hub,
        _cache_pool=cache_pool,
        redis_source=redis_source,
    )
    logger.info("Registering error handlers")
    dp.errors.register(
        on_unknown_intent,
        ExceptionTypeFilter(UnknownIntent),
    )
    dp.errors.register(
        on_unknown_state,
        ExceptionTypeFilter(UnknownState),
    )

    logger.info("Including  middlewares")
    dp.update.outer_middleware(DbSessionMiddleware(async_session_maker))
    dp.update.outer_middleware(GetUserMiddleware())
    dp.update.outer_middleware(ShadowBanMiddleware())
    dp.update.outer_middleware(TranslatorRunnerMiddleware())

    logger.info("Including routers")
    dp.include_routers(*routers)

    logger.info("Including dialogs")
    dp.include_routers(*dialogs)

    logger.info("Including error middlewares")
    dp.errors.middleware(DbSessionMiddleware(async_session_maker))
    dp.errors.middleware(GetUserMiddleware())
    dp.errors.middleware(ShadowBanMiddleware())
    dp.errors.middleware(TranslatorRunnerMiddleware())

    logger.info("Setting up dialogs")
    bg_factory = setup_dialogs(dp)
    dp.workflow_data.update(bg_factory=bg_factory)

    logger.info("Including observers middlewares")
    dp.observers[DIALOG_EVENT_NAME].outer_middleware(DbSessionMiddleware(async_session_maker))
    dp.observers[DIALOG_EVENT_NAME].outer_middleware(GetUserMiddleware())
    dp.observers[DIALOG_EVENT_NAME].outer_middleware(ShadowBanMiddleware())
    dp.observers[DIALOG_EVENT_NAME].outer_middleware(TranslatorRunnerMiddleware())

    if not broker.is_worker_process:
        logger.info("Starting taskiq broker")
        await broker.startup()

    # Launch polling and delayed message consumer
    try:
        await dp.start_polling(
            bot,
            bg_factory=bg_factory,
        ),
    except Exception as e:
        logger.exception(e)
    finally:
        await cache_pool.close()
        logger.info("Connection to Redis closed")
        if not broker.is_worker_process:
            logger.info("Connection to taskiq-broker closed")
            await broker.shutdown()
