import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user_models import User
from ..schemas.auth_schemas import UserCreate
from typing import Optional
from uuid import UUID

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Creates a new user in the database."""
    hashed_password = hash_password(user_in.password)
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hashed_password,
        role=user_in.role
    )
async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Creates a new user in the database."""
    hashed_password = hash_password(user_in.password)
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hashed_password,
        role=user_in.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """
    Authenticates a user by username/email and password.
    """
    result = await db.execute(select(User).where(User.email == username))
    user = result.scalars().first()
    if user and verify_password(password, user.password_hash):
        return user
    return None

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Fetches a user by their email address.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Fetches a user by their ID.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt.
    """
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """
    Verifies a password against a bcrypt hash.
    """
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def generate_password_reset_token() -> str:
    """
    Generates a secure, random token for password resets.
    """
    import secrets
    return secrets.token_urlsafe(32)

def validate_password_strength(password: str) -> bool:
    """
    Validates password strength.
    Minimum 8 characters, 1 uppercase, 1 number.
    """
    if len(password) < 8:
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char.isdigit() for char in password):
        return False
    return True