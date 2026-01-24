from sqlalchemy import func, TIMESTAMP, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column("id", primary_key=True, autoincrement=True)

    created_at: Mapped[DateTime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )
