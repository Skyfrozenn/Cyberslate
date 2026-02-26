from sqlalchemy import String, Boolean, DateTime, func, Index, Computed
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy.dialects.postgresql import TSVECTOR

from app.database import Base
from datetime import datetime, timezone


class CommandModel(Base):
    __tablename__ = "commands"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    is_filled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    tsv: Mapped[TSVECTOR] = mapped_column(
        TSVECTOR,
        Computed(
        """
        setweight(to_tsvector('english', coalesce(name, '')), 'A')
        || setweight(to_tsvector('russian', coalesce(name, '')), 'A')
        """,
        persisted=True, #данные пишутся автоматом
    ),
    nullable=False,
    )

     
    users: Mapped[list["UserModel"]] = relationship(back_populates="command")

    __table_args__ = (
        Index("ix_commands_tsv_gin", "tsv", postgresql_using="gin"),
        Index(
            "commands_trgm",
            "name",
            postgresql_using="gin", #гин индекс для поиска
            postgresql_ops={"name": "gin_trgm_ops"} #триграм разбивает слова на части Django dj, an, go
        ),
    )




