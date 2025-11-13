from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db.session import get_async_db
from ..schemas.auth_schemas import UserCreate, UserOut, Token, UserLogin
from ..services.auth_service import create_user, authenticate_user, get_user_by_email, get_user_by_id
from ..services.jwt_service import create_access_token
from ..models.user_models import User
from uuid import UUID

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    user: UserCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Register a new user.
    """
    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await create_user(db=db, user=user)

@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Authenticate user and return JWT token.
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(user_id=user.id, email=user.email, role=user.role)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
async def forgot_password(
    email: str,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Initiate password reset process.
    """
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # TODO: Implement actual password reset token generation and email sending
    return {"message": "Password reset link sent to your email"}

@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Reset user password using a valid token.
    """
    # TODO: Implement actual token verification and password reset logic
    return {"message": "Password has been reset successfully"}

@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get user by ID.
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
