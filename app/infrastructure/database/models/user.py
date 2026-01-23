from sqlalchemy import BigInteger, String, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.enums.user_roles import UserRole
from app.infrastructure.database.models.base_model import Base
from sqlalchemy.dialects.postgresql import ENUM as PgEnum


class UserModel(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True
    )
    username: Mapped[str | None] = mapped_column(String(32))
    first_name: Mapped[str | None] = mapped_column(String(64))
    last_name: Mapped[str | None] = mapped_column(String(64))
    language_code: Mapped[str | None] = mapped_column(String(10), default="ru")
    role: Mapped[UserRole] = mapped_column(PgEnum(UserRole, name="user_role"), default=UserRole.MEMBER)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_banned: Mapped[bool] = mapped_column(default=False)

    # Timezone region name (e.g., 'Europe/Moscow')
    tz_region: Mapped[str | None] = mapped_column(String(50), default="Europe/Moscow")
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    city: Mapped[str | None] = mapped_column(String(100))
