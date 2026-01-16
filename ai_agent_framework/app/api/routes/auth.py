"""Authentication routes."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.database import get_db
from app.api.auth import (
    authenticate_user_db,
    create_user_db,
    create_access_token,
    get_current_user,
)
from schemas.auth import Token, UserCreate, UserLogin, UserResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    return await create_user_db(
        db=db,
        username=user_data.username,
        password=user_data.password,
        email=user_data.email
    )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login and get access token."""
    user = await authenticate_user_db(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )


@router.post("/token", response_model=Token)
async def login_json(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login with JSON body and get access token."""
    user = await authenticate_user_db(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get current user info."""
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: UserResponse = Depends(get_current_user)):
    """Refresh access token."""
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": current_user.username, "user_id": current_user.id},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )
