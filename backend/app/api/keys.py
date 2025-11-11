from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..schemas.key_schemas import ExchangeConfigCreate, ExchangeConfigOut
from ..services import encryption_service, jwt_service
from ..services.encryption_service import ENCRYPTION_KEY
from ..models.key_models import ExchangeConfig
from ..middleware.auth_middleware import require_authenticated, get_current_user
from typing import List
from uuid import UUID

router = APIRouter()

@router.post("/{exchange}", response_model=ExchangeConfigOut)
@require_authenticated
async def create_exchange_config(
    exchange: str,
    config: ExchangeConfigCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
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
async def get_exchange_configs(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
):
    """
    Get all exchange configurations for the current user.
    """
    return db.query(ExchangeConfig).filter(ExchangeConfig.user_id == user_id).all()

@router.put("/{exchange}/validate")
@require_authenticated
async def validate_exchange_config(
    exchange: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
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
async def delete_exchange_config(
    exchange: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
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
async def set_exchange_mode(
    exchange: str,
    mode: str,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
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

@router.put("/{exchange}/enable")
@require_authenticated
async def set_exchange_enabled(
    exchange: str,
    enable: bool,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
):
    """
    Enable or disable an exchange configuration.
    """
    db_config = db.query(ExchangeConfig).filter(
        ExchangeConfig.user_id == user_id,
        ExchangeConfig.exchange_name == exchange,
    ).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Exchange configuration not found")
    
    db_config.is_enabled = enable
    db.commit()
    return {"success": True}
