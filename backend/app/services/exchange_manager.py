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
        
        return self

    async def get_current_price(self, symbol: str) -> Decimal:
        """Fetches the current market price for a symbol."""
        ticker = await self.exchange.fetch_ticker(symbol)
        return Decimal(str(ticker['last']))

    async def create_market_order(self, symbol: str, side: str, amount: Decimal):
        """Places a market order."""
        return await self.exchange.create_market_order(symbol, side, amount)

    async def place_order(self, symbol: str, side: str, amount: Decimal, order_type: str = 'market'):
        """Places an order on the exchange."""
        if order_type == 'market':
            return await self.create_market_order(symbol, side, amount)
        # TODO: Add support for other order types (e.g., limit)
        else:
            raise NotImplementedError(f"Order type '{order_type}' is not supported.")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.exchange:
            await self.exchange.close()

async def get_exchange(db: Session, exchange_name: str, user_id: UUID):
    return ExchangeManager(db, user_id, exchange_name)