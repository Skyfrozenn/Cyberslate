from sqlalchemy import String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from datetime import datetime, timezone


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    role : Mapped[str] = mapped_column(String(20), default="viewer")
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

     
    is_team_creator: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

     
    command_id: Mapped[int] = mapped_column(ForeignKey("commands.id"), nullable=True, index=True)

    command: Mapped["CommandModel"] = relationship(back_populates="users")