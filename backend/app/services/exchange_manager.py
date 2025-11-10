import ccxt.async_support as ccxt
from sqlalchemy.orm import Session
from ..models.key_models import ExchangeConfig
from ..services import encryption_service
from uuid import UUID
from decimal import Decimal

class ExchangeManager:
    def __init__(self, db: Session, user_id: UUID, exchange_name: str):
        self.db = db
        self.user_id = user_id
        self.exchange_name = exchange_name
        self.exchange = None

    async def __aenter__(self):
        db_config = self.db.query(ExchangeConfig).filter(
            ExchangeConfig.user_id == self.user_id,
            ExchangeConfig.exchange_name == self.exchange_name,
        ).first()

        if not db_config:
            raise Exception("Exchange configuration not found")

        api_key = encryption_service.decrypt_data(db_config.api_key_encrypted, encryption_service.ENCRYPTION_KEY)
        api_secret = encryption_service.decrypt_data(db_config.api_secret_encrypted, encryption_service.ENCRYPTION_KEY)

        exchange_class = getattr(ccxt, self.exchange_name)
        self.exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
        })

        if db_config.mode == 'testnet':
            self.exchange.set_sandbox_mode(True)
        
        return self.exchange

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.exchange:
            await self.exchange.close()

async def get_exchange(db: Session, exchange_name: str, user_id: UUID):
    return ExchangeManager(db, user_id, exchange_name)