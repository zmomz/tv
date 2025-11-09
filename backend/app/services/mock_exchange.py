import asyncio
from typing import Dict, Any

class MockExchange:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.markets = {
            "BTC/USDT": {
                'precision': {'price': 0.01, 'amount': 0.00001},
                'limits': {'cost': {'min': 5.0}},
            }
        }
        self.orders = {}
        self.order_id_counter = 0

    async def load_markets(self):
        # Simulate async market loading
        await asyncio.sleep(0.01)
        return self.markets

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        # Simulate fetching a ticker
        await asyncio.sleep(0.01)
        return {'last': 100000.00} # Fixed price for mock

    async def create_order(self, symbol: str, order_type: str, side: str, amount: float, price: float = None, params: Dict = None) -> Dict[str, Any]:
        await asyncio.sleep(0.01)
        self.order_id_counter += 1
        order_id = str(self.order_id_counter)
        order = {
            'info': {'symbol': symbol.replace('/', ''), 'orderId': order_id, 'status': 'NEW', 'type': order_type.upper(), 'side': side.upper()},
            'id': order_id,
            'clientOrderId': f'mock-order-{order_id}',
            'timestamp': asyncio.get_event_loop().time() * 1000,
            'datetime': None,
            'lastTradeTimestamp': None,
            'symbol': symbol,
            'type': order_type,
            'timeInForce': 'GTC',
            'postOnly': False,
            'reduceOnly': None,
            'side': side,
            'price': price,
            'triggerPrice': None,
            'amount': amount,
            'cost': price * amount if price else None,
            'average': None,
            'filled': 0.0,
            'remaining': amount,
            'status': 'open',
            'fee': None,
            'trades': [],
            'fees': [],
            'stopPrice': None,
            'takeProfitPrice': None,
            'stopLossPrice': None
        }
        self.orders[order_id] = order
        return order

    async def close(self):
        # Simulate closing connection
        await asyncio.sleep(0.01)
