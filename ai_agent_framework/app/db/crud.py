"""CRUD operations for database models."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    hashed_password: str,
    is_active: bool = True,
    is_superuser: bool = False,
) -> User:
    """Create a new user."""
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_active=is_active,
        is_superuser=is_superuser,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession,
    user: User,
    **kwargs
) -> User:
    """Update user fields."""
    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)
    await db.flush()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: User) -> bool:
    """Delete a user."""
    await db.delete(user)
    await db.flush()
    return True


async def check_username_exists(db: AsyncSession, username: str) -> bool:
    """Check if username already exists."""
    result = await db.execute(select(User.id).where(User.username == username))
    return result.scalar_one_or_none() is not None


async def check_email_exists(db: AsyncSession, email: str) -> bool:
    """Check if email already exists."""
    result = await db.execute(select(User.id).where(User.email == email))
    return result.scalar_one_or_none() is not None
