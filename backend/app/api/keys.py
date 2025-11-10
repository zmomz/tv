from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.key_schemas import ExchangeConfigCreate, ExchangeConfigOut
from app.services import encryption_service
from app.models.key_models import ExchangeConfig
from app.middleware.auth_middleware import require_authenticated
from typing import List
from uuid import UUID

router = APIRouter()

@router.post("/{exchange}", response_model=ExchangeConfigOut)
@require_authenticated
def create_exchange_config(
    exchange: str,
    config: ExchangeConfigCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(lambda token: UUID(jwt_service.verify_token(token)["sub"])),
):
    """
    Create a new exchange configuration.
    """
    encrypted_api_key = encryption_service.encrypt_data(config.api_key, ENCRYPTION_KEY)
    encrypted_api_secret = encryption_service.encrypt_data(config.api_secret, ENCRYPTION_KEY)
    
    db_config = ExchangeConfig(
        user_id=user_id,
        exchange_name=exchange,
        mode=config.mode,
        api_key_encrypted=encrypted_api_key,
        api_secret_encrypted=encrypted_api_secret,
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

@router.get("", response_model=List[ExchangeConfigOut])
@require_authenticated
def get_exchange_configs(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(lambda token: UUID(jwt_service.verify_token(token)["sub"])),
):
    """
    Get all exchange configurations for the current user.
    """
    return db.query(ExchangeConfig).filter(ExchangeConfig.user_id == user_id).all()

@router.put("/{exchange}/validate")
@require_authenticated
def validate_exchange_config(
    exchange: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(lambda token: UUID(jwt_service.verify_token(token)["sub"])),
):
    """
    Validate the connection to an exchange.
    """
    # This is a placeholder. In a real-world application, you would
    # decrypt the API key and secret, and then use them to make a
    # test API call to the exchange.
    return {"success": True}

@router.delete("/{exchange}")
@require_authenticated
def delete_exchange_config(
    exchange: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(lambda token: UUID(jwt_service.verify_token(token)["sub"])),
):
    """
    Delete an exchange configuration.
    """
    db.query(ExchangeConfig).filter(
        ExchangeConfig.user_id == user_id,
        ExchangeConfig.exchange_name == exchange,
    ).delete()
    db.commit()
    return {"success": True}

@router.put("/{exchange}/mode")
@require_authenticated
def set_exchange_mode(
    exchange: str,
    mode: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(lambda token: UUID(jwt_service.verify_token(token)["sub"])),
):
    """
    Set the mode for an exchange (testnet or live).
    """
    db_config = db.query(ExchangeConfig).filter(
        ExchangeConfig.user_id == user_id,
        ExchangeConfig.exchange_name == exchange,
    ).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Exchange configuration not found")
    
    db_config.mode = mode
    db.commit()
    return {"success": True}
