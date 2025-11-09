import ccxt.async_support as ccxt
from typing import Dict, Any
from .mock_exchange import MockExchange

def _round_to_precision(value: float, precision: float) -> float:
    """Rounds a value to the nearest multiple of precision."""
    return round(value / precision) * precision

class ExchangeManager:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.exchange = self._init_exchange(api_key, api_secret, testnet)

    def _init_exchange(self, api_key: str, api_secret: str, testnet: bool) -> Any:
        if testnet:
            return MockExchange(api_key, api_secret, testnet)
        else:
            exchange_class = getattr(ccxt, "binance")
            exchange = exchange_class({
                'apiKey': api_key,
                'secret': api_secret,
            })
            return exchange

    async def fetch_precision(self, symbol: str) -> Dict[str, Any]:
        """Get tick_size, step_size, min_notional"""
        if isinstance(self.exchange, MockExchange):
            await self.exchange.load_markets()
            market = self.exchange.markets.get(symbol)
            if not market:
                raise ValueError(f"Market {symbol} not found in mock exchange.")
            return {
                "tick_size": market['precision']['price'],
                "step_size": market['precision']['amount'],
                "min_notional": market['limits']['cost']['min'],
            }
        else:
            await self.exchange.load_markets()
            market = self.exchange.market(symbol)
            return {
                "tick_size": market['precision']['price'],
                "step_size": market['precision']['amount'],
                "min_notional": market['limits']['cost']['min'],
            }

    async def validate_order(self, symbol: str, side: str, price: float, quantity: float) -> (bool, str):
        """Pre-flight validation before order"""
        precision_data = await self.fetch_precision(symbol)

        # Round price and quantity to exchange precision for validation
        rounded_price = _round_to_precision(price, precision_data['tick_size'])
        rounded_quantity = _round_to_precision(quantity, precision_data['step_size'])

        if abs(price - rounded_price) > 1e-9:
            return False, f"Price ({price}) does not match exchange tick size ({precision_data['tick_size']}). Rounded to {rounded_price}"
        if abs(quantity - rounded_quantity) > 1e-9:
            return False, f"Quantity ({quantity}) does not match exchange step size ({precision_data['step_size']}). Rounded to {rounded_quantity}"

        # Validate min_notional
        notional_value = rounded_price * rounded_quantity
        if notional_value < precision_data['min_notional']:
            return False, f"Notional value ({notional_value}) is less than the minimum ({precision_data['min_notional']})"

        return True, ""

    async def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None):
        """Execute order with error handling"""
        params = {}
        if order_type == 'limit':
            # Ensure price is rounded to tick size before placing order
            precision_data = await self.fetch_precision(symbol)
            price = _round_to_precision(price, precision_data['tick_size'])
            quantity = _round_to_precision(quantity, precision_data['step_size'])
            params['price'] = price
        
        try:
            order = await self.exchange.create_order(symbol, order_type, side, quantity, price, params)
            return order
        except Exception as e:
            print(f"Error placing order: {e}")
            return None

    async def close(self):
        await self.exchange.close()
