import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..schemas.auth_schemas import UserCreate, UserLogin, Token, UserOut
from ..services import auth_service, jwt_service
from ..models.user_models import User

router = APIRouter()

@router.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    if not auth_service.validate_password_strength(user.password):
        raise HTTPException(status_code=400, detail="Password is not strong enough")
    
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth_service.hash_password(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        password_hash=hashed_password,
        role=user.role,
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    access_token = jwt_service.create_access_token(
        user_id=db_user.id, email=db_user.email, role=db_user.role
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    Log in a user.
    """
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not auth_service.verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = jwt_service.create_access_token(
        user_id=db_user.id, email=db_user.email, role=db_user.role
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout():
    """
    Log out a user.
    """
    # This is a placeholder. In a real-world application, you would
    # invalidate the token on the client-side.
    return {"success": True}

@router.post("/refresh", response_model=Token)
def refresh(token: str):
    """
    Refresh an access token.
    """
    try:
        new_token = jwt_service.refresh_token(token)
        return {"access_token": new_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    """
    Request a password reset.
    """
    # This is a placeholder. In a real-world application, you would
    # generate a password reset token, save it to the database, and
    # send an email to the user with a link to reset their password.
    return {"success": True}

@router.post("/reset-password")
def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    """
    Reset a user's password.
    """
    # This is a placeholder. In a real-world application, you would
    # verify the password reset token, and if it's valid, update the
    # user's password in the database.
    return {"success": True}

@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
