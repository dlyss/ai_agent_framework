"""SQLAlchemy ORM models."""

from datetime import datetime
from sqlalchemy import (
    BigInteger,
    String,
    Boolean,
    DateTime,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class User(Base):
    """User model for storing user information."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="用户ID"
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="用户名"
    )
    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="邮箱"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="密码哈希"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否超级用户"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"
