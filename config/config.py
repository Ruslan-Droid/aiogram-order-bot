from aiogram.enums import ParseMode
from dynaconf import Dynaconf
from pydantic import BaseModel, Field


class LogsConfig(BaseModel):
    level_name: str = Field(
        default="INFO", description="Log level name (e.g. DEBUG, INFO, WARNING, ERROR)."
    )
    format: str = Field(
        default="%(asctime)s [%(levelname)s] %(message)s",
        description="Log message format."
    )


class I18nConfig(BaseModel):
    default_locale: str = Field(default="en", description="Default locale for the application.")
    locales: list[str] = Field(default=["en"], description="List of supported locales.")


class BotConfig(BaseModel):
    token: str = Field(..., description="Telegram bot API token.")
    parse_mode: ParseMode = Field(
        ..., description="Default parse mode for sending messages (e.g. HTML, Markdown)."
    )


class PostgresConfig(BaseModel):
    name: str = Field(..., description="PostgreSQL database name.")
    host: str = Field(..., description="PostgreSQL server hostname.")
    port: int = Field(..., description="PostgreSQL server port.")
    user: str = Field(..., description="PostgreSQL username.")
    password: str = Field(..., description="PostgreSQL user password.")
    url: str = Field(..., description="PostgreSQL server URL.")


class RedisConfig(BaseModel):
    host: str = Field(default="localhost", description="Redis server hostname.")
    port: int = Field(default=6379, description="Redis server port.")
    database: int = Field(default=0, description="Redis database index.")
    username: str | None = Field(None, description="Optional Redis username.")
    password: str | None = Field(None, description="Optional Redis password.")
    redis_url: str | None = Field(None, description="Redis server URL.")


class NatsConfig(BaseModel):
    servers: str | list[str] = Field(..., description="NATS servers.")


class AdminConfig(BaseModel):
    admin_id: int = Field(..., description="Admin telegram id.")
    admin_chat_id: int = Field(..., description="Admin telegram chatID.")


class AppConfig(BaseModel):
    logs: LogsConfig
    i18n: I18nConfig
    bot: BotConfig
    postgres: PostgresConfig
    redis: RedisConfig
    nats: NatsConfig
    admin: AdminConfig


# Инициализация Dynaconf
_settings = Dynaconf(
    envvar_prefix=False,  # "DYNACONF",
    environments=True,
    env_switcher="ENV_FOR_DYNACONF",
    settings_files=["settings.toml"],
    load_dotenv=True,
)


def get_config() -> AppConfig:
    """
        Returns a typed application configuration.

        Returns:
            AppConfig: A validated Pydantic model containing the application language_settings.
    """
    logs = LogsConfig(
        level_name=_settings.logs.level_name,
        format=_settings.logs.format,
    )
    i18n = I18nConfig(
        default_locale=_settings.i18n.default_locale,
        locales=_settings.i18n.locales,
    )
    bot = BotConfig(
        token=_settings.bot_token,
        parse_mode=_settings.bot.parse_mode,
    )
    postgres = PostgresConfig(
        name=_settings.postgres_name,
        host=_settings.postgres_host,
        port=_settings.postgres_port,
        user=_settings.postgres_user,
        password=_settings.postgres_password,
        url=f"postgresql+asyncpg://{_settings.postgres_user}:{_settings.postgres_password}@{_settings.postgres_host}:"
            f"{_settings.postgres_port}/{_settings.postgres_name}"
    )
    redis = RedisConfig(
        host=_settings.redis_host,
        port=_settings.redis_port,
        database=_settings.redis_database,
        username=_settings.redis_username,
        password=_settings.redis_password,
        redis_url=f"redis://{_settings.redis_username}:{_settings.redis_password}@{_settings.redis_host}:{_settings.redis_port}/{_settings.redis_database}"
    )
    nats = NatsConfig(
        servers=_settings.nats.servers,
    )
    admin = AdminConfig(
        admin_id=_settings.admin_id,
        admin_chat_id=_settings.admin_chat,
    )

    return AppConfig(
        logs=logs,
        i18n=i18n,
        bot=bot,
        postgres=postgres,
        redis=redis,
        nats=nats,
        admin=admin,
    )
