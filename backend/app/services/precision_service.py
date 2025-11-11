import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
import asyncio
import json

import redis.asyncio as redis
from sqlalchemy.orm import Session

from ..services import exchange_manager
from ..core.config import settings # Assuming settings will provide REDIS_URL

# Global Redis client instance (or managed via FastAPI dependency)
redis_client: Optional[redis.Redis] = None

async def get_redis_client() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client

class PrecisionService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.cache_key_prefix = "precision:"
        self.cache_expiry_seconds = settings.PRECISION_CACHE_EXPIRY_SECONDS # Assuming this will be in config

    async def _get_cache_key(self, exchange: str, symbol: str) -> str:
        return f"{self.cache_key_prefix}{exchange}:{symbol}"

    async def fetch_and_cache_precision_rules(self, db: Session, exchange: str, symbol: str):
        """
        Fetches precision rules from the exchange and caches them.
        """
        try:
            precision_rules = await exchange_manager.get_precision_rules(db, exchange, symbol)
            cache_key = await self._get_cache_key(exchange, symbol)
            await self.redis.set(cache_key, json.dumps(precision_rules), ex=self.cache_expiry_seconds)
            print(f"Cached precision rules for {exchange}:{symbol}")
            return precision_rules
        except Exception as e:
            print(f"Error fetching and caching precision for {exchange}:{symbol}: {e}")
            return None

    async def get_precision(self, db: Session, exchange: str, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves precision rules from cache, or fetches and caches if not found/expired.
        """
        cache_key = await self._get_cache_key(exchange, symbol)
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            print(f"Retrieved precision rules for {exchange}:{symbol} from cache.")
            return json.loads(cached_data)
        else:
            print(f"Precision rules for {exchange}:{symbol} not in cache. Fetching...")
            return await self.fetch_and_cache_precision_rules(db, exchange, symbol)

async def fetch_precision_info(db: Session, exchange: str, symbol: str) -> dict:
    """
    Fetch precision information for a symbol on an exchange.
    """
    redis_client_instance = await get_redis_client()
    precision_service = PrecisionService(redis_client_instance)
    return await precision_service.get_precision(db, exchange, symbol)

def calculate_min_notional(quantity: Decimal, price: Decimal) -> Decimal:
    """
    Calculate the notional value of an order.
    """
    return quantity * price
