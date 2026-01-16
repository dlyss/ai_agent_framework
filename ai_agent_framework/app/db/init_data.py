"""Initialize database with default data."""

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User
from app.db import crud
from app.api.auth import get_password_hash


async def init_admin_user(db: AsyncSession) -> None:
    """Create default admin user if not exists.
    
    Admin user credentials:
    - username: admin
    - password: 111111
    - is_superuser: True (has all permissions)
    """
    admin_username = "admin"
    
    existing_admin = await crud.get_user_by_username(db, admin_username)
    if existing_admin:
        print(f"Admin user '{admin_username}' already exists.")
        return
    
    admin_user = User(
        username=admin_username,
        email="admin@aiagent.local",
        hashed_password=get_password_hash("111111"),
        is_active=True,
        is_superuser=True,
    )
    
    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)
    
    print(f"Created admin user: {admin_username} (id={admin_user.id})")


async def init_default_data(db: AsyncSession) -> None:
    """Initialize all default data."""
    await init_admin_user(db)
