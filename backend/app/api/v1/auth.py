"""Authentication endpoints."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
)
from app.core.permissions import UserRole
from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.v1.deps import get_current_active_user

router = APIRouter()


# Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str | None
    last_name: str | None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None


# Endpoints
@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticate user and return JWT token."""
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        # Increment failed attempts
        if user:
            user.failed_login_attempts += 1
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Reset failed attempts and update last login
    user.failed_login_attempts = 0
    user.last_login = datetime.utcnow()
    db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new user (creates VIEWER by default)."""
    # Check if email already exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=request.email,
        password_hash=get_password_hash(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        role=UserRole.VIEWER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        is_active=user.is_active,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    """Get current authenticated user."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
    )
