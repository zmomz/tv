import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_models import User

@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """
    Tests that a User model can be created and saved to the database.
    """
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.is_active is True
