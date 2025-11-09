import asyncio
from app.services.exchange_manager import ExchangeManager, _round_to_precision
from app.core.config import settings

async def main():
    manager = ExchangeManager(
        api_key=settings.API_KEY,
        api_secret=settings.API_SECRET,
        testnet=settings.EXCHANGE_TESTNET
    )
    try:
        # Test fetch_precision
        precision = await manager.fetch_precision("BTC/USDT")
        print(f"Precision for BTC/USDT: {precision}")
        assert precision['tick_size'] is not None
        assert precision['step_size'] is not None

        # Fetch current ticker price
        ticker = await manager.exchange.fetch_ticker("BTC/USDT")
        current_price = ticker['last']
        print(f"Current BTC/USDT price: {current_price}")

        # Calculate a limit price slightly below current price for a buy order
        limit_price = current_price * 0.99 # 1% below current price
        limit_price = _round_to_precision(limit_price, precision['tick_size']) # Round to tick size
        print(f"Calculated limit price: {limit_price}")

        # Calculate a quantity rounded to step size
        quantity = _round_to_precision(0.001, precision['step_size'])
        print(f"Calculated quantity: {quantity}")

        # Test validate_order
        is_valid, reason = await manager.validate_order("BTC/USDT", "buy", limit_price, quantity)
        print(f"Order validation result: {is_valid}, {reason}")
        assert is_valid

        is_valid, reason = await manager.validate_order("BTC/USDT", "buy", limit_price, 0.0000001)
        print(f"Order validation result: {is_valid}, {reason}")
        assert not is_valid

        # Test place_order
        order = await manager.place_order("BTC/USDT", "buy", "limit", quantity, limit_price)
        print(f"Placed order: {order}")
        assert order is not None
        assert order['symbol'] == 'BTC/USDT'
        assert order['side'] == 'buy'
        assert order['type'] == 'limit'

    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
