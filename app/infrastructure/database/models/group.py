from sqlalchemy import BigInteger, String, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base_model import Base


class GroupModel(Base):
    __tablename__ = "groups"

    group_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True
    )
    title: Mapped[str | None] = mapped_column(String(255))
    chat_type: Mapped[str] = mapped_column(String(20))  # group, supergroup, channel
    added_by_telegram_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="SET NULL")
    )
    language_code: Mapped[str | None] = mapped_column(String(10), default="en")
    bot_status: Mapped[str] = mapped_column(String(20))  # member, administrator, restricted, left, kicked
    admin_permissions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timezone region name (e.g., 'Europe/Moscow')
    tz_region: Mapped[str | None] = mapped_column(String(50), default="Europe/Moscow")
