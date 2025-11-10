from decimal import Decimal
from typing import List, Dict

def calculate_dca_levels(entry_price: Decimal, dca_config: Dict) -> List[Dict]:
    """
    Calculate the prices for each DCA level.
    """
    levels = []
    for i in range(dca_config["dca_levels"]):
        price = entry_price * (1 - dca_config["price_gaps"][i])
        levels.append({"price": price})
    return levels

def calculate_position_size(total_risk_usd: Decimal, dca_weights: List) -> List[Decimal]:
    """
    Calculate the size of each DCA order.
    """
    sizes = []
    for weight in dca_weights:
        sizes.append(total_risk_usd * Decimal(weight))
    return sizes

def calculate_take_profit_prices(entry_prices: List[Decimal], tp_percent: Decimal) -> List[Decimal]:
    """
    Calculate the take-profit price for each DCA level.
    """
    prices = []
    for price in entry_prices:
        prices.append(price * (1 + tp_percent))
    return prices
