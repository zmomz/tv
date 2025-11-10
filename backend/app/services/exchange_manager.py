import ccxt.async_support as ccxt
from sqlalchemy.orm import Session
from app.models.key_models import ExchangeConfig
from app.services import encryption_service
from uuid import UUID
from decimal import Decimal

async def get_exchange(db: Session, exchange_name: str, user_id: UUID):
    """
    Get an exchange instance.
    """
    db_config = db.query(ExchangeConfig).filter(
        ExchangeConfig.user_id == user_id,
        ExchangeConfig.exchange_name == exchange_name,
    ).first()
    
    if not db_config:
        raise Exception("Exchange configuration not found")
    
    api_key = encryption_service.decrypt_data(db_config.api_key_encrypted, encryption_service.ENCRYPTION_KEY)
    api_secret = encryption_service.decrypt_data(db_config.api_secret_encrypted, encryption_service.ENCRYPTION_KEY)
    
    exchange_class = getattr(ccxt, exchange_name)
    exchange = exchange_class({
        'apiKey': api_key,
        'secret': api_secret,
    })
    
    if db_config.mode == 'testnet':
        exchange.set_sandbox_mode(True)
        
    return exchange

async def get_balance(db: Session, exchange_name: str, user_id: UUID) -> dict:
    """
    Get the balance for an exchange.
    """
    exchange = await get_exchange(db, exchange_name, user_id)
    balance = await exchange.fetch_balance()
    await exchange.close()
    return balance

async def place_order(
    db: Session,
    exchange_name: str,
    user_id: UUID,
    symbol: str,
    side: str,
    order_type: str,
    quantity: Decimal,
    price: Decimal = None,
) -> dict:
    """
    Place an order on an exchange.
    """
    exchange = await get_exchange(db, exchange_name, user_id)
    order = await exchange.create_order(symbol, order_type, side, float(quantity), float(price) if price else None)
    await exchange.close()
    return order

async def cancel_order(db: Session, exchange_name: str, user_id: UUID, symbol: str, order_id: str) -> bool:
    """
    Cancel an order on an exchange.
    """
    exchange = await get_exchange(db, exchange_name, user_id)
    await exchange.cancel_order(order_id, symbol)
    await exchange.close()
    return True

async def get_order_status(db: Session, exchange_name: str, user_id: UUID, symbol: str, order_id: str) -> dict:
    """
    Get the status of an order on an exchange.
    """
    exchange = await get_exchange(db, exchange_name, user_id)
    order = await exchange.fetch_order(order_id, symbol)
    await exchange.close()
    return order

async def get_precision_rules(db: Session, exchange_name: str, symbol: str) -> dict:
    """
    Get the precision rules for a symbol on an exchange.
    """
    exchange = await get_exchange(db, exchange_name, None) # No auth needed for this
    await exchange.load_markets()
    market = exchange.market(symbol)
    await exchange.close()
    return market['precision']