"""Authentication schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
    user_id: Optional[str] = None
    scopes: list = []


class UserCreate(BaseModel):
    """User creation request."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: str = Field(..., description="User email address")


class UserLogin(BaseModel):
    """User login request."""
    username: str
    password: str


class UserResponse(BaseModel):
    """User response."""
    id: int = Field(..., description="User ID (bigint)")
    username: str
    email: Optional[str] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True
