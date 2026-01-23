import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from taskiq import TaskiqEvents, TaskiqScheduler, TaskiqState
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_nats import PushBasedJetStreamBroker
from nats.js.api import ConsumerConfig, StreamConfig, StorageType, RetentionPolicy
from taskiq_redis import RedisScheduleSource, RedisAsyncResultBackend

from config.config import get_config

config = get_config()

stream_config = StreamConfig(
    retention=RetentionPolicy.LIMITS,
    storage=StorageType.FILE,
    num_replicas=1,
)

consumer_config = ConsumerConfig(
    name="taskiq_consumer",
    durable_name="taskiq_consumer",
    max_ack_pending=25,
)

result_backend = RedisAsyncResultBackend(
    redis_url=config.redis.redis_url,
    prefix_str="taskiq_result_backend",
    result_ex_time=60
)

broker = PushBasedJetStreamBroker(
    servers=config.nats.servers,
    queue="taskiq_consumer",
    consumer_config=consumer_config,
    stream_config=stream_config,
).with_result_backend(
    result_backend=result_backend)

redis_source = RedisScheduleSource(
    url=config.redis.redis_url,
)

scheduler = TaskiqScheduler(broker, [redis_source, LabelScheduleSource(broker)])


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    logging.basicConfig(level=config.logs.level_name, format=config.logs.format)
    logger = logging.getLogger(__name__)
    logger.info("Starting worker...")

    state.logger = logger
    state.bot = Bot(token=config.bot.token,
                    default=DefaultBotProperties(parse_mode=ParseMode(config.bot.parse_mode)))


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState) -> None:
    state.logger.info("Worker stopped")
