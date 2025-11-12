import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_models import User
from app.models.key_models import APIKey

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


@pytest.mark.asyncio
async def test_create_api_key(db_session: AsyncSession):
    """
    Tests that an APIKey model can be created and saved to the database.
    """
    user = User(
        email="api_key_test@example.com",
        username="api_key_testuser",
        password_hash="hashed_api_key_password"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    api_key = APIKey(
        user_id=user.id,
        key_hash="hashed_api_key_value",
        label="My Test API Key"
    )
    db_session.add(api_key)
    await db_session.commit()
    await db_session.refresh(api_key)

    assert api_key.id is not None
    assert api_key.user_id == user.id
    assert api_key.key_hash == "hashed_api_key_value"
    assert api_key.label == "My Test API Key"
    assert api_key.is_active is True
