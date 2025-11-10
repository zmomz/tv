import os
import jwt
from datetime import datetime, timedelta
from uuid import UUID

JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret-key")
ALGORITHM = "HS256"

def create_access_token(user_id: UUID, email: str, role: str) -> str:
    """Creates a new access token."""
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = {
        "exp": expire,
        "sub": str(user_id),
        "email": email,
        "role": role,
    }
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verifies a JWT token and returns its payload."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")

def refresh_token(old_token: str) -> str:
    """Refreshes a JWT token if it's within 1 hour of expiry."""
    try:
        payload = jwt.decode(old_token, JWT_SECRET, algorithms=[ALGORITHM])
        
        # Check if the token is within 1 hour of expiry
        time_to_expiry = datetime.fromtimestamp(payload["exp"]) - datetime.utcnow()
        if time_to_expiry > timedelta(hours=1):
            raise Exception("Token is not within 1 hour of expiry")

        return create_access_token(
            user_id=UUID(payload["sub"]),
            email=payload["email"],
            role=payload["role"],
        )
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
